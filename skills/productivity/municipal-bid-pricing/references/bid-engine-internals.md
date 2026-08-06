# Bid Engine Internals — SQL and Data Flow

Detailed reference for the SQL queries and data transformations inside
`/opt/data/home/bid_engine.py` and `/opt/data/home/competitor_extractor.py`.

## Bid Engine (bid_engine.py)

### Step 2: Current rates (LocationServiceTypes)

```sql
SET NOCOUNT ON;
SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;
SELECT p.Desc1 AS ProjectName, l.City, lst.Desc1 AS LineItem,
       lst.SizeCode, lst.BasePrice, u.Desc1 AS UOM,
       lst.ServiceClassID, sc.Desc1 AS ServiceClass
FROM dbo.ProjectGroups pg WITH (NOLOCK)
JOIN dbo.Projects p WITH (NOLOCK) ON pg.ProjectID = p.ProjectID
LEFT JOIN dbo.Locations l WITH (NOLOCK) ON p.LocationID = l.LocationID
JOIN dbo.LocationServiceTypes lst WITH (NOLOCK) ON p.LocationID = lst.LocationID
LEFT JOIN dbo.UOMDefs u WITH (NOLOCK) ON lst.UOMDefID = u.UOMDefID
LEFT JOIN dbo.ServiceClasses sc WITH (NOLOCK) ON lst.ServiceClassID = sc.ServiceClassID
WHERE pg.ProjectGroupDefID = 11
AND lst.StatusDefID = 500 AND lst.BasePrice > 0
AND l.City = '{city}'
ORDER BY p.Desc1, lst.SeqOrder;
```

Key: `StatusDefID = 500` = active rate card entries. `ProjectGroupDefID = 11` = municipal.
Averages across projects per unique (LineItem, SizeCode, UOM) tuple.

### Step 3: Nearby city rates

Same query but excludes the target city, filtered to `ServiceClassID = 1` (pruning)
and `UOM = 'EA'`. Provides competitive context from other municipal contracts.

### Step 5: Commercial Price Buddy vs Municipal Grid Comparison (WorkOrderLines)

> **Current production behavior — supersedes the legacy formulas below.** Price Buddy is based on GSTS's historical **commercial** work. Municipal work usually differs because of street access, traffic control, crew deployment, density, and cycle patterns. The tool therefore treats commercial PB as a **reference, not a municipal hard floor**, and separately queries municipal grid history for comparison.
>
> Production signal version: `commercial_pb_plus_municipal_grid_v2`.
>
> The report must show, by DBH band: **Commercial PB Avg**, **Municipal Grid Avg**, **Spread $** (`municipal − commercial`), **Spread %**, both cycle-time references, **Our Bid**, and **Bid vs Grid**. It must also print the commercial/municipal caveat prominently.
>
> Municipal grid rows are filtered to `ProjectGroupDefID = 11`, pruning/trimming service types, and work orders with at least 100 completed lines. The engine fails closed when a band lacks municipal-grid comparison data. Commercial PB is excluded from automatic municipal price clamping; labor/day-rate safety floors remain enforced.

#### Legacy formulas (historical reference only)

**Formula A — CycleTimeEach (time-based, preferred):**
```sql
SELECT
    st.Desc1 AS LineItem,
    wol.SizeCode,
    COUNT(*) AS N,
    AVG(wol.CycleTimeEach) AS AvgCycleMin,
    AVG(wol.CycleTimeEach) / 60.0 * 130.0 AS CostFloor
FROM gsts.dbo.WorkOrderLines wol WITH (NOLOCK)
JOIN gsts.dbo.WorkOrders wo WITH (NOLOCK) ON wol.WorkOrderID = wo.WorkOrderID
JOIN gsts.dbo.ServiceTypes st WITH (NOLOCK) ON wol.ServiceTypeID = st.ServiceTypeID
WHERE wol.StatusDefID = 68
  AND wol.Qty = 1
  AND st.ServiceClassID = 1
  AND wol.CycleTimeEach > 0 AND wol.CycleTimeEach < 600
GROUP BY st.Desc1, wol.SizeCode;
```
This is the direct time-based cost floor: measures actual cycle time per tree, converts to hours, multiplies by $130/hr. Use when `CycleTimeEach` is populated. This was the formula specified in Gilligan's Long Beach PW25-648 prompt.

