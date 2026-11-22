from decimal import Decimal

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_missing_org_is_rejected():
    response = client.get("/api/disagreements/")
    assert response.status_code == 422


def test_invalid_org_is_rejected():
    response = client.get("/api/disagreements/?org=NOT-AN-ORG")
    assert response.status_code == 400


def test_org_results_are_isolated():
    org_a = client.get("/api/disagreements/?org=ORG-A").json()
    org_b = client.get("/api/disagreements/?org=ORG-B").json()

    assert isinstance(org_a, list)
    assert isinstance(org_b, list)

    for item in org_a:
        assert item["location"] is not None
        assert item["location"].startswith("LOC-1")

    for item in org_b:
        assert item["location"] is not None
        assert item["location"].startswith("LOC-2")


def test_reason_filter_and_descending_value_sort():
    mismatches = client.get(
        "/api/disagreements/?org=ORG-A"
        "&reason=VALUE_MISMATCH&sort=-value"
    )
    assert mismatches.status_code == 200
    rows = mismatches.json()

    assert all(row["reason"] == "VALUE_MISMATCH" for row in rows)
    values = [
        row["a_value"] for row in rows
        if row["a_value"] is not None
    ]
    assert values == sorted(
        values,
        key=lambda value: Decimal(value),
        reverse=True,
    )
