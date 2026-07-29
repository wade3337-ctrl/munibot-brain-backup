# PO-Gap Reconciliation Workflow

Use this when comparing a TRIM-IT municipal budget total with Nate's Sales Report, Brent's workbook, or another outside source.

## Key limitation

PO-pending municipal budgets are absent, zero, or stale in TRIM IT by policy. Therefore TRIM IT alone can identify suspicious records, but it cannot supply the missing city amounts. Exact city-level attribution requires the outside report's city rows. Never distribute a top-line gap across cities by inference.

Historical benchmarks are metric- and date-specific. Do not compare a current `Contracts` total directly with an older SPM Classic-View total and call the difference a change; preserve report date, fiscal-year label, filters, and metric definition.

## 1. Pull entered contract budgets

Contracts store five ordinal label/budget pairs. Normalize them with `CROSS APPLY`:

```sql
WITH BudgetRows AS (
  SELECT c.ContractID, c.ProjectID, c.PONumber,
         v.FYLabel, v.Budget
  FROM gsts.dbo.Contracts c
  CROSS APPLY (VALUES
    (c.Year01Label,c.Year01Budget),
    (c.Year02Label,c.Year02Budget),
    (c.Year03Label,c.Year03Budget),
    (c.Year04Label,c.Year04Budget),
    (c.Year05Label,c.Year05Budget)
  ) v(FYLabel,Budget)
  WHERE c.StatusDefID = 287
    AND ISNULL(c.PONumber,'') <> 'Homeowner'
)
SELECT co.PublishedName,
       SUM(ISNULL(b.Budget,0)) AS EnteredBudget
FROM BudgetRows b
JOIN gsts.dbo.Projects p ON p.ProjectID = b.ProjectID
JOIN gsts.dbo.Companies co ON co.CompanyID = p.CompanyID
JOIN gsts.dbo.ProjectGroups pg
  ON pg.ProjectID = p.ProjectID
 AND pg.ProjectGroupDefID = 11
WHERE b.FYLabel = '25/26' -- replace explicitly
GROUP BY co.PublishedName
ORDER BY co.PublishedName;
```

`StatusDefID = 287` is Approved for contracts. The municipal relationship is in `ProjectGroups`, not a column on `Projects`.

## 2. Build the exception queue

Inspect active/current municipal projects for:

- no approved contract;
- approved contract but requested FY label absent;
- requested FY budget NULL or zero;
- PO blank or placeholder such as `TBD`;
- calendar-year labels (`26`) that do not match fiscal labels (`25/26`);
- duplicate contracts or multiple budget rows for one project;
- fragmented city/project/company records.

These are candidates for follow-up, not proof of a missing amount.

## 3. Reconcile to the outside report

Obtain the dated city-level export (Excel, CSV, PDF, screenshot, or pasted rows). Normalize city names and join it to the TRIM results. Produce:

| City | Outside amount | TRIM entered budget | Gap | PO/contract signal | Confidence/action |
|---|---:|---:|---:|---|---|

Compute `Gap = Outside amount - TRIM entered budget`. Preserve unmatched rows from both sides and flag them rather than dropping them.

## 4. Validate totals

- Sum entered budgets and compare with the same dated dashboard/view and the same fiscal-year/filter definition.
- Sum outside rows and tie them to the report's top line.
- Sum city gaps and tie them to the overall difference.
- If any tie-out fails, report it as unresolved; do not force a plug.

## Reporting language

Separate three confidence levels:

1. **Verified entered budget** — directly queried from TRIM IT.
2. **Candidate / needs PO review** — missing, zero, placeholder, or label mismatch in TRIM IT.
3. **Verified PO-pending amount** — only after matching an outside city amount to the TRIM record and confirming the interpretation.
