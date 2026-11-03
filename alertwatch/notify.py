from __future__ import annotations

import httpx

from alertwatch.config import TelegramSpec


def send_alert(
    telegram: TelegramSpec,
    text: str,
    *,
    force_dry_run: bool = False,
) -> None:
    """Send Telegram message, or print a dry-run line when configured/forced."""
    if telegram.dry_run or force_dry_run:
        print(f"[dry-run] {text}")
        return

    url = f"https://api.telegram.org/bot{telegram.bot_token}/sendMessage"
    response = httpx.post(
        url,
        json={"chat_id": telegram.chat_id, "text": text},
        timeout=15.0,
    )
    response.raise_for_status()
