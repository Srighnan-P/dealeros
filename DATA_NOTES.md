# Data Exploration Notes

## 1. Dataset Overview

I inspected the three CSV files before starting implementation.

| File | Rows | Purpose |
|---|---:|---|
| locations.csv | 5 | Maps locations to organizations |
| system_a.csv | 120 | Contains original business records |
| system_b.csv | 121 | Contains corresponding entries from System B |

System B has more rows than System A. This does not automatically mean there are errors, because some records can have multiple entries.

## 2. Data Problems Found

### Missing Values
- System A contains one record with an empty `actor_id`.
- System B contains one entry with an empty `value`.
- These rows should be preserved. Missing numeric values should not become zero.

### Inconsistent Record References
Some references in System B use different formats:

- `rec1034` → `REC-1034`
- `REC - 1070` → `REC-1070`
- `1112` → `REC-1112`

These need normalization before matching records.

### Monetary Value Formatting
- One System B value is `1,25,400.00`.
- Commas must be removed before converting it to Decimal.
- System B's `value` should be compared against System A's `total_value`.

### Missing and Orphan Records
- `REC-1015` and `REC-1061` have no matching B entries.
- `ENT/2026/4901` references `REC-1999`, which does not exist in System A.

### Multiple Entries
- `REC-1042` has two B entries with the same amount, suggesting a duplicate.
- `REC-1055` has two B entries, including one labeled `Entry part 2 of 2`. Their amounts need to be summed before deciding whether they are valid.

### Other Differences
- `REC-1009` has different dates between the systems.
- `REC-1077` has different locations: `LOC-102` in A and `LOC-201` in B.
- `REC-1019` is marked `VOIDED` in A. Its treatment needs an explicit decision.

## 3. Tenant Isolation

The location file defines ownership:

- ORG-A: LOC-101, LOC-102, LOC-103
- ORG-B: LOC-201, LOC-202

Organization ownership must come from the location mapping, not from guessing based on location IDs.

The cross-organization location mismatch for `REC-1077` requires special handling so one organization cannot see another organization's private data.

## 4. Implementation Considerations

- Use SQLite for local database storage.
- Use Decimal instead of float for monetary calculations.
- Preserve original CSV values where normalization is needed.
- Import all rows, including incomplete or invalid ones.
- Make repeated imports safe without creating duplicates.
- Distinguish genuine duplicates from valid split entries.
- Apply tenant filtering on the backend.
- Write tests for reconciliation rules and tenant isolation.
