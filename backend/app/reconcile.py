# backend/app/reconcile.py

from collections import defaultdict
from decimal import Decimal


def compare(a_rows, b_rows):
    disagreements = []
    b_by_ref = defaultdict(list)

    # Group System B entries by their normalized reference.
    for entry in b_rows:
        b_by_ref[entry["ref"]].append(entry)

    # Find orphan entries in B.
    for ref, entries in b_by_ref.items():
        if ref not in a_rows:
            for entry in entries:
                disagreements.append({
                    "reason": "ORPHAN_IN_B",
                    "record_id": ref,
                    "entry_id": entry["entry_id"],
                    "a_location": None,
                    "b_location": entry["location"],
                    "a_value": None,
                    "b_value": entry["value"],
                    "difference": None,
                })

    # Compare every A record with its B entries.
    for record_id, a in a_rows.items():
        entries = b_by_ref.get(record_id, [])
        a_total = a["total"]

        if not entries:
            disagreements.append({
                "reason": "MISSING_IN_B",
                "record_id": record_id,
                "a_location": a["location"],
                "b_location": None,
                "a_value": a_total,
                "b_value": None,
                "difference": None,
            })
            continue

        values = [entry["value"] for entry in entries]

        # Blank B values are unknown, not zero.
        if any(value is None for value in values):
            disagreements.append({
                "reason": "VALUE_MISMATCH",
                "record_id": record_id,
                "a_location": a["location"],
                "b_location": None,
                "a_value": a_total,
                "b_value": None,
                "difference": None,
            })
            continue

        b_total = sum(values, Decimal("0"))

        # Multiple B entries may represent a valid split.
        if len(entries) > 1:
            if b_total != a_total:
                disagreements.append({
                    "reason": "DUPLICATE_IN_B",
                    "record_id": record_id,
                    "a_location": a["location"],
                    "b_location": None,
                    "a_value": a_total,
                    "b_value": b_total,
                    "difference": b_total - a_total,
                })
        elif b_total != a_total:
            disagreements.append({
                "reason": "VALUE_MISMATCH",
                "record_id": record_id,
                "a_location": a["location"],
                "b_location": entries[0]["location"],
                "a_value": a_total,
                "b_value": b_total,
                "difference": b_total - a_total,
            })

        # Check dates and locations for each B entry.
        for entry in entries:
            if entry["location"] != a["location"]:
                disagreements.append({
                    "reason": "LOCATION_MISMATCH",
                    "record_id": record_id,
                    "a_location": a["location"],
                    "b_location": entry["location"],
                    "a_value": a_total,
                    "b_value": entry["value"],
                    "difference": None,
                })

            if entry["date"] != a["date"]:
                disagreements.append({
                    "reason": "DATE_MISMATCH",
                    "record_id": record_id,
                    "a_location": a["location"],
                    "b_location": entry["location"],
                    "a_value": a_total,
                    "b_value": entry["value"],
                    "difference": None,
                })

    return disagreements