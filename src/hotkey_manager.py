from typing import Callable
from pynput import keyboard


def _to_pynput_format(combo: str) -> str:
    """Convert 'ctrl+shift+s' to '<ctrl>+<shift>+s' for pynput GlobalHotKeys."""
    modifiers = {"ctrl", "shift", "alt"}
    parts = combo.lower().split("+")
    return "+".join(f"<{p}>" if p in modifiers else p for p in parts)


class HotkeyManager:
    def __init__(self, hotkeys: dict[str, str], callbacks: dict[str, Callable]) -> None:
        """
        hotkeys: {"toggle": "ctrl+shift+s", "analyze": "ctrl+shift+a", ...}
        callbacks: {"toggle": fn, "analyze": fn, ...}
        """
        hotkey_map = {
            _to_pynput_format(combo): callbacks[action]
            for action, combo in hotkeys.items()
            if action in callbacks
        }
        self._listener = keyboard.GlobalHotKeys(hotkey_map)

    def start(self) -> None:
        self._listener.start()

    def stop(self) -> None:
        self._listener.stop()
