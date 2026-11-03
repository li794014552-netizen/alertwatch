from pathlib import Path

from alertwatch.config import FieldSpec
from alertwatch.parse import parse_fields

FIXTURES = Path(__file__).resolve().parent / "fixtures"

FIELDS = {
    "title": FieldSpec(selector="h1"),
    "price": FieldSpec(selector=".price"),
}


def test_parse_fields_extracts_title_and_price_from_v1():
    html = (FIXTURES / "page_v1.html").read_text(encoding="utf-8")
    values = parse_fields(html, FIELDS)
    assert values == {"title": "Demo Widget", "price": "$19.99"}


def test_parse_fields_sees_changed_price_in_v2():
    html = (FIXTURES / "page_v2.html").read_text(encoding="utf-8")
    values = parse_fields(html, FIELDS)
    assert values["title"] == "Demo Widget"
    assert values["price"] == "$24.99"


def test_parse_fields_reads_attribute_when_attr_set():
    html = (FIXTURES / "page_v1.html").read_text(encoding="utf-8")
    fields = {"buy_href": FieldSpec(selector="#buy", attr="href")}
    values = parse_fields(html, fields)
    assert values == {"buy_href": "/buy"}
