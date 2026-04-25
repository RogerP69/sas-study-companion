# SAS Study Companion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows desktop study companion that captures the screen, detects exam question changes, queries Claude Vision, and streams explanations to a second-monitor browser panel.

**Architecture:** Seven Python modules with single responsibilities, a FastAPI/WebSocket server for real-time updates, and a browser-based panel with Prism.js SAS syntax highlighting. A background thread checks for screen changes every 20s; three global hotkeys allow manual triggers and scroll-capture for long questions.

**Tech Stack:** Python 3.10+, anthropic SDK, mss, Pillow, FastAPI, uvicorn, websockets, pynput, python-dotenv, pyyaml, pytest

---

## File Map

| File | Responsibility |
|---|---|
| `src/main.py` | Entry point; wires all modules together; runs monitor loop |
| `src/screen_capture.py` | Screenshot via mss; returns PIL Image |
| `src/change_detector.py` | Pixel-diff comparison; fires on threshold breach |
| `src/hotkey_manager.py` | Global hotkeys via pynput; calls provided callbacks |
| `src/claude_client.py` | Claude Vision API call with prompt caching; returns parsed dict |
| `src/web_server.py` | FastAPI app; WebSocket broadcast; status endpoint |
| `src/session_logger.py` | Appends JSONL records to daily log file |
| `static/panel.html` | Answer panel UI |
| `static/style.css` | Panel styling |
| `static/app.js` | WebSocket client; renders results with Prism.js |
| `static/prism/prism.min.js` | Prism.js core (downloaded, not CDN) |
| `static/prism/prism-sas.min.js` | SAS language plugin for Prism.js |
| `static/prism/prism.min.css` | Syntax highlight theme |
| `config.yaml` | All tunable settings |
| `.env.example` | API key template |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Excludes logs/, .env, __pycache__, .venv |
| `tests/conftest.py` | Adds src/ to sys.path |
| `tests/test_session_logger.py` | Logger tests |
| `tests/test_change_detector.py` | Change detection tests |
| `tests/test_claude_client.py` | Claude client tests (mocked) |
| `tests/test_web_server.py` | FastAPI/WebSocket tests |
| `docs/setup-windows.md` | Step-by-step Windows setup guide |
| `docs/configuration.md` | All config.yaml options explained |

---

### Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `config.yaml`
- Create: `LICENSE`
- Create: `CONTRIBUTING.md`
- Create: `tests/conftest.py`

- [ ] **Step 1: Create `requirements.txt`**

```
anthropic>=0.40.0
mss>=9.0.0
Pillow>=10.0.0
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
websockets>=13.0
pynput>=1.7.7
python-dotenv>=1.0.0
pyyaml>=6.0.2
pytest>=8.0.0
pytest-asyncio>=0.24.0
httpx>=0.27.0
```

- [ ] **Step 2: Create `.env.example`**

```
ANTHROPIC_API_KEY=your_key_here
```

- [ ] **Step 3: Create `.gitignore`**

```
.env
logs/
__pycache__/
*.pyc
.venv/
*.egg-info/
dist/
.pytest_cache/
```

- [ ] **Step 4: Create `config.yaml`**

```yaml
monitor:
  scan_interval_seconds: 20
  change_threshold_percent: 8
  debounce_seconds: 1.5
  monitor_index: 1

hotkeys:
  toggle: "ctrl+shift+s"
  analyze: "ctrl+shift+a"
  scroll_capture: "ctrl+shift+c"

server:
  host: "localhost"
  port: 8765

claude:
  model: "claude-sonnet-4-6"
  max_tokens: 1500

logging:
  save_screenshots: false
```

- [ ] **Step 5: Create `LICENSE`**

```
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 6: Create `CONTRIBUTING.md`**

```markdown
# Contributing

