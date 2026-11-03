from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

from alertwatch.config import WatchConfig
from alertwatch.diff import Change, diff_values
from alertwatch.fetch import fetch_url
from alertwatch.notify import send_alert
from alertwatch.parse import parse_fields
from alertwatch.store import SnapshotStore


def _format_alert(config: WatchConfig, changes: list[Change]) -> str:
    lines = [f"AlertWatch: {config.name}", f"URL: {config.url}", "Changes:"]
    for change in changes:
        old = "(none)" if change.old is None else change.old
        lines.append(f"  - {change.field}: {old} → {change.new}")
    return "\n".join(lines)


def _append_log(path: Path, message: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"{stamp} {message}\n")


def run_once(config: WatchConfig, *, force_dry_run: bool = False) -> list[Change]:
    html = fetch_url(config.url, config.request)
    values = parse_fields(html, config.fields)
    store = SnapshotStore(config.state_path)
    previous = store.get(config.name)
    changes = diff_values(previous, values)

    if changes:
        text = _format_alert(config, changes)
        try:
            send_alert(config.telegram, text, force_dry_run=force_dry_run)
        except httpx.HTTPError as exc:
            _append_log(
                config.log_path,
                f"{config.name}: notify failed (soft): {exc}",
            )
            return changes
        store.put(config.name, values)
        _append_log(config.log_path, text.replace("\n", " | "))
    else:
        store.put(config.name, values)
        _append_log(
            config.log_path,
            f"{config.name}: baseline stored" if previous is None else f"{config.name}: no change",
        )
    return changes


def run_watch(config: WatchConfig, *, force_dry_run: bool = False) -> None:
    try:
        while True:
            try:
                run_once(config, force_dry_run=force_dry_run)
            except (httpx.HTTPError, OSError) as exc:
                _append_log(
                    config.log_path,
                    f"{config.name}: fetch failed (hard): {exc}",
                )
            time.sleep(config.poll_interval_seconds)
    except KeyboardInterrupt:
        _append_log(config.log_path, f"{config.name}: watch stopped (KeyboardInterrupt)")
        return
