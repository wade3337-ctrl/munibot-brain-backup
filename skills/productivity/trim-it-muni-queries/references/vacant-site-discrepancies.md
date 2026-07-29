# Vacant Site Inventory Discrepancies

When Brent reports that two TRIM IT screens show different vacant-site counts for
the same city, the root cause is almost always that the screens use **different
definitions of "vacant."**

## The Problem

TRIM IT has no single "vacant site" flag. Instead, two independent columns capture
vacancy — and they don't fully overlap:

| Definition | Column | What it means | Cypress example |
|-----------|--------|---------------|-----------------|
| Species-labeled vacant | `SpeciesRef = 'Vacant Site'` | The tree record is classified as a vacant planting site | 4,505 |
| Size-less record | `SizeCode = '---'` | The record has no size code (can't be priced) | 3,202 |
| Both criteria | Both of the above | True vacant sites | 2,813 |
| Either criteria | OR of the above | Union of both definitions | 4,894 |

The gap between SpeciesRef (4,505) and SizeCode (3,202) for Cypress is driven by:
- **1,692 records** labeled `SpeciesRef = 'Vacant Site'` but with a **real SizeCode**
  assigned — may have been replanted but never reclassified.
- **389 records** with `SizeCode = '---'` but **NOT** labeled as vacant species —
  possibly real trees with missing size data.

## Which Screen Uses Which Definition

- **Data Export** — likely pulls `SpeciesRef = 'Vacant Site'` (broader set).
- **Proposal Generation** — likely filters by `SizeCode = '---'` (the pricing engine
  assigns rates by size code; `---` records can't be priced).

This hypothesis was developed for City of Cypress (2026-07-21) and partially
confirmed: Brent reported the Proposal Generation figure as **2,582 vacant sites**
(1,161 Arterial + 1,421 Grids), which is closer to the SizeCode-based count (3,202
from DB, ~2,806 active-only) than the SpeciesRef count (4,505). The Data Export
figure was **4,065** (1,482 Arterial + 2,583 Grids).

## Which Count Is More Accurate?

**The Proposal Generation count (2,582) is the more accurate count of truly empty
planting sites.** It reflects sites with no measurable tree (`SizeCode = '---'`),
while the Data Export count (4,065) includes ~1,690 phantom vacancies — sites
labeled `SpeciesRef = 'Vacant Site'` that have a real DBH size assigned (likely
replanted but never reclassified).

The 1,483-record gap between the two figures is largely those phantom vacancies.
These need to be re-surveyed and reclassified to their actual species. Until that
happens, the two TRIM IT screens will always disagree.

**Caveat:** neither figure could be reproduced exactly from the database. The DB
shows 2,806 active records with both `SpeciesRef = 'Vacant Site'` AND
`SizeCode = '---'` — close to the proposal's 2,582 but not exact. The remaining
gap may be due to: (a) the play replica being ~24h behind live, (b) the proposal
engine applying additional filters beyond SizeCode, or (c) zone-based exclusion
at the application layer.

## The Zone Reproduction Gap

Brent's Data Export for Cypress showed a pivot: Arterial = 1,482, Grids = 2,583
(total 4,065). This split **cannot be reproduced via SQL** because:

- `InventoryDetail.ZoneDefID` is **NULL for ~99% of records** (21,909 of 22,019).
- `ZoneDefs` for Cypress LocationID 1276749 has zones "Arterial" (ZoneDefID 120)
  and "Grids" (ZoneDefID 451), but only 13 and 52 trees respectively are tagged
  to them in InventoryDetail.
- `DistrictRef` text labels are populated but sparsely (e.g. "Arterial Streets"
  has 2,674 trees, but only 393 vacant).
- The TRIM IT UI resolves zone membership at the **application layer**, likely
  via spatial lat/long matching against zone boundaries. This is not reproducible
  from the database alone.

**Action:** When Brent asks about zone-based export discrepancies, report the
definition gap (SpeciesRef vs SizeCode) and be upfront that zone splits can't be
reproduced via SQL. Ask Brent for the UI-exported data instead.

## Verified Query: Vacant Site Count Breakdown

```sql
SELECT
  CASE
    WHEN SpeciesRef = 'Vacant Site' AND SizeCode = '---' THEN 'Both (true vacant)'
    WHEN SpeciesRef = 'Vacant Site' AND SizeCode <> '---' THEN 'Vacant species, has size'
    WHEN SpeciesRef <> 'Vacant Site' AND SizeCode = '---' THEN '--- size, not vacant species'
    ELSE 'Neither'
  END AS Category,
  COUNT(*) AS Count
FROM gsts.dbo.InventoryDetail
WHERE ProjectID = <pid>
GROUP BY CASE
    WHEN SpeciesRef = 'Vacant Site' AND SizeCode = '---' THEN 'Both (true vacant)'
    WHEN SpeciesRef = 'Vacant Site' AND SizeCode <> '---' THEN 'Vacant species, has size'
    WHEN SpeciesRef <> 'Vacant Site' AND SizeCode = '---' THEN '--- size, not vacant species'
    ELSE 'Neither'
  END
ORDER BY Count DESC;
```

## Proposal Engine Over-Counts Vacant Sites (critical data-quality finding)

The proposal generation engine (`ProposalLines`) assigns **service types** to
vacant sites — including trimming services that should not apply to empty
planting sites. Verified on Cypress ProposalID 800600 ($2.9M full inventory,
June 2026):

| Service Assignment | Count | Correct? |
|---|:-:|---|
| ServiceTypeID 12 — "No Trim / Not Needed" | 3,378 | ✅ Correct |
| **ServiceTypeID 148 — "Grid Pruning"** | **917** | ❌ **Vacant site assigned trimming!** |
| ServiceTypeID 21 — "Plant" | 34 | ✅ Correct (planting recommendation) |
| ServiceTypeID 158 — "Selective Limb Removal" | 1 | ❌ Vacant site assigned removal |
| **Total vacant lines in proposal** | **4,330** | |

The 917 vacant sites assigned to Grid Pruning **inflate the proposal's vacant
count and add false trimming cost.** This is a data-quality problem worth flagging
to Brent — the proposal is pricing work on empty planting sites.

Query to check a proposal's vacant-site service assignments:

```sql
SELECT
  pl.ServiceTypeID,
  st.Desc1 AS ServiceType,
  COUNT(*) AS LineCount,
  SUM(pl.TotalPrice) AS TotalValue
FROM gsts.dbo.ProposalLines pl
LEFT JOIN gsts.dbo.ServiceTypes st ON st.ServiceTypeID = pl.ServiceTypeID
WHERE pl.ProposalID = <pid>
  AND (pl.Desc1 LIKE '%Vacant%' OR pl.Desc1 LIKE '%vacant%')
GROUP BY pl.ServiceTypeID, st.Desc1
ORDER BY LineCount DESC;
```

## Cypress Investigation Summary (2026-07-21)

- ProjectID: 1097737 ("City of Cypress (Inventory)")
- LocationID: 1276749
- Total trees: 22,019
- Vacant by SpeciesRef: 4,505 (plus 3 more with leading space ` Vacant Site` = 4,508)
- Vacant by SizeCode: 3,202
- Proposal 800600 vacant lines: **4,330** (917 wrongly assigned to Grid Pruning)
- Data Export figure (Brent's CSV): 4,065 (1,482 Arterial + 2,583 Grids)
- **Brent's confirmed Proposal Generation figure: 2,582 (1,161 Arterial + 1,421 Grids)**
- Difference between the two: 1,483 records
- None of the SQL-reproducible counts match either figure exactly — zone filtering
  and status filtering at the application layer reduce both below the raw DB totals.
- The proposal count (2,582) is likely the more accurate count of truly empty sites.

## Related
- `references/inventory-gps-tree-census.md` — InventoryDetail schema and pitfalls
- `references/inventory-cost-estimates-and-contacts.md` — the "Vacant Site" exclusion pattern for cost estimates
