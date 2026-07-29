# Verified Read-Only Muni Query Patterns (TRIM IT play replica)

The connection (`~/home/trimit-query.sh`) is **read-only** — writes are denied and verified denied
(`CREATE TABLE` → permission denied). Pipe SQL on stdin. Output is pipe-delimited with a header row.

The municipal segment is **`ProjectGroupDefID = 11`**. Include this filter when a query could
otherwise bleed into commercial or other segments.

## Company / Customer queries

### City customers (name starts with "City of")
```sql
SELECT CompanyID, PublishedName
FROM gsts.dbo.Companies
WHERE PublishedName LIKE '%City of%'
ORDER BY PublishedName;
```
- ⚠️ Name column is **`PublishedName`**, NOT `CompanyName`. Wrong column = zero rows.
- Raw result is **~233 rows** but true distinct cities ≈ **180**. De-duplicate before reporting
  (see SKILL.md Data-Hygiene Pitfalls): collapse whitespace/re-import duplicates, roll department
  sub-rows under their parent city, flag typos ("Alsio Viejo") and junk rows ("ZZZ=== CITY OF CARSON ===").

### Known fragmented cities (aggregate ALL CompanyIDs when summing)
| City | Sub-rows known |
|------|----------------|
| San Diego | ≥8 (Parks, Libraries, Water Ops, Crew, Broadleaf, Palms, + base) |
| Anaheim | Public Works, Sports & Entertainment |
| Long Beach | Public Works |
| Compton | Parks & Rec, Streets Div |
| Los Angeles | Airports, Recreation & Parks, Urban Forestry (+ "Los Angeles, City of" phrasing variant) |
| Irvine | CI Palm Contract |
| Lake Forest | Residents, + council-member contact row |

## Budget queries

### A city's contract budget
- Columns are ordinal pairs: `Year01Label`/`Year01Budget` through `Year05Label`/`Year05Budget`. Match the requested fiscal-year label across all five pairs, preferably by normalizing them with `CROSS APPLY (VALUES ...)`. There is no `Year26Budget` column convention.
- Scope: **Approved (`Contracts.StatusDefID = 287`), non-Homeowner** contracts.
- Municipal membership is joined through `ProjectGroups.ProjectID` with `ProjectGroupDefID = 11`; it is not stored directly on `Projects`.
- For a complete reconciliation and reusable SQL, see `po-gap-reconciliation.md`.

### PO-gating caveat (always apply)
Municipal budgets are **entered only after a PO issues**. Any TRIM-IT-sourced budget total
**understates reality** by the amount of PO-pending work. Confirmed gap (2026-07-14): SPM Classic-View
muni $6.62M vs Nate's Sales Report $8.75M → **~$2.14M unbudgeted**. Commercial reconciled to the dollar;
the entire gap is municipal PO-pending. See SKILL.md "The PO-Gated Budget Rule."

## Invoice queries

### Invoiced by fiscal year
- Sum `InvoiceMasters`, grouped by `ProjectYearLabel`.

## Status code lookups (StatusDefs)

`StatusDefs` has ~401 rows and the same word (e.g. "Approved") appears at many
different IDs, each scoped to a specific entity. **Always filter by `Scope`**
to find the right IDs for a given table:

```sql
SELECT StatusDefID, Desc1, Scope, SeqOrder, IsValid
FROM gsts.dbo.StatusDefs
WHERE Scope = '<EntityName>'  -- e.g. 'CompanyContracts', 'Contracts', 'Proposals'
ORDER BY SeqOrder;
```

Known scopes: `CompanyContracts` (IDs 291–296, 316), `Contracts` (IDs 135–136,
161–162, 287–288, 346), `Proposals` (IDs 40, 42, 106, 140–141, 148–149, 153,
244), `GoAheads` (IDs 43–45, 49, 92, 156, 237, 246–247).

`SeqOrder` indicates display grouping: lower numbers = more prominent in the UI;
99 = soft-deleted (stays in DB, drops from lists).

## General rules
- Always read-only. Never attempt INSERT/UPDATE/CREATE/DROP.
- Parse the pipe-delimited output; skip the `---|---` separator line after the header.
- When a total looks low vs an outside report, suspect PO-pending budgets FIRST — flag, don't fabricate.
