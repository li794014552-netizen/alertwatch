from alertwatch.diff import Change, diff_values


def test_diff_values_baseline_when_old_is_none():
    new = {"title": "Demo Widget", "price": "$19.99"}
    assert diff_values(None, new) == []


def test_diff_values_no_change_when_equal():
    values = {"title": "Demo Widget", "price": "$19.99"}
    assert diff_values(values, values.copy()) == []


def test_diff_values_reports_changed_price():
    old = {"title": "Demo Widget", "price": "$19.99"}
    new = {"title": "Demo Widget", "price": "$24.99"}
    changes = diff_values(old, new)
    assert changes == [Change(field="price", old="$19.99", new="$24.99")]


def test_diff_values_reports_new_field_as_change():
    old = {"title": "Demo Widget"}
    new = {"title": "Demo Widget", "price": "$19.99"}
    changes = diff_values(old, new)
    assert changes == [Change(field="price", old=None, new="$19.99")]
