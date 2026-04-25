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