1. Fork the repository and create a feature branch
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests before submitting: `pytest tests/ -v`
4. Open a pull request with a clear description of what was changed and why
```

- [ ] **Step 7: Create `tests/conftest.py`**

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

- [ ] **Step 8: Install dependencies**

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

- [ ] **Step 9: Commit**

```bash
git add requirements.txt .env.example .gitignore config.yaml LICENSE CONTRIBUTING.md tests/conftest.py
git commit -m "feat: project scaffolding"
```

---

### Task 2: `session_logger.py`

**Files:**
- Create: `src/session_logger.py`
- Create: `tests/test_session_logger.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_session_logger.py`:

```python
import json
from datetime import datetime
from unittest.mock import patch

import session_logger as sl
from session_logger import SessionLogger


def test_log_creates_file(tmp_path):
    with patch.object(sl, "LOGS_DIR", tmp_path):
        logger = SessionLogger()
        logger.log(
            trigger="manual_hotkey",
            question="What does PROC MEANS do?",
            answer="Computes descriptive statistics",
            explanation="PROC MEANS calculates statistics like mean, std, min, max.",
        )
    files = list(tmp_path.glob("session_*.jsonl"))
    assert len(files) == 1


def test_log_record_structure(tmp_path):
    with patch.object(sl, "LOGS_DIR", tmp_path):
        logger = SessionLogger()
        logger.log(trigger="auto_change", question="Q", answer="A", explanation="E")
    record = json.loads(logger.path.read_text(encoding="utf-8").strip())
    assert record["trigger"] == "auto_change"
    assert record["question"] == "Q"
    assert record["answer"] == "A"
    assert record["explanation"] == "E"
    assert record["screenshot"] is None
    assert "timestamp" in record


def test_log_appends_multiple_records(tmp_path):
    with patch.object(sl, "LOGS_DIR", tmp_path):
        logger = SessionLogger()
        for i in range(3):
            logger.log(trigger="manual_hotkey", question=f"Q{i}", answer=f"A{i}", explanation=f"E{i}")
    lines = logger.path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 3


def test_log_filename_is_todays_date(tmp_path):
    with patch.object(sl, "LOGS_DIR", tmp_path):
        logger = SessionLogger()
    expected = datetime.now().strftime("session_%Y-%m-%d.jsonl")
    assert logger.path.name == expected
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_session_logger.py -v
```

Expected: `ModuleNotFoundError: No module named 'session_logger'`

- [ ] **Step 3: Implement `src/session_logger.py`**

```python
import json
from datetime import datetime
from pathlib import Path

LOGS_DIR = Path(__file__).parent.parent / "logs"


class SessionLogger:
    def __init__(self):
        LOGS_DIR.mkdir(exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        self._path = LOGS_DIR / f"session_{date_str}.jsonl"

    def log(
        self,
        trigger: str,
        question: str,
        answer: str,
        explanation: str,
        screenshot: str | None = None,
    ) -> None:
        record = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "trigger": trigger,
            "question": question,
            "answer": answer,
            "explanation": explanation,
            "screenshot": screenshot,
        }
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    @property
    def path(self) -> Path:
        return self._path
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_session_logger.py -v
```

Expected: 4 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add src/session_logger.py tests/test_session_logger.py
git commit -m "feat: session logger with JSONL output"
```

---

### Task 3: `screen_capture.py`

**Files:**
- Create: `src/screen_capture.py`
- Create: `tests/test_screen_capture.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_screen_capture.py`:

