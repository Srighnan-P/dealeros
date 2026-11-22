# DealerOS — Technical Decisions

## 1. Technology Stack

- **Backend:** FastAPI (Python)
- **Frontend:** Next.js with TypeScript
- **Database:** SQLite
- **ORM:** SQLAlchemy
- **Testing:** pytest

I chose FastAPI because it makes building REST APIs straightforward. SQLite keeps the setup simple and does not require a separate database server. Next.js provides a simple frontend for displaying reconciliation results.

## 2. Database Design

I created three tables:

- `locations` — stores locations and their organization IDs.
- `system_a_records` — stores records from System A.
- `system_b_entries` — stores entries from System B.

System A and System B both reference the locations table.

I did not create a foreign key from System B's record reference to System A because some System B entries may reference records that do not exist in System A. These orphan entries must still be stored and detected.

## 3. Handling Dirty Data

The CSV importer handles inconsistent source data:

- **Record references:** Values such as `rec1034`, `REC - 1070`, and `1112` are normalized into a consistent `REC-1234` format.
- **Monetary values:** Commas are removed before converting values to Python `Decimal`.
- **Missing values:** Blank monetary values are stored as `None`, not zero.
- **Original values:** System B's original reference and monetary value are preserved for debugging.
- **Missing actor IDs:** Blank actor IDs are stored as `None`.

The importer uses primary keys to update existing records instead of inserting duplicates when run again.

## 4. Reconciliation Rules

The reconciliation logic compares System B values against System A's `total_value`, not `base_value`.

The following disagreements are detected:

| Reason | Description |
|---|---|
| `MISSING_IN_B` | A record exists in System A but has no matching System B entry. |
| `ORPHAN_IN_B` | A System B entry references a record that does not exist in System A. |
| `DUPLICATE_IN_B` | Multiple System B entries reference the same A record, and their combined amount does not match A's total. |
| `VALUE_MISMATCH` | A single B value differs from A's total, or a matching B entry has an invalid/blank amount. |
| `LOCATION_MISMATCH` | A matching A and B record have different locations. |
| `DATE_MISMATCH` | A matching A and B record have different dates. |

### Split Entries

Multiple System B entries are not automatically considered duplicates.

If their combined monetary value equals System A's total, they are treated as a valid split.

### VOIDED Records

I decided to include `VOIDED` System A records in reconciliation rather than automatically excluding them.

This avoids silently ignoring records. A future improvement would be to confirm whether VOIDED records require different business rules.

## 5. Tenant Isolation

The `locations` table defines which organization owns each location.

The API will require an organization ID and return only disagreements belonging to that organization.

Cross-organization mismatches must not expose another organization's private location or record details.

**Limitation:** An organization query parameter alone does not authenticate the user. Production tenant isolation would require authentication and server-side authorization.

## 6. Testing

I use pytest to check:

- Reference normalization.
- Blank and formatted monetary values.
- Missing and orphan records.
- Duplicate entries and valid splits.
- Value, date, and location mismatches.
- Clean records that should not produce disagreements.

Tenant-isolation tests will be added when implementing the API.

## 7. Trade-offs and Limitations

- SQLite is suitable for this assessment but may not be ideal for a larger multi-user production application.
- The importer assumes valid location IDs and valid dates in the supplied dataset.
- Reconciliation results are calculated from imported records instead of being stored in a separate disagreements table.
- The frontend is intentionally minimal because the assessment prioritizes correctness over visual design.
- Database schema migrations are not implemented; SQLAlchemy creates the initial tables.

## 8. Future Improvements

Given another day, I would prioritize adding authenticated tenant access and stronger cross-organization isolation tests.

Other improvements would include better validation and error reporting for malformed CSV rows, database migrations, and more integration tests.