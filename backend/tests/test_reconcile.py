from decimal import Decimal
from backend.app.reconcile import compare


def make_a(total="100.00", location="LOC-101",
           date="2026-03-01"):
    return {
        "REC-1": {
            "total": Decimal(total),
            "location": location,
            "date": date,
        }
    }


def make_b(value="100.00", ref="REC-1",
           entry_id="E1", location="LOC-101",
           date="2026-03-01"):
    return {
        "entry_id": entry_id,
        "ref": ref,
        "value": Decimal(value) if value is not None else None,
        "location": location,
        "date": date,
    }


def reasons(a, b):
    return [row["reason"] for row in compare(a, b)]


def test_missing_in_b():
    assert "MISSING_IN_B" in reasons(make_a(), [])


def test_orphan_in_b():
    assert "ORPHAN_IN_B" in reasons({}, [make_b()])


def test_duplicate_in_b():
    entries = [
        make_b(entry_id="E1"),
        make_b(entry_id="E2"),
    ]
    assert "DUPLICATE_IN_B" in reasons(make_a(), entries)


def test_value_mismatch():
    assert "VALUE_MISMATCH" in reasons(
        make_a(), [make_b(value="90.00")]
    )


def test_blank_value():
    assert "VALUE_MISMATCH" in reasons(
        make_a(), [make_b(value=None)]
    )


def test_valid_split():
    entries = [
        make_b(value="40.00", entry_id="E1"),
        make_b(value="60.00", entry_id="E2"),
    ]
    assert compare(make_a(), entries) == []


def test_location_mismatch():
    assert "LOCATION_MISMATCH" in reasons(
        make_a(),
        [make_b(location="LOC-201")]
    )


def test_date_mismatch():
    assert "DATE_MISMATCH" in reasons(
        make_a(),
        [make_b(date="2026-03-02")]
    )


def test_clean_record():
    assert compare(make_a(), [make_b()]) == []