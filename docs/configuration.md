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
