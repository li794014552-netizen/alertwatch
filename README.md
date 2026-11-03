# AlertWatch

YAML-configured page field watcher with Telegram or dry-run alerts.

Poll a page on a schedule, watch selected fields (price, title, listings), and push Telegram alerts when values change. Includes dry-run mode, SQLite snapshots, clear logs, and a local demo site so you can verify without touching production URLs.

## Requirements

- Python 3.11+

## Install

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Quick demo (dry-run)

1. Serve the bundled static demo site (port must match `configs/demo.yaml`):

```bash
cd demo_site
python -m http.server 8765
```

2. In another terminal, from the repo root, run a baseline poll (first successful poll stores snapshots with **no** alert):

```bash
alertwatch once -c configs/demo.yaml --dry-run
```

3. Edit `demo_site/index.html` and change the `.price` value (for example `$19.99` → `$24.99`).

4. Poll again — you should see a dry-run alert line:

```bash
alertwatch once -c configs/demo.yaml --dry-run
```

Example:

```text
[dry-run] AlertWatch: demo
URL: http://127.0.0.1:8765/
Changes:
  - price: $19.99 → $24.99
```

(`configs/demo.yaml` already sets `telegram.dry_run: true`; the CLI `--dry-run` flag also forces dry-run even if the config has `dry_run: false`.)

## CLI

| Command | Description |
|---------|-------------|
| `alertwatch once -c configs/demo.yaml` | Single poll cycle |
| `alertwatch watch -c configs/demo.yaml` | Loop using `poll_interval_seconds` until Ctrl-C |
| `--dry-run` | Force dry-run alerts (no Telegram HTTP) |

Exit behavior for `once`:

- Soft Telegram notify failures are logged and the process still exits `0`
- Hard fetch failures exit non-zero

## Telegram alerts

Set environment variables referenced by the demo config (`${TELEGRAM_BOT_TOKEN}` / `${TELEGRAM_CHAT_ID}`):

```bash
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"
```

Then turn off dry-run in config (`telegram.dry_run: false`) **or** use a config that already targets live Telegram, and run without `--dry-run`:

```bash
alertwatch once -c configs/demo.yaml
# or continuous:
alertwatch watch -c configs/demo.yaml
```

Create a bot with [@BotFather](https://t.me/BotFather) and use a chat ID for the destination.

## Config

See `configs/demo.yaml` for the v1 shape:

- `name`, `url`, `fields` (CSS selectors; optional `attr`, default text)
- `poll_interval_seconds` (used by `watch`)
- `request` (timeout, user-agent, retries)
- `telegram` (`bot_token` / `chat_id` with `${ENV}` placeholders, `dry_run`)
- `state_path` (SQLite snapshots), `log_path` (append-only text log)

## Tests

Offline unit tests (fixtures + mocked Telegram; no live network required):

```bash
pytest
```

## Upwork portfolio blurb

**Title:** Website Monitor → Telegram Alerts (Config-Driven Python CLI)

**Description:** Poll a page on a schedule, watch YAML-selected fields (price, title, listings), and push Telegram alerts when values change. Includes dry-run mode, SQLite snapshots, clear logs, and a local demo site so clients can verify without touching production URLs.
