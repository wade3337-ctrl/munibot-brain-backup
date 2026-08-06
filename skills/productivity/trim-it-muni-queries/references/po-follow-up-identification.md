# Identifying Municipal PO Follow-Up Cities

Use this when asked which cities still need a PO or renewal follow-up for a new fiscal year.

## Interpretation

TRIM IT does not contain a definitive "PO needed" flag. Because municipal budgets are PO-gated, a missing new-FY budget is a strong **follow-up signal**, not proof that the renewal was awarded or that a PO is definitely outstanding. Report the result as a **PO/renewal follow-up list inferred from missing budget entries** and note the play replica lag.

## Correct city-level method

1. Scope to municipal projects with `ProjectGroups.ProjectGroupDefID = 11`.
2. Use Approved contracts (`Contracts.StatusDefID = 287`) and exclude homeowner-paid contracts.
3. Inspect **all approved contract rows for each city**, not merely the newest contract.
4. Normalize the requested fiscal-year labels across all five label/budget pairs with `CROSS APPLY (VALUES ...)`.
5. Aggregate matching budgets at the city level.
6. Flag a city when its city-level new-FY budget is zero/missing, or when an expiring contract has no new-FY label.
7. Separately flag partial-component gaps when the city has a budget overall but one contract component is blank; do not call the whole city PO-missing if other approved components already carry the new-FY budget/PO.
8. Review `PONumber` as supporting context only. Values such as `TBD`, `NA`, or a prior-year PO can be stale or non-authoritative.

## Why newest-contract-only is wrong

Municipal cities can have several simultaneous approved contract components. A `ROW_NUMBER()` that keeps only the newest contract can falsely classify a city as missing its PO/budget. In the July 2026 verification:

- Cypress's newest Planting contract had a blank 26/27 budget, but four other approved components carried 26/27 budgets under the same PO.
- Long Beach's newest approved row ended at 25/26, but another approved contract row carried a 26/27 budget.

Therefore, aggregate all approved components before assigning city-level status.

## Reusable SQL shape

```sql
WITH MC AS (
  SELECT DISTINCT c.CompanyID, c.PublishedName,
         ct.ContractID, ct.Desc1 AS ContractName, ct.PONumber,
         ct.Year01Label, ct.Year01Budget,
         ct.Year02Label, ct.Year02Budget,
         ct.Year03Label, ct.Year03Budget,
         ct.Year04Label, ct.Year04Budget,
         ct.Year05Label, ct.Year05Budget
  FROM gsts.dbo.Companies c
  JOIN gsts.dbo.Projects p ON p.CompanyID = c.CompanyID
  JOIN gsts.dbo.ProjectGroups pg
    ON pg.ProjectID = p.ProjectID AND pg.ProjectGroupDefID = 11
  JOIN gsts.dbo.Contracts ct ON ct.ProjectID = p.ProjectID
  WHERE ct.StatusDefID = 287
    AND ISNULL(ct.Desc1,'') NOT LIKE '%Homeowner Paid%'
    AND c.PublishedName LIKE 'City of %'
    AND c.PublishedName NOT LIKE 'ZZZ%'
), U AS (
  SELECT CompanyID, PublishedName, ContractID, ContractName, PONumber,
         v.FYLabel, v.Budget
  FROM MC
  CROSS APPLY (VALUES
    (Year01Label,Year01Budget), (Year02Label,Year02Budget),
    (Year03Label,Year03Budget), (Year04Label,Year04Budget),
    (Year05Label,Year05Budget)
  ) v(FYLabel,Budget)
)
SELECT PublishedName,
       SUM(CASE WHEN FYLabel IN ('26/27','26')
                THEN ISNULL(Budget,0) ELSE 0 END) AS CityFYBudget,
       COUNT(DISTINCT CASE WHEN FYLabel IN ('26/27','26')
                            AND Budget IS NOT NULL THEN ContractID END)
         AS BudgetedComponents,
       COUNT(DISTINCT CASE WHEN FYLabel IN ('26/27','26')
                            AND Budget IS NULL THEN ContractID END)
         AS BlankComponents
FROM U
GROUP BY PublishedName
ORDER BY PublishedName;
```

Adjust the accepted label forms for the requested FY. Some contracts use single-year labels such as `26`; never assume every city uses `25/26` style.

## Reporting format

Give two short sections:

- **Needs PO/renewal follow-up:** cities with no city-level budget for the requested FY, plus the specific evidence (blank FY budget, `TBD`, expired contract/no new-year label).
- **Already showing coverage:** cities with an entered new-FY budget/PO.

Avoid saying "confirmed outstanding PO" unless an external renewal tracker, city correspondence, or authoritative PO source confirms it.