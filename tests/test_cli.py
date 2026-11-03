from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from alertwatch.cli import main
from alertwatch.diff import Change

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_CONFIG = REPO_ROOT / "configs" / "demo.yaml"


def test_cli_once_dry_run_invokes_run_once(monkeypatch):
    calls: list[dict] = []

    def fake_run_once(config, *, force_dry_run=False):
        calls.append({"name": config.name, "force_dry_run": force_dry_run})
        return []

    monkeypatch.setattr("alertwatch.cli.run_once", fake_run_once)

    runner = CliRunner()
    result = runner.invoke(main, ["once", "-c", str(DEMO_CONFIG), "--dry-run"])

    assert result.exit_code == 0, result.output
    assert calls == [{"name": "demo", "force_dry_run": True}]


def test_cli_watch_dry_run_invokes_run_watch(monkeypatch):
    calls: list[dict] = []

    def fake_run_watch(config, *, force_dry_run=False):
        calls.append({"name": config.name, "force_dry_run": force_dry_run})

    monkeypatch.setattr("alertwatch.cli.run_watch", fake_run_watch)

    runner = CliRunner()
    result = runner.invoke(main, ["watch", "-c", str(DEMO_CONFIG), "--dry-run"])

    assert result.exit_code == 0, result.output
    assert calls == [{"name": "demo", "force_dry_run": True}]


def test_cli_once_without_dry_run_flag_passes_false(monkeypatch):
    calls: list[bool] = []

    def fake_run_once(config, *, force_dry_run=False):
        calls.append(force_dry_run)
        return [Change(field="price", old="$1", new="$2")]

    monkeypatch.setattr("alertwatch.cli.run_once", fake_run_once)

    runner = CliRunner()
    result = runner.invoke(main, ["once", "-c", str(DEMO_CONFIG)])

    assert result.exit_code == 0, result.output
    assert calls == [False]


def test_cli_once_soft_notify_failure_exits_zero(tmp_path, monkeypatch):
    """Live Telegram HTTP errors are soft: once still exits 0 after logging."""
    import httpx
    from alertwatch.config import (
        FieldSpec,
        RequestSpec,
        TelegramSpec,
        WatchConfig,
        load_config,
    )
    html_v1 = (REPO_ROOT / "tests" / "fixtures" / "page_v1.html").read_text(encoding="utf-8")
    html_v2 = (REPO_ROOT / "tests" / "fixtures" / "page_v2.html").read_text(encoding="utf-8")
    pages = iter([html_v1, html_v2])

    cfg = WatchConfig(
        name="demo",
        url="http://example.test/",
        fields={
            "title": FieldSpec(selector="h1"),
            "price": FieldSpec(selector=".price"),
        },
        poll_interval_seconds=1,
        request=RequestSpec(timeout=5.0, user_agent="AlertWatchTest/0.1", retries=0),
        telegram=TelegramSpec(bot_token="tok", chat_id="1", dry_run=False),
        state_path=tmp_path / "state.db",
        log_path=tmp_path / "demo.log",
    )

    monkeypatch.setattr("alertwatch.cli.load_config", lambda path: cfg)
    monkeypatch.setattr("alertwatch.runner.fetch_url", lambda url, request: next(pages))

    def failing_send(telegram, text, *, force_dry_run=False):
        raise httpx.HTTPError("telegram down")

    monkeypatch.setattr("alertwatch.runner.send_alert", failing_send)

    runner = CliRunner()
    # baseline
    baseline = runner.invoke(main, ["once", "-c", str(DEMO_CONFIG)])
    assert baseline.exit_code == 0, baseline.output

    # change + soft notify failure
    result = runner.invoke(main, ["once", "-c", str(DEMO_CONFIG)])
    assert result.exit_code == 0, result.output
