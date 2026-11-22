from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Location, SystemARecord, SystemBEntry
from ..reconcile import compare


router = APIRouter(prefix="/api/disagreements", tags=["disagreements"])


def get_db():
    with SessionLocal() as session:
        yield session


def decimal_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value, "f")


@router.get("/")
def list_disagreements(
    org: str = Query(..., description="Organization ID"),
    reason: str | None = Query(None),
    sort: Literal["value", "-value"] | None = Query(None),
    db: Session = Depends(get_db),
) -> list[dict]:
    locations = db.execute(select(Location)).scalars().all()
    location_org = {
        location.location_id: location.org_id
        for location in locations
    }
    valid_orgs = set(location_org.values())

    if org not in valid_orgs:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid organization: {org}",
        )

    a_records = db.execute(select(SystemARecord)).scalars().all()
    b_entries = db.execute(select(SystemBEntry)).scalars().all()

    a_rows = {
        record.record_id: {
            "total": record.total_value,
            "location": record.location_id,
            "date": record.event_date,
        }
        for record in a_records
    }

    b_rows = [
        {
            "entry_id": entry.entry_id,
            "ref": entry.record_ref,
            "value": entry.value,
            "location": entry.location_id,
            "date": entry.recorded_on,
        }
        for entry in b_entries
    ]

    disagreements = compare(a_rows, b_rows)
    response = []

    for disagreement in disagreements:
        disagreement_reason = disagreement["reason"]
        if reason is not None and disagreement_reason != reason:
            continue

        a_location = disagreement["a_location"]
        b_location = disagreement["b_location"]

        if disagreement_reason == "MISSING_IN_B":
            owner_org = location_org.get(a_location)
            record_id = disagreement["record_id"]
            entry_id = None
            location = a_location
        elif disagreement_reason == "ORPHAN_IN_B":
            owner_org = location_org.get(b_location)
            record_id = None
            entry_id = disagreement["entry_id"]
            location = b_location
        else:
            owner_org = location_org.get(a_location)
            record_id = disagreement["record_id"]

            matching_entries = [
                entry for entry in b_rows
                if entry["ref"] == record_id
            ]
            if len(matching_entries) == 1:
                candidate_entry = matching_entries[0]
                entry_id = candidate_entry["entry_id"]
                if location_org.get(candidate_entry["location"]) != owner_org:
                    entry_id = None
            else:
                entry_id = None
            location = a_location

        if owner_org != org:
            continue

        has_cross_org_location = (
            disagreement_reason in {
                "VALUE_MISMATCH",
                "LOCATION_MISMATCH",
                "DATE_MISMATCH",
                "DUPLICATE_IN_B",
            }
            and any(
                entry["ref"] == disagreement["record_id"]
                and location_org.get(entry["location"]) != owner_org
                for entry in b_rows
            )
        )

        if has_cross_org_location:
            entry_id = None
            a_value = disagreement["a_value"]
            b_value = None
            difference = None
            location = a_location
        else:
            a_value = disagreement["a_value"]
            b_value = disagreement["b_value"]
            difference = disagreement["difference"]

        response.append({
            "reason": disagreement_reason,
            "record_id": record_id,
            "entry_id": entry_id,
            "location": location,
            "a_value": decimal_string(a_value),
            "b_value": decimal_string(b_value),
            "difference": decimal_string(difference),
        })

    if sort is not None:
        def monetary_sort_key(item: dict) -> tuple[int, Decimal]:
            raw_value = item["a_value"]
            if raw_value is None:
                raw_value = item["b_value"]

            if raw_value is None:
                return (1, Decimal("0"))
            return (0, Decimal(raw_value))

        if sort == "-value":
            with_values = [item for item in response if monetary_sort_key(item)[0] == 0]
            without_values = [item for item in response if monetary_sort_key(item)[0] == 1]
            with_values.sort(key=monetary_sort_key, reverse=True)
            response = with_values + without_values
        else:
            response.sort(key=monetary_sort_key)

    return response
