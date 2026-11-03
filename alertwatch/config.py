from __future__ import annotations

import os
import re
from pathlib import Path

import yaml
from pydantic import BaseModel, field_validator

_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _resolve_env(value: str) -> str:
    def repl(match: re.Match[str]) -> str:
        return os.environ.get(match.group(1), "")

    return _ENV_PATTERN.sub(repl, value)


class FieldSpec(BaseModel):
    selector: str
    attr: str | None = None


class RequestSpec(BaseModel):
    timeout: float = 15.0
    user_agent: str
    retries: int = 2


class TelegramSpec(BaseModel):
    bot_token: str
    chat_id: str
    dry_run: bool = True

    @field_validator("bot_token", "chat_id", mode="before")
    @classmethod
    def resolve_env_vars(cls, value: object) -> object:
        if isinstance(value, str):
            return _resolve_env(value)
        return value


class WatchConfig(BaseModel):
    name: str
    url: str
    fields: dict[str, FieldSpec]
    poll_interval_seconds: int = 60
    request: RequestSpec
    telegram: TelegramSpec
    state_path: Path
    log_path: Path


def load_config(path: str | Path) -> WatchConfig:
    raw = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(raw) or {}
    return WatchConfig.model_validate(data)
