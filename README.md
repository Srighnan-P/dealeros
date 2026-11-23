# DealerOS — Full-Stack Assessment

## 1. Project Overview

DealerOS is a full-stack reconciliation application that compares business records from System A and System B and identifies disagreements.

The application imports CSV data into SQLite, compares matching records, and displays disagreements in a simple dashboard.

The application supports two organizations, ORG-A and ORG-B. Locations are mapped to organizations using `locations.csv`, and the API filters reconciliation results based on organization ownership.

## 2. Technology Stack

| Layer | Technology |
|---|---|
| Backend | Python, FastAPI |
| Database | SQLite |
| ORM | SQLAlchemy |
| Frontend | Next.js, React, TypeScript |
| Testing | pytest |

### Why I Chose FastAPI Instead of Django

The assessment recommends Django with React or Next.js but also allows alternative technology stacks.

I chose **FastAPI instead of Django because I am more familiar with FastAPI and wanted to focus on implementing the reconciliation logic correctly within the given time**.

FastAPI provides a straightforward way to build REST APIs, supports request validation, and integrates well with SQLAlchemy.

I used Next.js for the frontend because I am familiar with React and wanted to build a simple dashboard for displaying reconciliation results.

SQLite was chosen because it is lightweight, easy to set up, and suitable for this assessment.

## 3. Project Structure

```text
dealeros/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── importer.py
│   │   ├── reconcile.py
│   │   └── routes/
│   │       └── disagreements.py
│   ├── data/
│   │   ├── locations.csv
│   │   ├── system_a.csv
│   │   └── system_b.csv
│   ├── tests/
│   │   ├── test_importer.py
│   │   ├── test_reconcile.py
│   │   └── test_tenant.py
│   └── requirements.txt
├── frontend/
│   └── app/
│       └── page.tsx
├── DATA_NOTES.md
├── DECISIONS.md
└── README.md
```

## 4. Setup and Installation

### Requirements

- Python 3.10 or newer
- Node.js and npm
- Git

### Backend Setup

Clone the repository and open the project directory.

```bash
git clone <repository-url>
cd dealeros
```

Create a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows, activate it using:

```bash
.venv\Scripts\activate
```

Install backend dependencies:

```bash
pip install -r backend/requirements.txt
```

Initialize the SQLite database and create tables:

```bash
python -c "from backend.app.database import Base, engine; from backend.app import models; Base.metadata.create_all(bind=engine)"
```

Import the CSV files:

```bash
python -m backend.app.importer
```

Start the backend:

```bash
uvicorn backend.app.main:app --reload
```

Backend: http://localhost:8000

API documentation: http://localhost:8000/docs

### Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:3000

Keep both servers running to use the dashboard.

## 5. CSV Import and Data Cleaning

The importer reads three files:

- `locations.csv`
- `system_a.csv`
- `system_b.csv`

The provided dataset contains 5 locations, 120 System A records, and 121 System B entries.

### Data Cleaning Decisions

**Record normalization**

Inconsistent references such as `rec1034`, `REC - 1070`, and `1112` are converted into a consistent `REC-1234` format.

**Monetary values**

Values such as `1,25,400.00` are converted to `Decimal("125400.00")`.

I used `Decimal` instead of `float` to avoid floating-point precision problems when comparing monetary values.

**Missing values**

Blank monetary values are stored as `None` instead of zero because a missing value does not mean the amount is zero.

**Preserving original data**

The original System B reference and monetary value are stored alongside their cleaned versions.

**Idempotent imports**

The importer checks existing primary keys before inserting or updating records, so running it multiple times does not create duplicate records.

## 6. Reconciliation Rules

The reconciliation engine compares System B values against System A's `total_value`.

| Disagreement | Description |
|---|---|
| MISSING_IN_B | A record exists in System A but has no matching B entry |
| ORPHAN_IN_B | A B entry references a record missing from System A |
| DUPLICATE_IN_B | Multiple B entries reference one A record, and their combined amount differs from A |
| VALUE_MISMATCH | The B amount differs from A or is missing |
| LOCATION_MISMATCH | Matching records have different locations |
| DATE_MISMATCH | Matching records have different dates |

