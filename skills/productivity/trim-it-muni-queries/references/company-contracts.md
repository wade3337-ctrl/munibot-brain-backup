# Company-Level Contracts (`dbo.CompanyContracts`)

TRIM IT has a **company-level contract** layer that sits above individual projects.
When Brent asks about contracts at the company level (not project-specific), this is
the table to query.

## Schema overview (51 columns)

Key columns:

| Column | Type | Notes |
|--------|------|-------|
| `CompanyContractID` | int | Primary key |
| `Desc1` | nvarchar(255) | Contract description (e.g. "Citywide Tree Maintenance Services") |
| `Desc2` | nvarchar(255) | Secondary note / sub-portfolio name (e.g. "Cypress Contracts", "Long Beach USD") |
| `CompanyID` | int | FK to `Companies` (the customer) |
| `StatusDefID` | int | FK to `StatusDefs` (see status codes below) |
| `StartDate` | datetime | Contract start |
| `EndDate` | datetime | Contract end (may be `1930-xx-xx` for bogus/perpetual — see Irvine) |
| `Qty` | decimal | Number of items/sites/years in the contract |
| `TotalPrice` | money | Total contract value |
| `HTDBilled` | money | Billed-to-date amount |
| `AmountRemaining` | money | Remaining (= TotalPrice - HTDBilled, can be negative if overbilled) |
| `PONumber` | nvarchar | PO number if applicable |
| `Year01Label`–`Year05Label` | nvarchar(50) | Fiscal year labels (e.g. "FY 23/24") |
| `Year01Budget`–`Year05Budget` | money | Per-year budget allocations |
| `SalesRepID` | int | Sales rep |
| `ContactID` | int | Billing contact FK |
| `AgreementRefNo` | nvarchar | External agreement reference number |

⚠️ **No `ProjectID` column.** CompanyContracts sit at the company level. To get
project-level contracts, query `Projects.ContractID` (which links projects to
their parent CompanyContract via `CompanyContractID` — but note: many projects
have `ContractID = NULL`; the link is often implicit via CompanyID).

⚠️ **No `PublishedName` on this table.** Join to `Companies` to get the company name:
```sql
SELECT cc.CompanyContractID, cc.Desc1, c.PublishedName, ...
FROM gsts.dbo.CompanyContracts cc
LEFT JOIN gsts.dbo.Companies c ON c.CompanyID = cc.CompanyID
```

## Status codes (verified 2026-07-17)

All 7 statuses have `StatusDefs.Scope = 'CompanyContracts'` — they are distinct
from the project-level `Contracts` table statuses (which use IDs 135=Active,
136=Inactive, 161=Pending, 162=InProcess, 287=Approved, 288=Not Approved,
346=Complete). Same words, different IDs — the StatusDefs overload pattern.

**SeqOrder** tells the display grouping in the TRIM IT UI:
- SeqOrder 1 (Pending, Approved) = live, active statuses
- SeqOrder 2 (Not Approved, InProcess, Inactive) = working/superseded
- SeqOrder 98 (Archived) = old, pushed out of active views
- SeqOrder 99 (Deleted) = soft-deleted (row stays in DB, drops from lists)

**PO-gating applies to Approved (295):** budgets are only entered on Approved
contracts. An Approved company contract carries the live budget data
(`Year01Budget`–`Year05Budget`, `PONumber`). That's why PO-pending cities show
gaps — the contract hasn't been flipped to Approved yet.

| StatusDefID | Status | SeqOrder | Count (as of 2026-07-17) |
|-------------|--------|----------|------|
| 295 | Approved | 1 | 55 |
| 316 | Archived | 98 | 19 |
| 292 | Inactive | 2 | 16 |
| 294 | InProcess | 2 | 9 |
| 291 | Deleted | 99 | 7 |
| 296 | Not Approved | 2 | 6 |
| 293 | Pending | 1 | 4 |
| **Total** | | | **146** |

## Standard query: all company contracts with names and status

```sql
SELECT cc.CompanyContractID, cc.Desc1, cc.Desc2,
       c.PublishedName, cc.CompanyID,
       s.Desc1 AS Status,
       cc.StartDate, cc.EndDate,
       cc.Qty, cc.TotalPrice, cc.HTDBilled, cc.AmountRemaining
FROM gsts.dbo.CompanyContracts cc
LEFT JOIN gsts.dbo.Companies c ON c.CompanyID = cc.CompanyID
LEFT JOIN gsts.dbo.StatusDefs s ON s.StatusDefID = cc.StatusDefID
ORDER BY c.PublishedName, cc.Desc1;
```

## Filter to active contracts only

```sql
... WHERE cc.StatusDefID = 295  -- Approved only
```

## Data quality notes

- **Duplicate company names.** Same `PublishedName` can appear under multiple
  `CompanyID`s (e.g. "The Irvine Company" = 295656, 297592, 301642). Always
  check CompanyID, not just name.
- **`*** New Company Contract ***`** placeholder rows — created when a user starts
  a new contract but hasn't filled in the description yet. Some have no data at all.
  Filter these or flag them.
- **Test companies.** "ZZZ === TEST COMPANY A ===" and "ZZ TEST COMPANY B" — filter out.
- **Negative `AmountRemaining`.** When HTD Billed > TotalPrice, AmountRemaining is
  negative (overbilled). This is legitimate — the contract was billed beyond its
  notional value, often because additional work was authorized.
- **Bogus `EndDate`.** Some contracts have `EndDate = 1930-08-31` — this is a
  data-entry placeholder for perpetual/evergreen contracts (e.g. City of Irvine).
  Don't treat 1930 as a real expiration date.

## Delivering contract data as CSV

When Brent asks for a contracts table, deliver as a CSV email attachment:

1. Query the data via `trimit-query.sh`.
2. Parse pipe-delimited output into CSV with proper headers.
3. Format money columns as `$X,XXX.XX`, dates as `YYYY-MM-DD`, NULLs as blank.
4. Save as CSV, attach to a single email with `<#part filename="..." name="TrimIT_Company_Contracts.csv">`.
5. Include a status summary table in the email body.

Worked example: 146 contracts → 19.6 KB CSV → single email. See [[email-large-deliverables]]
skill for the MML pattern.

## Related
- [[commercial-contract-proposals]] — Irvine Company and commercial-contract scope
- [[muni-query-patterns]] — verified SQL pattern catalog
- `Projects.ContractID` — links projects to their parent CompanyContract (often NULL)
