from __future__ import annotations

from bs4 import BeautifulSoup

from alertwatch.config import FieldSpec


def parse_fields(html: str, fields: dict[str, FieldSpec]) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    values: dict[str, str] = {}
    for name, spec in fields.items():
        element = soup.select_one(spec.selector)
        if element is None:
            values[name] = ""
            continue
        if spec.attr is not None:
            raw = element.get(spec.attr, "")
            values[name] = "" if raw is None else str(raw).strip()
        else:
            values[name] = element.get_text(strip=True)
    return values
