from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Change:
    field: str
    old: str | None
    new: str


def diff_values(
    old: dict[str, str] | None,
    new: dict[str, str],
) -> list[Change]:
    if old is None:
        return []
    changes: list[Change] = []
    for field, new_value in new.items():
        old_value = old.get(field)
        if old_value != new_value:
            changes.append(Change(field=field, old=old_value, new=new_value))
    return changes
