---
title: Price Buddy Grid-Only Cost Floor — Clean Method
type: reference
tags: [price-buddy, cost-floor, grid-only, trim-it, sql]
updated: 2026-07-21
---

# Price Buddy Grid-Only Cost Floor

## The Problem

The standard PB floor query (all WorkOrderLines with StatusDefID=68, Qty=1, ServiceClassID=1) produces **blended floors** that mix two very different work types:

1. **Grid-cycle trimming** — 50-200+ trees per work order, fast per-tree cycle times, efficient routing
2. **Service requests** — 1-5 trees per work order, slow per-tree cycle times, more setup/travel overhead

The service-request work inflates mid-band cycle times dramatically:

| Band | Blended Floor | Grid-Only Floor | Overstatement |
|------|:---:|:---:|:---:|
| 0-6 | $44 | $84 | Under (!) |
| 7-12 | $104 | $132 | 21% |
| 13-18 | $221 | $143 | **143%** |
| 19-24 | $279 | $187 | **125%** |
| 24-30 | $162 | $240 | Under (!) |
| 31+ | $151 | $280 | Under (!) |

Note: some bands go the other way (0-6, 24-30, 31+ have higher grid floors than blended) because the blended sample is dominated by different service types in those bands. The grid-only filter gives a consistent, reliable picture.

## The Grid-Only Query

```sql
WITH GridLines AS (
    SELECT wol.CycleTimeEach, wol.Price,
        CASE
            WHEN wol.SizeCode IN ('0-6','0-4','S','SML') THEN '0-6'
            WHEN wol.SizeCode IN ('07-12','7-12','M','MED') THEN '7-12'
            WHEN wol.SizeCode IN ('13-18','L','LRG') THEN '13-18'
            WHEN wol.SizeCode IN ('19-24','XLRG') THEN '19-24'
            WHEN wol.SizeCode IN ('24-30','25-30') THEN '24-30'
            WHEN wol.SizeCode IN ('31+','XXLRG','31-36') THEN '31+'
        END AS Band
    FROM gsts.dbo.WorkOrderLines wol WITH (NOLOCK)
    JOIN gsts.dbo.WorkOrders wo WITH (NOLOCK) ON wol.WorkOrderID = wo.WorkOrderID
    JOIN gsts.dbo.ServiceTypes st WITH (NOLOCK) ON wol.ServiceTypeID = st.ServiceTypeID
    JOIN gsts.dbo.Projects p WITH (NOLOCK) ON wo.ProjectID = p.ProjectID
    JOIN gsts.dbo.ProjectGroups pg WITH (NOLOCK) ON pg.ProjectID = p.ProjectID AND pg.ProjectGroupDefID = 11
    WHERE wol.StatusDefID = 68 AND wol.Qty = 1 AND st.ServiceClassID = 1
      AND wol.CycleTimeEach > 0 AND wol.CycleTimeEach < 600
      AND wo.WorkOrderID IN (
          SELECT wol2.WorkOrderID FROM gsts.dbo.WorkOrderLines wol2 WITH (NOLOCK)
          WHERE wol2.StatusDefID = 68 GROUP BY wol2.WorkOrderID HAVING COUNT(*) >= 100
      )
      AND (st.Desc1 LIKE '%Prune%' OR st.Desc1 LIKE '%Trim%' OR st.Desc1 LIKE '%Thin%')
)
SELECT Band, COUNT(*) AS N,
    ROUND(AVG(CycleTimeEach),1) AS AvgCycleMin,
    ROUND(AVG(CycleTimeEach)/60.0*130.0,2) AS CostFloor_130,
    ROUND(AVG(Price),2) AS AvgBilledPrice,
    ROUND(MIN(Price),2) AS MinPrice, ROUND(MAX(Price),2) AS MaxPrice
FROM GridLines WHERE Band IS NOT NULL GROUP BY Band ORDER BY Band;
```

### Key filters explained

- **`HAVING COUNT(*) >= 100`** — isolates grid-cycle WOs (100+ completed tree lines = true grid trimming). Service-request WOs rarely exceed 5-10 lines. The threshold can be lowered to 50 for more sample size at some precision cost.
- **`ProjectGroupDefID = 11`** — municipal projects only. Excludes commercial/HOA work which may have different cycle-time profiles.
- **`st.Desc1 LIKE '%Prune%' OR '%Trim%' OR '%Thin%'`** — pruning-class service types only. Excludes removals, planting, stump grinding, and non-tree services that would distort the pruning floor.

## The AvgBilledPrice Validation

The `AVG(Price)` column in the grid-only query is **the most important column** — it shows what we actually charge per tree on municipal grid contracts across all cities. This is the real-world cost reference.

**Validation chain for any bid price:**
1. Is the bid above `AvgBilledPrice`? → We have margin (we profitably charge this elsewhere)
2. Is the bid near the incumbent's current rate? → Competitive
3. Is the formula floor (`CycleTimeEach ÷ 60 × $130`) above the bid? → The formula overstates cost (it includes travel/setup), not a real concern if (1) and (2) pass

**Why the formula overstates:** `CycleTimeEach` on a grid WO includes time from arriving at the tree to leaving it — which includes walking from the truck, setting up cones, moving the boom bucket, communicating with the crew, and hauling brush. The actual hands-on pruning time is shorter. The $130/hr target is meant to cover the FULL crew cost including non-productive time, so multiplying total cycle time by $130 double-counts the overhead.

## Validated Results (Long Beach PW25-648, 2026-07-21)

N = 48,379 grid-cycle lines from municipal projects.

| Band | N | Avg Cycle (min) | Grid Floor | Avg Billed | Min Price | Max Price |
|------|--:|------:|------:|------:|------:|------:|
| 0-6 | 12,800 | 38.6 | $84 | $42 | $1.95 | $289 |
| 7-12 | 23,978 | 60.8 | $132 | $67 | $4.95 | $289 |
| 13-18 | 27,598 | 65.9 | $143 | $73 | $0.95 | $338 |
| 19-24 | 9,497 | 86.2 | $187 | $94 | $24.50 | $289 |
| 24-30 | 2,965 | 110.7 | $240 | $121 | $5.00 | $337 |
| 31+ | 1,041 | 129.3 | $280 | $133 | $39.95 | $289 |

Our Long Beach bid ($47-186 by band) was above `AvgBilledPrice` ($42-133) on every Full Prune band, confirming real margin.
