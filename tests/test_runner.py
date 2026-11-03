from __future__ import annotations

from pathlib import Path

from alertwatch.config import (
    FieldSpec,
    RequestSpec,
    TelegramSpec,
    WatchConfig,
)
from alertwatch.diff import Change
from alertwatch.runner import run_once, run_watch

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _config(tmp_path: Path) -> WatchConfig:
    return WatchConfig(
        name="demo",
        url="http://example.test/",
        fields={
            "title": FieldSpec(selector="h1"),
            "price": FieldSpec(selector=".price"),
        },
        poll_interval_seconds=1,
        request=RequestSpec(timeout=5.0, user_agent="AlertWatchTest/0.1", retries=0),
        telegram=TelegramSpec(bot_token="tok", chat_id="1", dry_run=True),
        state_path=tmp_path / "state.db",
        log_path=tmp_path / "demo.log",
    )


def test_run_once_first_cycle_baseline_no_notify(tmp_path, monkeypatch):
    html_v1 = (FIXTURES / "page_v1.html").read_text(encoding="utf-8")
    alerts: list[str] = []

    monkeypatch.setattr("alertwatch.runner.fetch_url", lambda url, request: html_v1)
    monkeypatch.setattr(
        "alertwatch.runner.send_alert",
        lambda telegram, text, *, force_dry_run=False: alerts.append(text),
    )

    changes = run_once(_config(tmp_path), force_dry_run=True)

    assert changes == []
    assert alerts == []


def test_run_once_second_cycle_notifies_on_price_change(tmp_path, monkeypatch):
    html_v1 = (FIXTURES / "page_v1.html").read_text(encoding="utf-8")
    html_v2 = (FIXTURES / "page_v2.html").read_text(encoding="utf-8")
    pages = iter([html_v1, html_v2])
    alerts: list[str] = []

    monkeypatch.setattr(
        "alertwatch.runner.fetch_url",
        lambda url, request: next(pages),
    )
    monkeypatch.setattr(
        "alertwatch.runner.send_alert",
        lambda telegram, text, *, force_dry_run=False: alerts.append(text),
    )

    config = _config(tmp_path)
    first = run_once(config, force_dry_run=True)
    second = run_once(config, force_dry_run=True)

    assert first == []
    assert second == [Change(field="price", old="$19.99", new="$24.99")]
    assert len(alerts) == 1
    assert "price" in alerts[0]
    assert "$19.99" in alerts[0]
    assert "$24.99" in alerts[0]
    assert "demo" in alerts[0]
    assert "http://example.test/" in alerts[0]


def test_run_once_notifies_before_snapshot_put(tmp_path, monkeypatch):
    html_v1 = (FIXTURES / "page_v1.html").read_text(encoding="utf-8")
    html_v2 = (FIXTURES / "page_v2.html").read_text(encoding="utf-8")
    pages = iter([html_v1, html_v2])
    order: list[str] = []

    monkeypatch.setattr(
        "alertwatch.runner.fetch_url",
        lambda url, request: next(pages),
    )

    def tracking_send(telegram, text, *, force_dry_run=False):
        order.append("notify")

    monkeypatch.setattr("alertwatch.runner.send_alert", tracking_send)

    from alertwatch.store import SnapshotStore

    original_put = SnapshotStore.put

    def tracking_put(self, job, values):
        order.append("put")
        return original_put(self, job, values)

    monkeypatch.setattr(SnapshotStore, "put", tracking_put)

    config = _config(tmp_path)
    assert run_once(config, force_dry_run=True) == []
    # baseline put only
    assert order == ["put"]
    order.clear()

    second = run_once(config, force_dry_run=True)
    assert second == [Change(field="price", old="$19.99", new="$24.99")]
    assert order == ["notify", "put"]


def test_run_once_soft_notify_failure_logs_and_skips_snapshot(tmp_path, monkeypatch):
    import httpx

    html_v1 = (FIXTURES / "page_v1.html").read_text(encoding="utf-8")
    html_v2 = (FIXTURES / "page_v2.html").read_text(encoding="utf-8")
    pages = iter([html_v1, html_v2])

    monkeypatch.setattr(
        "alertwatch.runner.fetch_url",
        lambda url, request: next(pages),
    )

    def failing_send(telegram, text, *, force_dry_run=False):
        raise httpx.HTTPStatusError(
            "bad gateway",
            request=httpx.Request("POST", "https://api.telegram.org"),
            response=httpx.Response(502),
        )

    monkeypatch.setattr("alertwatch.runner.send_alert", failing_send)

    config = _config(tmp_path)
    # baseline
    assert run_once(config, force_dry_run=False) == []

    from alertwatch.store import SnapshotStore

    store = SnapshotStore(config.state_path)
    before = store.get(config.name)
    assert before == {"title": "Demo Widget", "price": "$19.99"}

    # change cycle: soft failure must not raise, must not advance snapshot
    changes = run_once(config, force_dry_run=False)
    assert changes == [Change(field="price", old="$19.99", new="$24.99")]
    assert store.get(config.name) == before

    log_text = config.log_path.read_text(encoding="utf-8")
    assert "notify" in log_text.lower() or "fail" in log_text.lower() or "error" in log_text.lower() or "502" in log_text


def test_run_watch_survives_hard_fetch_failure_then_continues(tmp_path, monkeypatch):
    import httpx

    html_v1 = (FIXTURES / "page_v1.html").read_text(encoding="utf-8")
    call_count = {"n": 0}
    sleep_calls: list[float] = []

    def flaky_fetch(url, request):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise httpx.ConnectError("connection refused")
        return html_v1

    monkeypatch.setattr("alertwatch.runner.fetch_url", flaky_fetch)
    monkeypatch.setattr(
        "alertwatch.runner.send_alert",
        lambda telegram, text, *, force_dry_run=False: None,
    )

    def fake_sleep(seconds):
        sleep_calls.append(seconds)
        if call_count["n"] >= 2:
            raise KeyboardInterrupt()

    monkeypatch.setattr("alertwatch.runner.time.sleep", fake_sleep)

    config = _config(tmp_path)
    run_watch(config, force_dry_run=True)

    assert call_count["n"] >= 2
    assert len(sleep_calls) >= 2
    log_text = config.log_path.read_text(encoding="utf-8")
    assert "fetch failed" in log_text.lower() or "hard" in log_text.lower()
    assert "baseline" in log_text.lower() or "no change" in log_text.lower() or "stored" in log_text.lower()