**Formula B — EstTPH (price-derived):**
```sql
WITH BandData AS (
    SELECT
        wol.Price, wol.TotalMinutes, wol.EstTPH, wol.TrimMinutes,
        wol.SizeCode,
        CASE
            WHEN wol.SizeCode IN ('0-6','00-03','04-06','0-4','0-2','4-6') THEN '0-6'
            WHEN wol.SizeCode IN ('07-12','7-12','4-10') THEN '7-12'
            WHEN wol.SizeCode IN ('13-18','10-17') THEN '13-18'
            WHEN wol.SizeCode IN ('19-24','17-24') THEN '19-24'
            WHEN wol.SizeCode IN ('25-30','24-30','25-36') THEN '24-30'
            WHEN wol.SizeCode IN ('31+','31-36','30-37','37+','37-42','42+','>30','>28.5') THEN '31+'
            WHEN wol.SizeCode IN ('SML','S','XSML') THEN '0-6'
            WHEN wol.SizeCode IN ('MED','M') THEN '13-18'
            WHEN wol.SizeCode IN ('LRG','L') THEN '19-24'
            WHEN wol.SizeCode IN ('XLRG','XL','XXLRG','XXXLRG') THEN '31+'
            ELSE NULL
        END AS Band
    FROM dbo.WorkOrderLines wol WITH (NOLOCK)
    JOIN dbo.WorkOrders wo WITH (NOLOCK) ON wol.WorkOrderID = wo.WorkOrderID
    JOIN dbo.LocationServiceTypes lst WITH (NOLOCK) ON wol.LocationServiceTypeID = lst.LocationServiceTypeID
    WHERE wo.StatusDefID = 48          -- completed work orders
    AND wol.StatusDefID = 68           -- completed lines
    AND wol.Price > 0
    AND lst.ServiceClassID = 1          -- pruning
    AND wo.DateCompleted >= '2023-01-01'
)
SELECT
    Band,
    COUNT(*) AS N,
    ROUND(AVG(Price), 2) AS AvgPrice,
    ROUND(AVG(EstTPH), 0) AS AvgEstTPH,
    ROUND(AVG(NULLIF(TrimMinutes,0)), 0) AS AvgTrimMinutes,
    ROUND(AVG(Price) / AVG(EstTPH), 3) AS EstHours,
    ROUND(AVG(Price) / AVG(EstTPH) * 130.0, 2) AS BlendedFloor,
    ROUND(AVG(Price) / AVG(EstTPH) * 130.0 * 0.75, 2) AS GridFloor
FROM BandData
WHERE Band IS NOT NULL
GROUP BY Band
ORDER BY CASE Band WHEN '0-6' THEN 1 WHEN '7-12' THEN 2 WHEN '13-18' THEN 3 WHEN '19-24' THEN 4 WHEN '24-30' THEN 5 WHEN '31+' THEN 6 END;
```

Key: `EstTPH` is the estimated target-per-hour for each line. `BlendedFloor` =
`avg_price / avg_tph * $130` — the minimum viable price to maintain $130/hr.
`GridFloor` = `BlendedFloor * 0.75` — the direct-cost floor (75% of blended).

The SizeCode normalization CASE statement maps ~25 different TRIM IT size-code
variants into 6 standard bands. This is the authoritative mapping.

**⚠ BOTH formulas produce BLENDED floors that overstate grid cost.** Documented with hard evidence on Long Beach PW25-648 (2026-07-21): the "Tree Pruning" qty=1 sample mixed slow service-request work with fast grid-trimming, producing floors 49-143% above the incumbent's profitable actual rates. Use blended floors as a documentation/sanity signal, NOT as a hard pricing floor on challenger bids. The incumbent's actual current rate card (from warehouse PRA) is the better cost reference.

### Signals JSON structure (output of bid_engine.py)