```python
from unittest.mock import MagicMock, patch
from PIL import Image


def test_capture_returns_pil_image():
    mock_screenshot = MagicMock()
    mock_screenshot.size = (1920, 1080)
    mock_screenshot.bgra = b"\x00" * (1920 * 1080 * 4)

    mock_sct = MagicMock()
    mock_sct.__enter__ = lambda s: s
    mock_sct.__exit__ = MagicMock(return_value=False)
    mock_sct.monitors = [None, {"left": 0, "top": 0, "width": 1920, "height": 1080}]
    mock_sct.grab.return_value = mock_screenshot

    with patch("screen_capture.mss.mss", return_value=mock_sct):
        from screen_capture import capture
        result = capture(monitor_index=1)

    assert isinstance(result, Image.Image)
    assert result.size == (1920, 1080)


def test_capture_uses_correct_monitor_index():
    mock_screenshot = MagicMock()
    mock_screenshot.size = (2560, 1440)
    mock_screenshot.bgra = b"\x00" * (2560 * 1440 * 4)

    mock_sct = MagicMock()
    mock_sct.__enter__ = lambda s: s
    mock_sct.__exit__ = MagicMock(return_value=False)
    mock_sct.monitors = [
        None,
        {"left": 0, "top": 0, "width": 1920, "height": 1080},
        {"left": 1920, "top": 0, "width": 2560, "height": 1440},
    ]
    mock_sct.grab.return_value = mock_screenshot

    with patch("screen_capture.mss.mss", return_value=mock_sct):
        from screen_capture import capture
        capture(monitor_index=2)
        mock_sct.grab.assert_called_once_with(
            {"left": 1920, "top": 0, "width": 2560, "height": 1440}
        )
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_screen_capture.py -v
```

Expected: `ModuleNotFoundError: No module named 'screen_capture'`

- [ ] **Step 3: Implement `src/screen_capture.py`**

```python
import mss
from PIL import Image


def capture(monitor_index: int = 1) -> Image.Image:
    with mss.mss() as sct:
        monitor = sct.monitors[monitor_index]
        screenshot = sct.grab(monitor)
        return Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_screen_capture.py -v
```

Expected: 2 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add src/screen_capture.py tests/test_screen_capture.py
git commit -m "feat: screen capture module"
```

---

### Task 4: `change_detector.py`

**Files:**
- Create: `src/change_detector.py`
- Create: `tests/test_change_detector.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_change_detector.py`:

```python
from PIL import Image
from change_detector import ChangeDetector


def _solid_image(color: tuple, size=(400, 300)) -> Image.Image:
    img = Image.new("RGB", size, color)
    return img


def test_first_call_never_triggers():
    detector = ChangeDetector(threshold_percent=8.0)
    result = detector.has_changed(_solid_image((255, 0, 0)))
    assert result is False


def test_identical_images_do_not_trigger():
    detector = ChangeDetector(threshold_percent=8.0)
    img = _solid_image((100, 100, 100))
    detector.has_changed(img)
    assert detector.has_changed(img) is False


def test_completely_different_images_trigger():
    detector = ChangeDetector(threshold_percent=8.0)
    detector.has_changed(_solid_image((0, 0, 0)))
    result = detector.has_changed(_solid_image((255, 255, 255)))
    assert result is True


def test_threshold_respected():
    detector_sensitive = ChangeDetector(threshold_percent=1.0)
    detector_tolerant = ChangeDetector(threshold_percent=90.0)

    base = _solid_image((0, 0, 0))
    # Image with roughly 50% pixels changed
    changed = Image.new("RGB", (400, 300))
    pixels = [(255, 255, 255) if i < 150 * 400 else (0, 0, 0) for i in range(400 * 300)]
    changed.putdata(pixels)

    detector_sensitive.has_changed(base)
    detector_tolerant.has_changed(base)

    assert detector_sensitive.has_changed(changed) is True
    assert detector_tolerant.has_changed(changed) is False


def test_reset_clears_previous():
    detector = ChangeDetector(threshold_percent=8.0)
    detector.has_changed(_solid_image((0, 0, 0)))
    detector.reset()
    # After reset, first call should never trigger
    result = detector.has_changed(_solid_image((255, 255, 255)))
    assert result is False
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_change_detector.py -v
```

Expected: `ModuleNotFoundError: No module named 'change_detector'`

- [ ] **Step 3: Implement `src/change_detector.py`**

```python
from PIL import Image, ImageChops

