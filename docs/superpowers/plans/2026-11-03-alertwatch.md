# AlertWatch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship an installable Python CLI that watches YAML-configured page fields and alerts via Telegram or dry-run, with a bundled demo site for portfolio demos.

**Architecture:** Config (Pydantic) → fetch (httpx) → parse (BeautifulSoup) → SQLite snapshot store → diff → notify (Telegram/dry-run); Click CLI `once`/`watch`; pytest with fixtures and mocked HTTP.

**Tech Stack:** Python 3.11+, httpx, beautifulsoup4, pydantic v2, click, pyyaml, pytest

## Global Constraints

- Repo root: `/workspace/alertwatch`
- No Playwright/Selenium in v1
- Demo must not scrape third-party live sites; use `demo_site/`
- Unit tests must pass offline (fixture HTML + mock Telegram HTTP)
- Package name / CLI: `alertwatch`
- English README (Upwork portfolio)
- Telegram credentials only via config `${ENV}` or env; never commit real tokens

## File map

- Create: `pyproject.toml`, `README.md`, `.gitignore`
- Create: `alertwatch/__init__.py`, `config.py`, `fetch.py`, `parse.py`, `store.py`, `diff.py`, `notify.py`, `runner.py`, `cli.py`
- Create: `configs/demo.yaml`
- Create: `demo_site/index.html`
- Create: `tests/fixtures/page_v1.html`, `tests/fixtures/page_v2.html`
- Create: `tests/test_config.py`, `tests/test_parse.py`, `tests/test_diff.py`, `tests/test_store.py`, `tests/test_notify.py`, `tests/test_runner.py`, `tests/test_cli.py`
- Create: `data/.gitkeep`

---

### Task 1: Package skeleton + config loader

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `alertwatch/__init__.py`, `alertwatch/config.py`
- Create: `configs/demo.yaml`, `data/.gitkeep`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `load_config(path: str | Path) -> WatchConfig`
- `WatchConfig` fields: `name: str`, `url: str`, `fields: dict[str, FieldSpec]`, `poll_interval_seconds: int = 60`, `request: RequestSpec`, `telegram: TelegramSpec`, `state_path: Path`, `log_path: Path`
- `FieldSpec`: `selector: str`, `attr: str | None = None`
- `RequestSpec`: `timeout: float = 15.0`, `user_agent: str`, `retries: int = 2`
- `TelegramSpec`: `bot_token: str`, `chat_id: str`, `dry_run: bool = True`
- `${VAR}` in token/chat_id resolved from environment when loading

- [ ] **Step 1: Write failing test** `tests/test_config.py` that loads `configs/demo.yaml` and asserts `name`, `url`, field selectors, `telegram.dry_run is True`

- [ ] **Step 2: Run test — expect FAIL** (`ModuleNotFoundError` or missing file)

- [ ] **Step 3: Implement** `pyproject.toml` (deps: httpx, beautifulsoup4, pydantic>=2, click, pyyaml; optional `dev=[pytest]`; script `alertwatch = alertwatch.cli:main`), `.gitignore` (venv, `__pycache__`, `*.egg-info`, `data/*.db`, `data/*.log` but keep `data/.gitkeep`), `alertwatch/config.py`, `configs/demo.yaml` pointing at `http://127.0.0.1:8765/` with fields `title` → `h1`, `price` → `.price`

- [ ] **Step 4: Create venv, `uv pip install -e ".[dev]"`, pytest green**

- [ ] **Step 5: Commit** `feat: package skeleton and YAML config loader`

---

### Task 2: Parse, store, diff

**Files:**
- Create: `alertwatch/parse.py`, `alertwatch/store.py`, `alertwatch/diff.py`
- Create: `tests/fixtures/page_v1.html`, `tests/fixtures/page_v2.html`
- Test: `tests/test_parse.py`, `tests/test_store.py`, `tests/test_diff.py`

**Interfaces:**
- Consumes: `WatchConfig`, `FieldSpec`
- Produces:
  - `parse_fields(html: str, fields: dict[str, FieldSpec]) -> dict[str, str]`
  - `SnapshotStore(path)` with `get(job: str) -> dict[str, str] | None`, `put(job: str, values: dict[str, str]) -> None`
  - `diff_values(old: dict[str, str] | None, new: dict[str, str]) -> list[Change]` where `Change` is a dataclass `field: str`, `old: str | None`, `new: str`
  - If `old is None`, return empty list (baseline; no alert)

- [ ] **Step 1: Write failing parse/diff/store tests** using fixtures (v1 title/price; v2 changed price)

- [ ] **Step 2: Implement parse/store/diff minimally**

- [ ] **Step 3: pytest those modules — all PASS**

- [ ] **Step 4: Commit** `feat: field parse, SQLite snapshots, and diff`

---

### Task 3: Fetch, notify, runner, CLI, demo site

**Files:**
- Create: `alertwatch/fetch.py`, `alertwatch/notify.py`, `alertwatch/runner.py`, `alertwatch/cli.py`
- Create: `demo_site/index.html`
- Test: `tests/test_notify.py`, `tests/test_runner.py`, `tests/test_cli.py`

**Interfaces:**
- Produces:
  - `fetch_url(url: str, request: RequestSpec) -> str`
  - `send_alert(telegram: TelegramSpec, text: str, *, force_dry_run: bool = False) -> None` — if dry_run or force: append/print `[dry-run] {text}`; else POST `https://api.telegram.org/bot{token}/sendMessage`
  - `run_once(config: WatchConfig, *, force_dry_run: bool = False) -> list[Change]` — full cycle; on first run returns `[]` after storing baseline
  - `run_watch(config, *, force_dry_run: bool = False) -> None` — loop sleep `poll_interval_seconds`
  - CLI: `alertwatch once -c ... [--dry-run]`, `alertwatch watch -c ... [--dry-run]`

- [ ] **Step 1: Write notify test** mocking httpx for Telegram; dry-run asserts no HTTP

- [ ] **Step 2: Write runner test** with respx/httpx mock or monkeypatch fetch+notify; first cycle no notify, second with changed HTML notifies

- [ ] **Step 3: Implement fetch, notify, runner, cli**

- [ ] **Step 4: Build `demo_site/index.html`** with `<h1>` and `<span class="price">`

- [ ] **Step 5: Manual dry-run E2E**

```bash
cd /workspace/alertwatch/demo_site && python -m http.server 8765 &
cd /workspace/alertwatch && alertwatch once -c configs/demo.yaml --dry-run
# edit demo price, run once again — expect dry-run change line
python -m pytest -v
```

- [ ] **Step 6: Commit** `feat: fetch, notify, runner, CLI, and demo site`

---

### Task 4: README + portfolio blurb

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write README** — install, serve demo, `once`/`watch`, `--dry-run`, env vars `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`, pytest, Upwork title/description from design spec

- [ ] **Step 2: Commit** `docs: README and portfolio copy`

---

## Spec coverage check

- Field-level YAML watch ✓ Tasks 1–2  
- SQLite snapshots + baseline no-alert ✓ Task 2  
- Telegram + dry-run ✓ Task 3  
- CLI once/watch + interval ✓ Task 3  
- Demo site ✓ Task 3  
- Offline pytest ✓ Tasks 1–3  
- README portfolio ✓ Task 4  
- No Playwright / no third-party scrape in demo ✓ Global constraints  
