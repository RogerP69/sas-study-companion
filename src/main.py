import asyncio
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path

import uvicorn
import yaml
from dotenv import load_dotenv
from PIL import Image

from change_detector import ChangeDetector
from claude_client import ClaudeClient
from hotkey_manager import HotkeyManager
from screen_capture import capture
from session_logger import SessionLogger
from web_server import app, broadcast, get_event_loop, set_monitoring, set_processing

_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def _load_config() -> dict:
    with _CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


def _stitch(frames: list[Image.Image]) -> Image.Image:
    total_height = sum(f.height for f in frames)
    stitched = Image.new("RGB", (frames[0].width, total_height))
    y = 0
    for frame in frames:
        stitched.paste(frame, (0, y))
        y += frame.height
    return stitched


class Companion:
    def __init__(self, config: dict) -> None:
        self._config = config
        self._monitoring = False
        self._scroll_capturing = False
        self._scroll_frames: list[Image.Image] = []
        self._scroll_lock = threading.Lock()
        self._detector = ChangeDetector(config["monitor"]["change_threshold_percent"])
        self._claude = ClaudeClient(config["claude"]["model"], config["claude"]["max_tokens"])
        self._logger = SessionLogger()

    def _broadcast_sync(self, message: dict) -> None:
        loop = get_event_loop()
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast(message), loop)

    def toggle(self) -> None:
        self._monitoring = not self._monitoring
        set_monitoring(self._monitoring)
        self._broadcast_sync({"type": "status", "monitoring": self._monitoring, "processing": False})
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitoring {'ON' if self._monitoring else 'OFF'}")

    def analyze_now(self) -> None:
        if not self._monitoring:
            return
        image = capture(self._config["monitor"]["monitor_index"])
        threading.Thread(target=self._analyze, args=(image, "manual_hotkey"), daemon=True).start()

    def toggle_scroll_capture(self) -> None:
        with self._scroll_lock:
            if not self._scroll_capturing:
                self._scroll_frames = [capture(self._config["monitor"]["monitor_index"])]
                self._scroll_capturing = True
                self._start_scroll_listener()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Scroll capture started")
            else:
                self._scroll_capturing = False
                self._stop_scroll_listener()
                frames = list(self._scroll_frames)
                self._scroll_frames = []
                if frames:
                    stitched = _stitch(frames)
                    threading.Thread(target=self._analyze, args=(stitched, "scroll_capture"), daemon=True).start()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Scroll capture ended ({len(frames)} frames)")

    def _start_scroll_listener(self) -> None:
        from pynput.mouse import Listener as MouseListener
        self._last_scroll = 0.0
        self._pending_scroll = False

        def on_scroll(x, y, dx, dy):
            if not self._scroll_capturing:
                return False  # stop listener
            self._last_scroll = time.monotonic()
            if not self._pending_scroll:
                self._pending_scroll = True
                threading.Timer(0.5, self._do_scroll_capture, args=(self._last_scroll,)).start()

        self._scroll_listener = MouseListener(on_scroll=on_scroll)
        self._scroll_listener.start()

    def _do_scroll_capture(self, scroll_time: float) -> None:
        if scroll_time == self._last_scroll and self._scroll_capturing:
            frame = capture(self._config["monitor"]["monitor_index"])
            with self._scroll_lock:
                if self._scroll_capturing:
                    self._scroll_frames.append(frame)
        self._pending_scroll = False

    def _stop_scroll_listener(self) -> None:
        if hasattr(self, "_scroll_listener"):
            self._scroll_listener.stop()

    def _analyze(self, image: Image.Image, trigger: str) -> None:
        set_processing(True)
        self._broadcast_sync({"type": "processing"})
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Analyzing ({trigger})...")
        try:
            result = self._claude.analyze(image)
            self._logger.log(trigger=trigger, **result)
            self._broadcast_sync({
                "type": "result",
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                **result,
            })
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Done.")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}", file=sys.stderr)
            self._broadcast_sync({"type": "error", "message": str(e)})
        finally:
            set_processing(False)

    def run_monitor_loop(self) -> None:
        interval = self._config["monitor"]["scan_interval_seconds"]
        debounce = self._config["monitor"]["debounce_seconds"]
        monitor_idx = self._config["monitor"]["monitor_index"]
        while True:
            if self._monitoring and not self._scroll_capturing:
                image = capture(monitor_idx)
                if self._detector.has_changed(image):
                    time.sleep(debounce)
                    image = capture(monitor_idx)
                    threading.Thread(target=self._analyze, args=(image, "auto_change"), daemon=True).start()
            time.sleep(interval)


def main() -> None:
    load_dotenv()
    config = _load_config()
    companion = Companion(config)

    host = config["server"]["host"]
    port = config["server"]["port"]

    server_thread = threading.Thread(
        target=uvicorn.run,
        kwargs={"app": app, "host": host, "port": port, "log_level": "warning"},
        daemon=True,
    )
    server_thread.start()

    # Wait for the server event loop to be ready
    for _ in range(20):
        if get_event_loop() is not None:
            break
        time.sleep(0.1)

    hotkeys = HotkeyManager(
        hotkeys=config["hotkeys"],
        callbacks={
            "toggle": companion.toggle,
            "analyze": companion.analyze_now,
            "scroll_capture": companion.toggle_scroll_capture,
        },
    )
    hotkeys.start()

    webbrowser.open(f"http://{host}:{port}")

    print("SAS Study Companion running.")
    print(f"  Panel:    http://{host}:{port}")
    print(f"  Logs:     {companion._logger.path}")
    print(f"  Toggle:   {config['hotkeys']['toggle']}")
    print(f"  Analyze:  {config['hotkeys']['analyze']}")
    print(f"  Scroll:   {config['hotkeys']['scroll_capture']}")
    print("Press Ctrl+C to quit.\n")

    monitor_thread = threading.Thread(target=companion.run_monitor_loop, daemon=True)
    monitor_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        hotkeys.stop()
        print("\nGoodbye.")


if __name__ == "__main__":
    main()
