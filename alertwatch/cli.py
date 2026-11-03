from __future__ import annotations

from pathlib import Path

import click

from alertwatch.config import load_config
from alertwatch.runner import run_once, run_watch


@click.group()
def main() -> None:
    """Watch configured page fields and alert on changes."""


@main.command("once")
@click.option(
    "-c",
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to YAML watch config.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Force dry-run alerts (no Telegram HTTP).",
)
def once_cmd(config_path: Path, dry_run: bool) -> None:
    """Run a single poll cycle."""
    config = load_config(config_path)
    run_once(config, force_dry_run=dry_run)


@main.command("watch")
@click.option(
    "-c",
    "--config",
    "config_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    help="Path to YAML watch config.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Force dry-run alerts (no Telegram HTTP).",
)
def watch_cmd(config_path: Path, dry_run: bool) -> None:
    """Poll repeatedly using poll_interval_seconds."""
    config = load_config(config_path)
    run_watch(config, force_dry_run=dry_run)


if __name__ == "__main__":
    main()
