from pathlib import Path

from alertwatch.config import load_config

REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_CONFIG = REPO_ROOT / "configs" / "demo.yaml"


def test_load_demo_config():
    config = load_config(DEMO_CONFIG)

    assert config.name == "demo"
    assert config.url == "http://127.0.0.1:8765/"
    assert config.fields["title"].selector == "h1"
    assert config.fields["price"].selector == ".price"
    assert config.telegram.dry_run is True
