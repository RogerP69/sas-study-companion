# SAS Study Companion

A background study tool for Windows that monitors your screen, detects clinical SAS programming exam questions, and displays explanations and answers in a dedicated panel on your second monitor.

Powered by [Claude Vision API](https://www.anthropic.com) (Anthropic). Designed for **practice and self-study only**.

---

## Features

- **Continuous screen monitoring** — detects when a new question appears automatically
- **Manual trigger** — force an analysis at any time with a hotkey
- **Scroll capture** — stitch multiple frames for long questions that require scrolling
- **Second monitor panel** — clean answer panel with SAS syntax highlighting
- **Session log** — every Q&A pair saved to a local `.jsonl` file for review
- **Fully configurable** — hotkeys, scan interval, sensitivity, Claude model via `config.yaml`

---

## Prerequisites

- Windows 10 / 11
- Python 3.10 or higher → [python.org](https://www.python.org/downloads/)
- An Anthropic API key → [console.anthropic.com](https://console.anthropic.com)

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/RogerP69/sas-study-companion.git
cd sas-study-companion
```

### 2. Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

Copy the example env file and add your Anthropic API key:

```bash
copy .env.example .env
```

Open `.env` and replace the placeholder:

```
ANTHROPIC_API_KEY=your_key_here
```

### 5. (Optional) Adjust settings

Edit `config.yaml` to change hotkeys, scan interval, or monitor index. See [docs/configuration.md](docs/configuration.md) for all options.

### 6. Launch

```bash
python src/main.py
```

A browser tab will open automatically with the answer panel. Move it to your second monitor.

---

## Hotkeys

| Hotkey | Action |
|---|---|
| `Ctrl+Shift+S` | Toggle monitoring ON / OFF |
| `Ctrl+Shift+A` | Force analyze current screen immediately |
| `Ctrl+Shift+C` | Start / stop scroll capture (for long questions) |

All hotkeys are configurable in `config.yaml`.

---

## Scroll Capture (Long Questions)

If a question is longer than your screen:

1. Press `Ctrl+Shift+C` to start a capture session
2. Scroll through the full question at your own pace
3. Press `Ctrl+Shift+C` again to stop — all frames are stitched and sent to Claude as one image

---

## Session Logs

Each practice session is saved to `logs/session_YYYY-MM-DD.jsonl`. Every entry includes:

- Timestamp
- Trigger type (`auto_change`, `manual_hotkey`, `scroll_capture`)
- Question, answer, and explanation

Logs are stored locally and never uploaded anywhere.

---

## Configuration

See [docs/configuration.md](docs/configuration.md) for a full reference.

Key settings in `config.yaml`:

```yaml
monitor:
  scan_interval_seconds: 20   # How often to check for screen changes
  change_threshold_percent: 8 # Sensitivity (lower = more sensitive)
  monitor_index: 1            # Which monitor to capture (1 = primary)

claude:
  model: "claude-sonnet-4-6"
  max_tokens: 1500
```

---

## Project Structure

```
sas-study-companion/
├── src/                  # Python source modules
├── static/               # Answer panel (HTML/CSS/JS)
├── docs/                 # Setup and configuration guides
├── logs/                 # Session logs (auto-created, gitignored)
├── config.yaml           # All tunable settings
└── .env.example          # API key template
```

---

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

---

## License

MIT — see [LICENSE](LICENSE) for details.