The signals JSON at `/opt/data/home/muni-scratch/bid_output/{City}_signals.json`
has these keys:

| Key | Type | Contents |
|-----|------|----------|
| `city` | str | City name |
| `tph` | int | TPH target (130) |
| `incumbent` | str | Incumbent name (e.g. "WCA") |
| `current_rates` | list[dict] | GSTS rates from LocationServiceTypes (129+ items) |
| `nearby_rates` | list[dict] | Rates from other municipal cities (180+ items) |
| `competitor_files` | list[str] | Paths to competitor/contract PDFs in warehouse |
| `price_buddy` | **dict** | Cost floor per band — keyed by band name |
| `guardrails` | dict | Pricing guardrails (discounts, floors, ratios) |
| `rfp_files` | list[str] | RFP/inventory files found in the rfp-dir |

**`price_buddy` is a dict (not a list).** Access by band name:
```python
pb = signals['price_buddy']  # dict
pb['0-6']  # → {'n': 36900, 'avg_price': 61.09, 'est_tph': 130.0, ...}
```

**`guardrails` structure:**
```json
{
  "tph_target": 130,
  "volume_bands": ["13-18", "19-24", "24-30"],
  "low_volume_bands": ["31+", "0-6"],
  "crown_raise_ratio": 0.35,      // raise/clearance = 35% of full prune floor
  "stump_removal_ratio": 0.35,   // stump = 35% of removal floor
  "escalation_rate": 0.035,
  "standard_discount": 0.08,
  "volume_discount": 0.10,
  "low_vol_discount": 0.05,
  "labor_floor": 130,            // $/hr minimum for all labor
  "day_rate_floor": 3120,        // $/day (3p × 8hr × $130)
  "emergency_day_floor": 390,    // $/hr (3p × $130)
  "emergency_night_floor": 488   // $/hr (3p × $130 × 1.25)
}
```

## Competitor Extractor (competitor_extractor.py)

### PDF format assumption

Long Beach Bid Results PDFs have a fixed 7-line-per-item layout:
```
L0: FULL PRUNE 0-6" DSH          ← description
L1: 1                            ← quantity (always 1)
L2: EACH                         ← unit
L3: $44.00                       ← bidder 1 unit price
L4: $44.00                       ← bidder 1 extended total
L5: $39.00                       ← bidder 2 unit price
L6: $39.00                       ← bidder 2 extended total
```

The scanner looks for this exact sequence: description (non-$, non-digit) → '1' →
known unit → $ → $ → $ → $. When the pattern matches, it extracts both bidder prices
and advances past the 7 lines.

### Bidder identification

The extractor looks for 'GSTS' and 'WCA' in the document text. If both are found,
it assigns Bidder1 = WCA, Bidder2 = GSTS (verified for Long Beach 2021).

**This is city-specific.** Other cities may have different bidders or different
column ordering. Always verify by checking the PDF's header/footer for bidder labels.

### Output format

```json
{
  "/path/to/2021-2026 CONTRACT": [
    {
      "description": "FULL PRUNE 0-6\" DSH",
      "unit": "EACH",
      "bidder1_price": 44.0,
      "bidder2_price": 39.0,
      "bidder1_name": "WCA",
      "bidder2_name": "GSTS"
    },
    ...
  ]
}
```

## Long Beach PW25-648 worked example (2026-07-17, full pipeline run)

| Metric | Value |
|--------|-------|
| Tree inventory | ~87,229 trees, 300+ species (6 DBH bands) |
| Line items priced | 46 (zero blanks — verified by verify_no_blanks.py) |
| Items under WCA est | 39/46 (84.8%) |
| Floor-enforced items | 9 (7 labor rates + 2 small-tree grid bands — see below) |
| Escalation | 3.5%/yr × 5yr = 18.8% (factor 1.1877) |
| Palm trunk differentiation | Date $59/ft vs Fan $38/ft ✅ |
| Crown Raise items | 6/6 populated ✅ |
| Stump Grinding items | 6/6 populated ✅ |

### Price Buddy cost floor (actual TRIM IT query, 168k+ WorkOrderLines since 2023)