_THUMBNAIL_SIZE = (200, 150)
_CHANGE_SENSITIVITY = 30  # sum of RGB channel diffs to count a pixel as "changed"


class ChangeDetector:
    def __init__(self, threshold_percent: float = 8.0):
        self._threshold = threshold_percent / 100.0
        self._previous: Image.Image | None = None

    def has_changed(self, current: Image.Image) -> bool:
        thumb = current.resize(_THUMBNAIL_SIZE).convert("RGB")
        if self._previous is None:
            self._previous = thumb
            return False
        diff = ImageChops.difference(self._previous, thumb)
        pixels = list(diff.getdata())
        changed = sum(1 for r, g, b in pixels if r + g + b > _CHANGE_SENSITIVITY)
        self._previous = thumb
        return (changed / len(pixels)) >= self._threshold

    def reset(self) -> None:
        self._previous = None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_change_detector.py -v
```

Expected: 5 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add src/change_detector.py tests/test_change_detector.py
git commit -m "feat: change detector with configurable threshold"
```

---

### Task 5: `claude_client.py`

**Files:**
- Create: `src/claude_client.py`
- Create: `tests/test_claude_client.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_claude_client.py`:

```python
import json
from unittest.mock import MagicMock, patch
from PIL import Image
from claude_client import ClaudeClient, _image_to_base64


def _blank_image() -> Image.Image:
    return Image.new("RGB", (100, 80), (200, 200, 200))


def test_image_to_base64_returns_string():
    result = _image_to_base64(_blank_image())
    assert isinstance(result, str)
    assert len(result) > 0


def test_analyze_parses_response():
    expected = {
        "question": "What does PROC SORT do?",
        "answer": "Sorts a SAS dataset",
        "explanation": "PROC SORT reorders observations by one or more variables.",
    }

    mock_content = MagicMock()
    mock_content.text = json.dumps(expected)

    mock_response = MagicMock()
    mock_response.content = [mock_content]

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("claude_client.anthropic.Anthropic", return_value=mock_client):
        client = ClaudeClient(model="claude-sonnet-4-6", max_tokens=1500)
        result = client.analyze(_blank_image())

    assert result["question"] == expected["question"]
    assert result["answer"] == expected["answer"]
    assert result["explanation"] == expected["explanation"]


def test_analyze_sends_image_as_base64():
    mock_content = MagicMock()
    mock_content.text = json.dumps({"question": "Q", "answer": "A", "explanation": "E"})
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("claude_client.anthropic.Anthropic", return_value=mock_client):
        client = ClaudeClient()
        client.analyze(_blank_image())

    call_kwargs = mock_client.messages.create.call_args
    messages = call_kwargs.kwargs["messages"]
    image_block = messages[0]["content"][0]
    assert image_block["type"] == "image"
    assert image_block["source"]["type"] == "base64"
    assert image_block["source"]["media_type"] == "image/png"


def test_analyze_uses_prompt_caching():
    mock_content = MagicMock()
    mock_content.text = json.dumps({"question": "Q", "answer": "A", "explanation": "E"})
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("claude_client.anthropic.Anthropic", return_value=mock_client):
        client = ClaudeClient()
        client.analyze(_blank_image())

    call_kwargs = mock_client.messages.create.call_args
    system = call_kwargs.kwargs["system"]
    assert system[0]["cache_control"] == {"type": "ephemeral"}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_claude_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'claude_client'`

- [ ] **Step 3: Implement `src/claude_client.py`**

