from __future__ import annotations

from alertwatch.config import TelegramSpec
from alertwatch.notify import send_alert


def test_send_alert_dry_run_prints_and_skips_http(monkeypatch, capsys):
    calls: list[object] = []

    def boom(*args, **kwargs):  # pragma: no cover - must not be called
        calls.append((args, kwargs))
        raise AssertionError("httpx must not be called in dry-run")

    monkeypatch.setattr("httpx.post", boom)
    monkeypatch.setattr("httpx.Client", boom)

    telegram = TelegramSpec(bot_token="tok", chat_id="123", dry_run=True)
    send_alert(telegram, "price changed")

    captured = capsys.readouterr()
    assert "[dry-run] price changed" in captured.out
    assert calls == []


def test_send_alert_force_dry_run_skips_http_even_when_config_live(monkeypatch, capsys):
    calls: list[object] = []

    def boom(*args, **kwargs):  # pragma: no cover
        calls.append((args, kwargs))
        raise AssertionError("httpx must not be called when force_dry_run")

    monkeypatch.setattr("httpx.post", boom)

    telegram = TelegramSpec(bot_token="tok", chat_id="123", dry_run=False)
    send_alert(telegram, "title changed", force_dry_run=True)

    captured = capsys.readouterr()
    assert "[dry-run] title changed" in captured.out
    assert calls == []


def test_send_alert_posts_telegram_send_message(monkeypatch):
    recorded: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

    def fake_post(url, *, data=None, json=None, timeout=None, **kwargs):
        recorded["url"] = url
        recorded["data"] = data
        recorded["json"] = json
        recorded["timeout"] = timeout
        recorded["kwargs"] = kwargs
        return FakeResponse()

    monkeypatch.setattr("httpx.post", fake_post)

    telegram = TelegramSpec(bot_token="SECRET", chat_id="42", dry_run=False)
    send_alert(telegram, "hello alert")

    assert recorded["url"] == "https://api.telegram.org/botSECRET/sendMessage"
    payload = recorded["json"] if recorded["json"] is not None else recorded["data"]
    assert payload["chat_id"] == "42"
    assert payload["text"] == "hello alert"
