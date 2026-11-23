from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.main import app
from backend.app.models import Location, SystemARecord, SystemBEntry
from backend.app.routes.disagreements import get_db


@pytest.fixture()
def db_session(tmp_path):
    database_path = tmp_path / "tenant-tests.sqlite"
    engine = create_engine(
        f"sqlite:///{database_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    session = SessionLocal()
    seed_database(session)
    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.rollback()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def seed_database(db):
    db.add_all([
        Location(location_id="LOC-A-101", org_id="ORG-A", location_name="A One"),
        Location(location_id="LOC-A-102", org_id="ORG-A", location_name="A Two"),
        Location(location_id="LOC-B-201", org_id="ORG-B", location_name="B One"),
        Location(location_id="LOC-B-202", org_id="ORG-B", location_name="B Two"),
    ])

    db.flush()

    db.add_all([
        SystemARecord(
            record_id="REC-A-VALUE-100",
            location_id="LOC-A-101",
            event_date=date(2026, 1, 1),
            category_code="SERVICE",
            actor_id="ACT-A-1",
            base_value=Decimal("90.00"),
            adjustment=Decimal("10.00"),
            total_value=Decimal("100.00"),
            state="OPEN",
        ),
        SystemARecord(
            record_id="REC-A-VALUE-500",
            location_id="LOC-A-102",
            event_date=date(2026, 1, 2),
            category_code="SERVICE",
            actor_id="ACT-A-2",
            base_value=Decimal("500.00"),
            adjustment=Decimal("0.00"),
            total_value=Decimal("500.00"),
            state="OPEN",
        ),
        SystemARecord(
            record_id="REC-A-BLANK",
            location_id="LOC-A-101",
            event_date=date(2026, 1, 3),
            category_code="SERVICE",
            actor_id="ACT-A-3",
            base_value=Decimal("200.00"),
            adjustment=Decimal("0.00"),
            total_value=Decimal("200.00"),
            state="OPEN",
        ),
        SystemARecord(
            record_id="REC-A-CROSS",
            location_id="LOC-A-101",
            event_date=date(2026, 1, 4),
            category_code="SERVICE",
            actor_id="ACT-A-4",
            base_value=Decimal("300.00"),
            adjustment=Decimal("0.00"),
            total_value=Decimal("300.00"),
            state="OPEN",
        ),
        SystemARecord(
            record_id="REC-A-SPLIT",
            location_id="LOC-A-102",
            event_date=date(2026, 1, 5),
            category_code="SERVICE",
            actor_id="ACT-A-5",
            base_value=Decimal("100.00"),
            adjustment=Decimal("0.00"),
            total_value=Decimal("100.00"),
            state="OPEN",
        ),
        SystemARecord(
            record_id="REC-B-MISSING",
            location_id="LOC-B-202",
            event_date=date(2026, 1, 6),
            category_code="SERVICE",
            actor_id="ACT-B-1",
            base_value=Decimal("700.00"),
            adjustment=Decimal("0.00"),
            total_value=Decimal("700.00"),
            state="OPEN",
        ),
    ])

    db.flush()

    db.add_all([
        SystemBEntry(
            entry_id="ENT-A-VALUE-100",
            record_ref_raw="REC-A-VALUE-100",
            record_ref="REC-A-VALUE-100",
            location_id="LOC-A-101",
            recorded_on=date(2026, 1, 1),
            value_raw="90.00",
            value=Decimal("90.00"),
            label="Mismatch",
        ),
        SystemBEntry(
            entry_id="ENT-A-VALUE-500",
            record_ref_raw="REC-A-VALUE-500",
            record_ref="REC-A-VALUE-500",
            location_id="LOC-A-102",
            recorded_on=date(2026, 1, 2),
            value_raw="450.00",
            value=Decimal("450.00"),
            label="Mismatch",
        ),
        SystemBEntry(
            entry_id="ENT-A-BLANK",
            record_ref_raw="REC-A-BLANK",
            record_ref="REC-A-BLANK",
            location_id="LOC-A-101",
            recorded_on=date(2026, 1, 3),
            value_raw="",
            value=None,
            label="Unknown",
        ),
        SystemBEntry(
            entry_id="ENT-B-PRIVATE-CROSS",
            record_ref_raw="REC-A-CROSS",
            record_ref="REC-A-CROSS",
            location_id="LOC-B-201",
            recorded_on=date(2026, 1, 4),
            value_raw="250.00",
            value=Decimal("250.00"),
            label="Private B entry",
        ),
        SystemBEntry(
            entry_id="ENT-A-SPLIT-1",
            record_ref_raw="REC-A-SPLIT",
            record_ref="REC-A-SPLIT",
            location_id="LOC-A-102",
            recorded_on=date(2026, 1, 5),
            value_raw="40.00",
            value=Decimal("40.00"),
            label="Entry part 1 of 2",
        ),
        SystemBEntry(
            entry_id="ENT-A-SPLIT-2",
            record_ref_raw="REC-A-SPLIT",
            record_ref="REC-A-SPLIT",
            location_id="LOC-A-102",
            recorded_on=date(2026, 1, 5),
            value_raw="60.00",
            value=Decimal("60.00"),
            label="Entry part 2 of 2",
        ),
        SystemBEntry(
            entry_id="ENT-B-ORPHAN",
            record_ref_raw="REC-NOT-IN-A",
            record_ref="REC-NOT-IN-A",
            location_id="LOC-B-201",
            recorded_on=date(2026, 1, 7),
            value_raw="800.00",
            value=Decimal("800.00"),
            label="B orphan",
        ),
    ])


def test_org_a_only_receives_a_owned_disagreements(client):
    response = client.get("/api/disagreements/?org=ORG-A")

    assert response.status_code == 200
    rows = response.json()
    assert isinstance(rows, list)
    assert rows
    assert all(row["location"] in {"LOC-A-101", "LOC-A-102"} for row in rows)
    assert all(row["location"] not in {"LOC-B-201", "LOC-B-202"} for row in rows)


def test_org_b_only_receives_b_owned_disagreements(client):
    response = client.get("/api/disagreements/?org=ORG-B")

    assert response.status_code == 200
    rows = response.json()
    assert isinstance(rows, list)
    assert rows
    assert all(row["location"] in {"LOC-B-201", "LOC-B-202"} for row in rows)
    assert all(row["location"] not in {"LOC-A-101", "LOC-A-102"} for row in rows)


def test_missing_org_is_rejected(client):
    response = client.get("/api/disagreements/")

    assert response.status_code == 422
    assert "org" in response.text


def test_unknown_org_is_rejected(client):
    response = client.get("/api/disagreements/?org=ORG-UNKNOWN")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid organization: ORG-UNKNOWN"


def test_cross_org_mismatch_is_redacted_for_org_a(client):
    response = client.get("/api/disagreements/?org=ORG-A")

    assert response.status_code == 200
    cross_rows = [row for row in response.json() if row["record_id"] == "REC-A-CROSS"]
    assert cross_rows

    serialized = response.text
    assert "LOC-B-201" not in serialized
    assert "ENT-B-PRIVATE-CROSS" not in serialized
    assert "250.00" not in serialized

    for row in cross_rows:
        assert row["location"] == "LOC-A-101"
        assert row["entry_id"] is None
        assert row["b_value"] is None
        assert row["difference"] is None


def test_org_b_cannot_retrieve_org_a_owned_record(client):
    response = client.get("/api/disagreements/?org=ORG-B")

    assert response.status_code == 200
    assert all(row["record_id"] != "REC-A-CROSS" for row in response.json())


def test_value_mismatch_reason_filter(client):
    response = client.get(
        "/api/disagreements/?org=ORG-A&reason=VALUE_MISMATCH"
    )

    assert response.status_code == 200
    rows = response.json()
    assert rows
    assert all(row["reason"] == "VALUE_MISMATCH" for row in rows)


def test_sort_minus_value_is_descending(client):
    response = client.get(
        "/api/disagreements/?org=ORG-A&sort=-value"
    )

    assert response.status_code == 200
    rows = response.json()
    values = [
        Decimal(row["a_value"])
        for row in rows
        if row["a_value"] is not None
    ]

    assert values == sorted(values, reverse=True)


def test_missing_monetary_value_is_null(client):
    response = client.get("/api/disagreements/?org=ORG-A")

    assert response.status_code == 200
    blank_rows = [row for row in response.json() if row["record_id"] == "REC-A-BLANK"]
    assert blank_rows
    assert all(row["b_value"] is None for row in blank_rows)


def test_valid_split_is_not_reported_as_duplicate(client):
    response = client.get("/api/disagreements/?org=ORG-A")

    assert response.status_code == 200
    split_rows = [row for row in response.json() if row["record_id"] == "REC-A-SPLIT"]
    assert split_rows == []