```python
import base64
import json
from io import BytesIO

import anthropic
from PIL import Image

_SYSTEM_PROMPT = """You are an expert clinical SAS programmer and exam tutor.
You will be shown a screenshot of a clinical SAS programming exam question.

Your job is to:
1. Identify the question being asked
2. Provide the correct answer with a clear explanation
3. If code is involved, show and explain the correct SAS code
4. Reference relevant CDISC standards (SDTM, ADaM) or SAS procedures where appropriate
5. Keep explanations educational — explain WHY, not just WHAT

Format your response as JSON with these exact keys:
- "question": what you understood the question to be
- "answer": the correct answer (concise)
- "explanation": why this is correct, with any relevant SAS/CDISC context and code examples

Respond with valid JSON only — no markdown wrapper, no extra text."""


def _image_to_base64(image: Image.Image) -> str:
    buf = BytesIO()
    image.save(buf, format="PNG")
    return base64.standard_b64encode(buf.getvalue()).decode("utf-8")


class ClaudeClient:
    def __init__(self, model: str = "claude-sonnet-4-6", max_tokens: int = 1500):
        self._client = anthropic.Anthropic()
        self._model = model
        self._max_tokens = max_tokens

    def analyze(self, image: Image.Image) -> dict:
        image_data = _image_to_base64(image)
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": "Please analyze this exam question."},
                    ],
                }
            ],
        )
        return json.loads(response.content[0].text)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_claude_client.py -v
```

Expected: 4 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add src/claude_client.py tests/test_claude_client.py
git commit -m "feat: Claude Vision client with prompt caching"
```

---

### Task 6: `web_server.py`

**Files:**
- Create: `src/web_server.py`
- Create: `tests/test_web_server.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_web_server.py`:

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from pathlib import Path


@pytest.fixture(autouse=True)
def reset_server_state():
    import web_server
    web_server._connections.clear()
    web_server._state["monitoring"] = False
    web_server._state["processing"] = False
    yield


def test_status_endpoint_returns_state():
    from web_server import app
    client = TestClient(app)
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["monitoring"] is False
    assert data["processing"] is False


def test_set_monitoring_updates_state():
    from web_server import app, set_monitoring
    set_monitoring(True)
    client = TestClient(app)
    response = client.get("/status")
    assert response.json()["monitoring"] is True


def test_set_processing_updates_state():
    from web_server import set_processing
    import web_server
    set_processing(True)
    assert web_server._state["processing"] is True


def test_websocket_receives_status_on_connect():
    from web_server import app
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        data = ws.receive_json()
        assert data["type"] == "status"
        assert "monitoring" in data
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_web_server.py -v
```

Expected: `ModuleNotFoundError: No module named 'web_server'`

- [ ] **Step 3: Implement `src/web_server.py`**

```python
import asyncio
from pathlib import Path
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

_STATIC_DIR = Path(__file__).parent.parent / "static"

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

_connections: Set[WebSocket] = set()
_state: dict = {"monitoring": False, "processing": False}
_event_loop: asyncio.AbstractEventLoop | None = None


@app.on_event("startup")
async def _capture_loop() -> None:
    global _event_loop
    _event_loop = asyncio.get_running_loop()


@app.get("/")
async def serve_panel() -> FileResponse:
    return FileResponse(str(_STATIC_DIR / "panel.html"))


@app.get("/status")
async def get_status() -> dict:
    return dict(_state)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    _connections.add(websocket)
    await websocket.send_json({"type": "status", **_state})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _connections.discard(websocket)


async def broadcast(message: dict) -> None:
    dead: Set[WebSocket] = set()
    for ws in list(_connections):
        try:
            await ws.send_json(message)
        except Exception:
            dead.add(ws)
    _connections.difference_update(dead)


def get_event_loop() -> asyncio.AbstractEventLoop | None:
    return _event_loop


def set_monitoring(active: bool) -> None:
    _state["monitoring"] = active


def set_processing(active: bool) -> None:
    _state["processing"] = active
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_web_server.py -v
```

