# SAS Study Companion — Design Spec
**Date:** 2026-04-25  
**Status:** Approved  

---

## Overview

A background study companion tool for Windows that monitors a student's screen, detects clinical SAS programming exam questions, and displays explanations and answers in a dedicated panel on a second monitor. Designed for practice and self-study — not for use during real exams.

The project will be published as an open-source GitHub repository with full setup documentation.

---

## Architecture

```
sas-study-companion/
├── README.md
├── LICENSE                        (MIT)
├── CONTRIBUTING.md
├── requirements.txt
├── .env.example
├── config.yaml
├── src/
│   ├── main.py                    (entry point + orchestrator)
│   ├── screen_capture.py          (screenshot via mss)
│   ├── change_detector.py         (pixel diff change detection)
│   ├── hotkey_manager.py          (global hotkeys via pynput)
│   ├── claude_client.py           (Claude Vision API integration)
│   ├── web_server.py              (FastAPI + WebSocket server)
│   └── session_logger.py          (JSONL session log writer)
├── static/
│   ├── panel.html                 (answer panel UI)
│   ├── style.css
│   └── app.js                     (WebSocket client)
├── docs/
│   ├── setup-windows.md
│   ├── configuration.md
│   └── screenshots/
└── logs/                          (.gitignored)
    └── session_YYYY-MM-DD.jsonl
```

---

## Components

### 1. `screen_capture.py`
- Uses `mss` to capture a specific monitor (configurable via `monitor_index` in `config.yaml`, default: `1` = primary)
- Returns the raw screenshot for use by the change detector and Claude client
- Supports capturing the full screen or a configurable region

### 2. `change_detector.py`
- Compares the latest screenshot against the previously stored one
- Resizes both to a small thumbnail before comparison (fast pixel diff)
- Fires a change event when the diff exceeds a configurable threshold (default: 8% of pixels)
- Applies a 1.5-second debounce after a change is detected to allow the screen to settle before triggering analysis

### 3. `hotkey_manager.py`
Registers three global hotkeys via `pynput`. All are configurable in `config.yaml`.

| Hotkey | Action |
|---|---|
| `Ctrl+Shift+S` | Toggle monitoring ON/OFF |
| `Ctrl+Shift+A` | Force analyze current screen immediately |
| `Ctrl+Shift+C` | Start / stop scroll capture session |

### 4. `claude_client.py`
- Sends screenshot(s) to `claude-sonnet-4-6` using the Anthropic Python SDK
- Uses the Claude Vision API (image payload)
- Enables **prompt caching** on the system prompt to reduce API costs across repeated calls
- Returns a structured response: `question`, `answer`, `explanation`

**System prompt:**
```
You are an expert clinical SAS programmer and exam tutor.
You will be shown a screenshot of a clinical SAS programming exam question.

Your job is to:
1. Identify the question being asked
2. Provide the correct answer with a clear explanation
3. If code is involved, show and explain the correct SAS code
4. Reference relevant CDISC standards (SDTM, ADaM) or SAS procedures where appropriate
5. Keep explanations educational — explain WHY, not just WHAT

Format your response as JSON with these keys:
- "question": what you understood the question to be
- "answer": the correct answer (concise)
- "explanation": why this is correct, with any relevant SAS/CDISC context and code examples
```

### 5. `web_server.py`
- FastAPI application serving the static panel files
- WebSocket endpoint at `/ws` — pushes updates to the panel in real time
- Exposes a `/status` endpoint (ON/OFF state)
- Runs on `localhost:8765` (configurable)

### 6. `session_logger.py`
- Appends one JSON record per analysis to `logs/session_YYYY-MM-DD.jsonl`
- Record schema:
```json
{
  "timestamp": "2026-04-25T14:32:05",
  "trigger": "auto_change | manual_hotkey | scroll_capture",
  "question": "...",
  "answer": "...",
  "explanation": "...",
  "screenshot": null
}
```
- Screenshot saving is off by default; configurable in `config.yaml`
- One file per calendar day

### 7. Answer Panel (`static/panel.html`)
- Browser tab opened on the second monitor
- Connects to the WebSocket server on load
- Displays: monitoring status indicator, question, answer, explanation, last-updated timestamp, link to session log
- SAS code blocks rendered with **Prism.js** syntax highlighting (loaded locally — no CDN dependency)
- Shows a spinner while Claude is processing

---

## Core Loop

```
[Monitoring ON]
    │
    ├── Every 20 seconds:
    │     Capture screenshot
    │     → change_detector: diff vs. previous
    │     → if diff > 8%: debounce 1.5s → send to Claude
    │
    ├── Ctrl+Shift+A (manual):
    │     Capture screenshot immediately → send to Claude
    │
    └── Ctrl+Shift+C (scroll capture):
          Start session: capture current screen
          → on each scroll event (debounced 500ms): capture additional frame
          Stop session (second Ctrl+Shift+C press):
          → stitch all frames vertically into one tall image
          → send stitched image to Claude

[On Claude response]
    → push result to panel via WebSocket
    → append to session log
```

---

## Configuration (`config.yaml`)

```yaml
monitor:
  scan_interval_seconds: 20
  change_threshold_percent: 8
  debounce_seconds: 1.5
  monitor_index: 1           # 1 = primary monitor (where the exam is shown)

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

---

## Environment Variables (`.env`)

```
ANTHROPIC_API_KEY=your_key_here
```

---

## Repository & Distribution

- **License:** MIT
- **README:** includes overview, prerequisites, one-command setup, hotkey reference, and screenshots of the panel
- **`docs/setup-windows.md`:** step-by-step guide (Python install, venv, pip install, API key setup, launching)
- **`docs/configuration.md`:** all `config.yaml` options explained
- **`.gitignore`:** excludes `logs/`, `.env`, `__pycache__/`, `.venv/`
- **`.env.example`:** safe template for API key

---

## Dependencies

```
anthropic          # Claude API SDK
mss                # Screen capture
Pillow             # Image processing and stitching
fastapi            # Web server
uvicorn            # ASGI server
websockets         # WebSocket support
pynput             # Global hotkeys
python-dotenv      # .env loading
pyyaml             # config.yaml parsing
```

---

## Out of Scope

- macOS / Linux support (Windows only for v1)
- OCR fallback (Claude Vision handles all image reading)
- Multi-monitor screen selection UI (monitor index is set in `config.yaml`)
- User accounts or cloud sync of session logs