| Band | N | Avg Price | Avg TPH | Est Hours | Blended Floor | Grid Floor |
|------|--:|----------:|--------:|----------:|--------------:|-----------:|
| 0-6 | 36,900 | $61.09 | 130 | 0.471 | **$61.28** | $45.96 |
| 7-12 | 60,540 | $85.99 | 133 | 0.649 | **$84.32** | $63.24 |
| 13-18 | 49,830 | $89.40 | 132 | 0.679 | **$88.23** | $66.17 |
| 19-24 | 16,931 | $117.39 | 127 | 0.922 | **$119.86** | $89.90 |
| 24-30 | 4,238 | $147.47 | 127 | 1.163 | **$151.20** | $113.40 |
| 31+ | 2,061 | $156.21 | 132 | 1.183 | **$153.73** | $115.30 |

### The 9 floor-enforced items

**2 grid-trim bands** where WCA's escalated price is below our PB blended floor:

| Band | WCA 2021 | WCA 2026 Est | GSTS Price | PB Floor | Why |
|------|---------|-------------|------------|----------|-----|
| Full Prune 0-6" | $44 | $52 | **$61** | $61.28 | WCA underbids small trees; we can't match below cost |
| Full Prune 7-12" | $64 | $76 | **$84** | $84.32 | Same — WCA's small-tree pricing is below our cost |

**7 labor/emergency rates** where WCA's escalated TPH is below our $130 floor:

| Item | WCA 2026 Est | GSTS Price | Floor |
|------|-------------|------------|-------|
| Ground Person | $112/hr | $130/hr | $130 TPH |
| Equipment Operator | $112/hr | $130/hr | $130 TPH |
| Tree Trimmer | $112/hr | $130/hr | $130 TPH |
| Day Rate Crew | $2,679/day | $3,120/day | 3p×8hr×$130 |
| Emergency Day | $335/hr | $390/hr | 3p×$130 |
| Emergency Night | $513/hr | $488/hr | 3p×$130×1.25 |
| Qualified Applicator | $135/hr | $130/hr | $130 TPH (only non-emergency labor below est) |

Note: Emergency Night WCA est ($513) is actually ABOVE our floor ($488), so it shows
positive savings. The floor-enforced flag fires because the target price ($513 × 0.92 =
$472) is below the $488 floor, so we clamp to $488. This is correct behavior.

### Full Prune pricing (volume-weighted)

| Band | Trees | % | WCA 2021 | WCA 2026 Est | GSTS Price | Discount | PB Floor |
|------|------:|---:|---------:|-------------:|-----------:|----------|----------|
| 0-6" | 5,606 | 6.4% | $44 | $52 | **$61** ⚠ | Floor | $61.28 |
| 7-12" | 15,667 | 18.0% | $64 | $76 | **$84** ⚠ | Floor | $84.32 |
| 13-18" | 21,590 | 24.8% | $84 | $100 | **$90** | **10%** | $88.23 |
| 19-24" | 19,054 | 21.8% | $114 | $135 | **$122** | **10%** | $119.86 |
| 24-30" | 22,603 | 25.9% | $174 | $207 | **$186** | **10%** | $151.20 |
| 31+" | 2,709 | 3.1% | $174 | $207 | **$197** | 5% | $153.73 |

### Palm trunk differentiation (verified different prices)

| Line | WCA 2021 | WCA 2026 Est | GSTS Price | Discount | Why |
|------|---------|-------------|------------|----------|-----|
| Date Palm clean (per ft) | $54 | $64 | **$59** | 8% | Premium work — don't undercut aggressively |
| Fan Palm clean (per ft) | $54 | $64 | **$38** | **40%** | WCA overcharges — fan palm clean is fast work |

### Renewal caps

Form has 3 blanks. Recommended 7%/7%/7% per renewal period.

### Output file

`/opt/data/home/long_beach_bids/Long_Beach_PW25-648_Cost_Proposal.xlsx`
— 4-tab workbook (Cost Proposal, Pricing Analysis, Cost Floor & Weighting, Methodology)