### Handling Valid Splits

Multiple System B entries are not automatically treated as duplicates.

For example:

```text
System A total: 1000

System B entry 1: 400
System B entry 2: 600

Combined B total: 1000
Result: Valid split, no amount disagreement
```

### VOIDED Records

VOIDED records are included in reconciliation rather than automatically excluded. This decision avoids silently ignoring source records without an explicit business rule requiring exclusion.

## 7. Tenant Isolation

The application uses the `locations` table to identify which organization owns each location.

The API requires an organization parameter and returns disagreements according to that organization.

Cross-organization mismatches must not reveal the other organization's private location IDs, entry IDs, or monetary values.

**Limitation:** The organization parameter provides data filtering, not real authentication. A production application would require authenticated users and server-side authorization to prevent users from requesting another organization's data.

## 8. API Endpoint

### Get Disagreements

```http
GET /api/disagreements/?org=ORG-A
```

Optional filters:

```http
GET /api/disagreements/?org=ORG-A&reason=VALUE_MISMATCH&sort=-value
```

Query parameters:

| Parameter | Required | Description |
|---|---|---|
| org | Yes | Organization ID |
| reason | No | Filter by disagreement type |
| sort | No | Sort monetary values using `value` or `-value` |

The frontend uses this API to display reconciliation results.

## 9. Frontend

The Next.js dashboard provides:

- Organization selection
- Disagreement reason filtering
- Monetary value sorting
- A table showing record ID, location, disagreement reason, System A value, System B value, and difference
- Loading, error, and empty-result states

I kept the UI minimal because the assessment focuses on correctness rather than visual design.

## 10. Testing

The project uses pytest for backend testing.

Run all tests from the project root:

```bash
python -m pytest backend/tests/ -v
```

The tests cover reference normalization, monetary parsing, missing records, orphan entries, duplicate entries, value mismatches, valid splits, date and location mismatches, and tenant isolation.

To check the frontend:

```bash
cd frontend
npm run lint
npm run build
```

## 11. AI Usage and Reflections

### Q1. How did you use AI during this assessment?

I used ChatGPT and an Codex to help plan the project structure, understand the assessment requirements, implement parts of the backend and frontend, and prepare tests.

I divided the implementation into smaller Git commits instead of generating the entire application at once.

This helped me review each part separately, understand how the files connect, and verify functionality before moving to the next step.

### Q2. What was one mistake made by AI, and how did you notice and fix it?

**AI mistake:** While implementing the reconciliation logic, the AI initially used a `continue` statement after detecting a missing monetary value in System B. This meant the code could skip checking other mismatches, such as location or date differences, for the same record.

**How I noticed it:** While reviewing the reconciliation function, I noticed that the `continue` statement would stop the remaining checks for that record. Since a record can have more than one disagreement, this could lead to incomplete results.

**How I fixed it:** I adjusted the conditional logic so that missing monetary values were handled separately without skipping the location and date checks. I then checked the reconciliation results and tested the relevant cases to confirm that multiple disagreements could be detected for the same record.

### Q3. Which part of the implementation are you least confident about, and why?

The part I am least confident about is handling all possible cross-organization reconciliation edge cases.

I understand the basic approach of using the locations table to identify organization ownership. However, situations where matching records belong to different organizations require extra care to avoid exposing another organization's information.

I would want to test more unusual combinations before considering the application production-ready.

### Q4. If you had one more day, what would you improve first?

I would first improve tenant security by adding authentication and server-side authorization.

Currently, the API uses an organization query parameter to filter results. In a production application, the organization should be determined from the authenticated user's permissions rather than trusting a user-supplied parameter.

After that, I would add more integration tests for malformed CSV data and unusual reconciliation cases.

## 12. Known Limitations

- No user authentication or role-based authorization.
- SQLite is used instead of a production database server.
- Database migrations are not implemented.
- The frontend is intentionally minimal.
- The importer assumes valid location identifiers and valid dates in the supplied dataset.

Additional technical decisions are documented in `DECISIONS.md`, and source-data observations are documented in `DATA_NOTES.md`.