from alertwatch.store import SnapshotStore


def test_snapshot_store_get_missing_returns_none(tmp_path):
    store = SnapshotStore(tmp_path / "state.db")
    assert store.get("demo") is None


def test_snapshot_store_put_then_get_roundtrip(tmp_path):
    store = SnapshotStore(tmp_path / "state.db")
    values = {"title": "Demo Widget", "price": "$19.99"}
    store.put("demo", values)
    assert store.get("demo") == values


def test_snapshot_store_put_overwrites_previous(tmp_path):
    store = SnapshotStore(tmp_path / "state.db")
    store.put("demo", {"price": "$19.99"})
    store.put("demo", {"price": "$24.99"})
    assert store.get("demo") == {"price": "$24.99"}