Expected: 4 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add src/web_server.py tests/test_web_server.py
git commit -m "feat: FastAPI server with WebSocket broadcast"
```

---

### Task 7: `hotkey_manager.py`

**Files:**
- Create: `src/hotkey_manager.py`

Note: Global hotkeys require OS-level input hooks and cannot be meaningfully unit tested in a headless environment. Manual verification is done in Task 11.

- [ ] **Step 1: Implement `src/hotkey_manager.py`**

```python
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
```

- [ ] **Step 2: Commit**

```bash
git add src/hotkey_manager.py
git commit -m "feat: global hotkey manager via pynput"
```

---

### Task 8: Static Panel (HTML / CSS / JS)

**Files:**
- Create: `static/panel.html`
- Create: `static/style.css`
- Create: `static/app.js`
- Download: `static/prism/prism.min.css`
- Download: `static/prism/prism.min.js`
- Download: `static/prism/prism-sas.min.js`

- [ ] **Step 1: Download Prism.js files**

Go to https://prismjs.com/download.html, select:
- Theme: **Tomorrow Night** (dark theme)
- Language: **SAS**

Click Download JS and Download CSS, save to `static/prism/`. Rename to:
- `prism.min.js`
- `prism-sas.min.js` (download the SAS component separately from https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-sas.min.js)
- `prism.min.css`

Or run:
```bash
mkdir static\prism
curl -o static/prism/prism.min.css https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css
curl -o static/prism/prism.min.js https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js
curl -o static/prism/prism-sas.min.js https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-sas.min.js
```

- [ ] **Step 2: Create `static/style.css`**

```css
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #1a1a2e;
    color: #e0e0e0;
    min-height: 100vh;
    padding: 16px;
}

header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding-bottom: 12px;
    border-bottom: 1px solid #2a2a4a;
    margin-bottom: 16px;
}

