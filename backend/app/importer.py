import csv
import re
from pathlib import Path
from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy import select

from .database import SessionLocal
from .models import Location, SystemARecord, SystemBEntry


DATA_DIR = Path(__file__).resolve().parents[1] / "data"

def normalize_ref(raw):
    """Convert inconsistent references to REC-1234 format."""
    match = re.search(r"\d+", raw or "")

    if not match:
        return None

    return f"REC-{match.group()}"


def parse_amount(raw):
    """Convert money text into Decimal, preserving blanks as None."""
    value = (raw or "").strip().replace(",", "")

    if not value:
        return None

    try:
        amount = Decimal(value)
        return amount if amount.is_finite() else None
    except InvalidOperation:
        return None


def parse_date(raw):
    """Parse an ISO date, returning None for invalid dates."""
    try:
        return date.fromisoformat((raw or "").strip())
    except ValueError:
        return None


def read_csv(filename):
    with open(DATA_DIR / filename, newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for row in reader:
            yield {
                key: value.strip() if value is not None else ""
                for key, value in row.items()
            }

def import_locations(session):
    count = 0

    for row in read_csv("locations.csv"):
        location = session.get(Location, row["location_id"])

        if location is None:
            location = Location(location_id=row["location_id"])
            session.add(location)

        location.org_id = row["org_id"]
        location.location_name = row["location_name"]
        count += 1

    session.flush()
    return count



def import_system_a(session):
    count = 0

    for row in read_csv("system_a.csv"):
        record = session.get(SystemARecord, row["record_id"])

        if record is None:
            record = SystemARecord(record_id=row["record_id"])
            session.add(record)

        record.location_id = row["location_id"]
        record.event_date = parse_date(row["event_date"])
        record.category_code = row["category_code"]
        record.actor_id = row["actor_id"] or None

        record.base_value = parse_amount(row["base_value"])
        record.adjustment = parse_amount(row["adjustment"])
        record.total_value = parse_amount(row["total_value"])
        record.state = row["state"]

        count += 1

    session.flush()
    return count

def import_system_b(session):
    count = 0
    blank_values = 0
    cleaned_refs = 0

    for row in read_csv("system_b.csv"):
        entry = session.get(SystemBEntry, row["entry_id"])

        if entry is None:
            entry = SystemBEntry(entry_id=row["entry_id"])
            session.add(entry)

        raw_ref = row["record_ref"]
        raw_value = row["value"]

        normalized = normalize_ref(raw_ref)
        parsed_value = parse_amount(raw_value)

        entry.record_ref_raw = raw_ref
        entry.record_ref = normalized
        entry.location_id = row["location_id"]
        entry.recorded_on = parse_date(row["recorded_on"])
        entry.value_raw = raw_value
        entry.value = parsed_value
        entry.label = row["label"] or None

        if parsed_value is None:
            blank_values += 1
            print(f"Warning: invalid/blank value in {row['entry_id']}")

        if normalized != raw_ref:
            cleaned_refs += 1

        count += 1

    session.flush()
    return count, blank_values, cleaned_refs

def import_all():
    with SessionLocal() as session:
        with session.begin():
            locations = import_locations(session)
            a_records = import_system_a(session)
            b_entries, blank_values, cleaned_refs = import_system_b(session)

        print("\nImport completed successfully")
        print(f"Locations: {locations} rows processed")
        print(f"System A: {a_records} rows processed")
        print(f"System B: {b_entries} rows processed")
        print(f"Blank/invalid B values: {blank_values}")
        print(f"References normalized: {cleaned_refs}")


if __name__ == "__main__":
    import_all()

