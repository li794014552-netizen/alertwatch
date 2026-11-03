# AlertWatch Design

**Date:** 2026-11-03  
**Goal:** A small, installable Python CLI that watches configured page fields on a schedule and alerts via Telegram (or dry-run) for an Upwork portfolio demo.

## Purpose

Show clients we can ship website monitoring bots: poll a page, detect field-level changes (title/price/etc.), notify Telegram with details and a link, keep a simple log. Targets fixed-price Upwork jobs like “monitor site → Telegram alerts”.

## Non-goals (v1)

- Proxy pools, CAPTCHA, authenticated sessions
- Playwright/Selenium (httpx + BeautifulSoup only)
- Email/SMS/multi-channel notify (Telegram + dry-run only)
- Web dashboard / admin UI
- Scraping third-party live sites in the demo (use bundled static demo HTML)

## Approach (approved)

Small installable package (`pip install -e .`) with YAML configs, bundled static demo site, SQLite snapshots, CLI `once` / `watch`, Telegram Bot API + dry-run, pytest.

## Architecture

```
demo_site/            Static HTML with mutable price for demos
configs/demo.yaml     URL, field selectors, interval, telegram
alertwatch/
  config.py           Load/validate YAML → Pydantic models
  fetch.py            httpx GET with timeout + basic retries
  parse.py            BeautifulSoup extract watched fields
  store.py            SQLite last-seen field snapshots
  diff.py             Compare current vs last; return Change list
  notify.py           Telegram sendMessage or dry-run print/log
  runner.py           one poll cycle: fetch→parse→diff→notify→store
  cli.py              Click: alertwatch once | watch
tests/                Unit tests; Telegram mocked; fixture HTML
```

**Data flow:** YAML → fetch URL → parse fields → diff vs SQLite → if changes: notify → upsert snapshot → append log line.

## Config shape (v1)

- `name`: watch job label
- `url`: page to poll
- `fields`: map of name → CSS selector (+ optional `attr`, default text)
- `poll_interval_seconds`: used by `watch` (default 60)
- `request`: timeout, user-agent, retries
- `telegram`: `bot_token` / `chat_id` (support `${ENV}` placeholders) + `dry_run: bool`
- `state_path`: SQLite path (default `./data/alertwatch.db`)
- `log_path`: append-only text log (default `./data/alertwatch.log`)

## CLI

- `alertwatch once -c configs/demo.yaml` — single poll cycle; exit 0 always after soft notify failures logged; exit non-zero on hard fetch failure
- `alertwatch watch -c configs/demo.yaml` — loop with `poll_interval_seconds` until Ctrl-C
- `--dry-run` CLI flag forces dry-run even if config has `dry_run: false`

## Change detection

For each configured field, compare normalized string values. First successful poll stores baseline with **no** alert. Later polls alert only when a field value differs. Message includes job name, field, old→new, and URL.

## Success criteria

1. Fresh clone: venv, `pip install -e ".[dev]"`, serve `demo_site`, `alertwatch once --dry-run` prints a clear dry-run message after forcing a demo price change
2. pytest green offline (fixtures + mocked Telegram)
3. README: install, dry-run demo, real Telegram env vars, portfolio blurb

## Portfolio copy (draft)

**Title:** Website Monitor → Telegram Alerts (Config-Driven Python CLI)  
**Description:** Poll a page on a schedule, watch YAML-selected fields (price, title, listings), and push Telegram alerts when values change. Includes dry-run mode, SQLite snapshots, clear logs, and a local demo site so clients can verify without touching production URLs.