h1 { font-size: 1rem; font-weight: 600; color: #a0a0c0; }

.indicator {
    width: 10px; height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
}
.indicator.on  { background: #4ade80; box-shadow: 0 0 6px #4ade80; }
.indicator.off { background: #ef4444; }

#status-text { font-size: 0.8rem; color: #888; }

.spinner {
    display: none;
    text-align: center;
    padding: 32px;
    color: #888;
    font-size: 0.9rem;
}
.spinner::before {
    content: "⟳ ";
    animation: spin 1s linear infinite;
    display: inline-block;
}
@keyframes spin { to { transform: rotate(360deg); } }

.section { margin-bottom: 16px; }

.label {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #6060a0;
    margin-bottom: 4px;
}

.question-box {
    background: #16213e;
    border-left: 3px solid #4f46e5;
    padding: 10px 12px;
    border-radius: 4px;
    font-size: 0.9rem;
    line-height: 1.5;
}

.answer-box {
    background: #0f3460;
    border-left: 3px solid #4ade80;
    padding: 10px 12px;
    border-radius: 4px;
    font-size: 0.95rem;
    font-weight: 600;
    color: #a0f0b0;
}

.explanation-box {
    background: #16213e;
    padding: 10px 12px;
    border-radius: 4px;
    font-size: 0.85rem;
    line-height: 1.6;
}

.explanation-box pre {
    margin: 8px 0;
    border-radius: 4px;
    overflow-x: auto;
}

footer {
    margin-top: 16px;
    font-size: 0.75rem;
    color: #555;
    border-top: 1px solid #2a2a4a;
    padding-top: 8px;
    display: flex;
    justify-content: space-between;
}

#result { display: none; }
```

- [ ] **Step 3: Create `static/panel.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAS Study Companion</title>
    <link rel="stylesheet" href="/static/style.css">
    <link rel="stylesheet" href="/static/prism/prism.min.css">
</head>
<body>
    <header>
        <div class="indicator off" id="status-indicator"></div>
        <h1>SAS Study Companion</h1>
        <span id="status-text">Connecting...</span>
    </header>

    <div class="spinner" id="spinner">Analyzing question...</div>

    <div id="result">
        <div class="section">
            <div class="label">Question</div>
            <div class="question-box" id="question-text"></div>
        </div>
        <div class="section">
            <div class="label">Answer</div>
            <div class="answer-box" id="answer-text"></div>
        </div>
        <div class="section">
            <div class="label">Explanation</div>
            <div class="explanation-box" id="explanation-text"></div>
        </div>
    </div>

    <footer>
        <span id="timestamp"></span>
        <span id="log-link"></span>
    </footer>

    <script src="/static/prism/prism.min.js"></script>
    <script src="/static/prism/prism-sas.min.js"></script>
    <script src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 4: Create `static/app.js`**

```javascript
const PORT = 8765;
let ws;

function connect() {
    ws = new WebSocket(`ws://localhost:${PORT}/ws`);

    ws.onopen = () => {
        document.getElementById('status-text').textContent = 'Connected';
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'status') {
            updateStatus(data.monitoring, data.processing);
        } else if (data.type === 'processing') {
            showSpinner();
        } else if (data.type === 'result') {
            showResult(data);
        }
    };

    ws.onclose = () => {
        document.getElementById('status-text').textContent = 'Reconnecting...';
        document.getElementById('status-indicator').className = 'indicator off';
        setTimeout(connect, 3000);
    };

    ws.onerror = () => ws.close();
}

function updateStatus(monitoring, processing) {
    const indicator = document.getElementById('status-indicator');
    indicator.className = 'indicator ' + (monitoring ? 'on' : 'off');
    document.getElementById('status-text').textContent = monitoring ? 'Monitoring ON' : 'Monitoring OFF';
    if (!processing) hideSpinner();
}

function showSpinner() {
    document.getElementById('spinner').style.display = 'block';
    document.getElementById('result').style.display = 'none';
}

function hideSpinner() {
    document.getElementById('spinner').style.display = 'none';
}

function showResult(data) {
    hideSpinner();
    document.getElementById('question-text').textContent = data.question || '';
    document.getElementById('answer-text').textContent = data.answer || '';

    const explanationEl = document.getElementById('explanation-text');
    explanationEl.innerHTML = formatExplanation(data.explanation || '');
    Prism.highlightAllUnder(explanationEl);

    const ts = data.timestamp ? new Date(data.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
    document.getElementById('timestamp').textContent = 'Last updated: ' + ts;
    document.getElementById('result').style.display = 'block';
}

function formatExplanation(text) {
    return text
        .replace(/```sas\n?([\s\S]*?)```/g, '<pre><code class="language-sas">$1</code></pre>')
        .replace(/```\n?([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
}

connect();
```

- [ ] **Step 5: Commit**

```bash
git add static/
git commit -m "feat: answer panel with SAS syntax highlighting"
```

---

### Task 9: `main.py` (Orchestrator)

**Files:**
- Create: `src/main.py`

- [ ] **Step 1: Implement `src/main.py`**

```python
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
```

- [ ] **Step 2: Run all tests to verify nothing is broken**

```bash
pytest tests/ -v
```

Expected: all previously passing tests still PASS

- [ ] **Step 3: Commit**

```bash
git add src/main.py
git commit -m "feat: main orchestrator wiring all modules"
```

---

### Task 10: Documentation

**Files:**
- Create: `docs/setup-windows.md`
- Create: `docs/configuration.md`

- [ ] **Step 1: Create `docs/setup-windows.md`**

```markdown
# Windows Setup Guide

## Prerequisites

- Windows 10 or 11
- Python 3.10 or higher: https://www.python.org/downloads/
  - During install, check "Add Python to PATH"
- An Anthropic API key: https://console.anthropic.com

## Step-by-Step Setup

### 1. Clone the repository

Open Command Prompt or PowerShell and run:

    git clone https://github.com/RogerP69/sas-study-companion.git
    cd sas-study-companion

### 2. Create a virtual environment

    python -m venv .venv
    .venv\Scripts\activate

You should see `(.venv)` at the start of your prompt.

### 3. Install dependencies

    pip install -r requirements.txt

### 4. Add your API key

Copy the example file:

    copy .env.example .env

Open `.env` in Notepad and replace `your_key_here` with your actual Anthropic API key:

    ANTHROPIC_API_KEY=sk-ant-...

### 5. (Optional) Configure settings

Open `config.yaml` to adjust:
- `monitor.monitor_index` — which monitor shows the exam (1 = primary)
- `monitor.scan_interval_seconds` — how often to check for changes
- `hotkeys` — change any keyboard shortcut

See [configuration.md](configuration.md) for full details.

### 6. Launch

    python src/main.py

A browser tab will open with the answer panel. Move it to your second monitor.

## Usage

| Hotkey | Action |
|---|---|
| Ctrl+Shift+S | Toggle monitoring ON/OFF |
| Ctrl+Shift+A | Analyze current screen now |
| Ctrl+Shift+C | Start/stop scroll capture |

Press **Ctrl+C** in the terminal to quit.

## Troubleshooting

**"No module named X"** — Make sure your virtual environment is activated (`.venv\Scripts\activate`).

**Hotkeys not working** — Run the terminal as Administrator (right-click → Run as administrator).

**Panel not loading** — Check that the server is running on port 8765. Open http://localhost:8765 manually.
```

- [ ] **Step 2: Create `docs/configuration.md`**

```markdown
# Configuration Reference

All settings live in `config.yaml` at the project root.

## `monitor`

| Key | Default | Description |
|---|---|---|
| `scan_interval_seconds` | `20` | How often (in seconds) the monitor loop checks for screen changes |
| `change_threshold_percent` | `8` | Percentage of pixels that must differ to count as a new question (lower = more sensitive) |
| `debounce_seconds` | `1.5` | Seconds to wait after a change is detected before capturing (allows page to settle) |
| `monitor_index` | `1` | Which monitor to capture. `1` = primary, `2` = second monitor, etc. |

## `hotkeys`

Each value is a key combination string using `+` as separator.

| Key | Default | Action |
|---|---|---|
| `toggle` | `ctrl+shift+s` | Turn monitoring on or off |
| `analyze` | `ctrl+shift+a` | Force-analyze the current screen immediately |
| `scroll_capture` | `ctrl+shift+c` | Start or stop a scroll capture session |

Supported modifiers: `ctrl`, `shift`, `alt`. Example: `"alt+shift+q"`

## `server`

| Key | Default | Description |
|---|---|---|
| `host` | `localhost` | Host the panel server binds to |
| `port` | `8765` | Port number for the panel and WebSocket |

## `claude`

| Key | Default | Description |
|---|---|---|
| `model` | `claude-sonnet-4-6` | Claude model to use for analysis |
| `max_tokens` | `1500` | Maximum tokens in Claude's response |

## `logging`

| Key | Default | Description |
|---|---|---|
| `save_screenshots` | `false` | If `true`, saves the captured screenshot alongside each log entry |
```

- [ ] **Step 3: Commit**

```bash
git add docs/setup-windows.md docs/configuration.md
git commit -m "docs: setup guide and configuration reference"
```

---

### Task 11: Final Integration Smoke Test

- [ ] **Step 1: Run the full test suite**

```bash
pytest tests/ -v
```

Expected: all tests PASS

- [ ] **Step 2: Launch the app and verify manually**

```bash
python src/main.py
```

Verify:
1. Browser opens with the panel on `http://localhost:8765`
2. Panel shows "Monitoring OFF" indicator (red dot)
3. Press `Ctrl+Shift+S` → indicator turns green, console shows "Monitoring ON"
4. Open any webpage with text on the primary monitor
5. Press `Ctrl+Shift+A` → spinner appears in panel, result appears after Claude responds
6. Navigate to a new page, wait up to 20s → auto-detection triggers a new analysis
7. On a long question: press `Ctrl+Shift+C`, scroll down slowly, press `Ctrl+Shift+C` again → stitched image is analyzed
8. Check `logs/session_YYYY-MM-DD.jsonl` contains the logged entries

- [ ] **Step 3: Push everything to GitHub**

```bash
git push origin master
```
```
