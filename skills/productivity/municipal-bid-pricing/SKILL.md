---
name: municipal-bid-pricing
description: "Price municipal tree-care bids to win and make money. Synthesize Price Buddy cost floor, competitive comps, historical bids, inventory weighting, and TPH floor into specific recommended prices — not options."
version: 1.3.0
author: Boss Hermes
platforms: [linux]
metadata:
  hermes:
    tags: [municipal, bidding, pricing, tree-care, trim-it, price-buddy, crew-review]
    related_skills: [trim-it-operations, crew-orchestration, rfp-flow]
---

# Municipal Bid Pricing — Win the Bid AND Make Money

> The tool's job is to come back with **specific recommended prices and why** — not a table of options for the Skipper to decide. Synthesize all signals into one call.

## Trigger

When the Skipper says "price this bid," "fill out this RFP," "what should we bid for [city]," or hands you a municipal RFP packet.

## The Pricing Philosophy

**Win the bid at the lowest price that still clears our margin floor.**

- Lead with competitiveness — price to WIN on the bands that drive the most revenue
- Hard floor = TPH. **$130/hour is FULLY-LOADED** (labor + equipment + overhead + profit). Do NOT add equipment on top. This IS the all-in number.
- Weight by tree inventory — the bands with the most trees and revenue get the most competitive pricing
- Protect margin on low-volume lines where the city can't shop around

## The Pricing Engine — Step by Step

### Step 1: Extract the RFP form

Parse the city's cost-proposal form (usually a PDF) to get:
- Every line item, unit, and size band
- Contract term (base years + renewal periods)
- Escalation cap fields (may be blank — needs to be proposed)
- Any "submit AS IS, no alterations" language
- **AWARD FACTORS** — look in the RFP Overview / Bid Specifications for "Awarding Factors: Lowest Bid: Yes/No, Most Comprehensive: Yes/No." This determines everything. Lowest-bid-wins (Pomona IFB) means pure price competition; qualification-scored (Pomona 2021, Long Beach) means you can win without being cheapest.

**Two form shapes exist — identify which one before pricing:**
1. **DBH-banded** (Long Beach, Industry): single grid section with per-tree rates by DBH size band (0-6, 7-12, 13-18, 19-24, 24-30, 31+). One cost-proposal level.
2. **Flat per-tree by category** (Pomona IFB# 2026-17): grid section has a flat per-tree rate *per canopy category* (Street Trees / Park Trees / Chinese Elm / Palms / Phillips Ranch / VPD), each with multiple years and fixed tree counts — NOT DBH-banded. Plus a large DBH-banded "Extra Work" unit-price section. **Two cost-proposal levels (Level A / Level B) both required to be responsive**, differing only in tree counts per cycle.

The form shape changes the pricing strategy: DBH-banded bids need TPH cost-floor weighting by band; flat-category bids need species/district-sensitive pricing (don't bid one flat rate across all categories — the incumbent won't, and a flat rate 67% over the incumbent's cheapest category will lose the whole bid, as Pomona 2025 proved).

Extract PDF text with pymupdf (`/opt/data/.venv/bin/python` — pymupdf is installed in the venv, not system Python). If pymupdf returns blank pages, the PDF is a **scanned image** — render to PNG with `page.get_pixmap(matrix=Matrix(2.5,2.5))` and read visually, or use marker-pdf for OCR. Many city documents (schedules of compensation, contracts, Q&A addenda) arrive as scans.

### Step 2: Pull current contract rates from TRIM IT

```sql
SELECT p.Desc1, l.City, lst.Desc1 AS LineItem, lst.SizeCode, lst.BasePrice, u.Desc1 AS UOM
FROM dbo.ProjectGroups pg
JOIN dbo.Projects p ON pg.ProjectID = p.ProjectID
LEFT JOIN dbo.Locations l ON p.LocationID = l.LocationID
JOIN dbo.LocationServiceTypes lst ON p.LocationID = lst.LocationID
LEFT JOIN dbo.UOMDefs u ON lst.UOMDefID = u.UOMDefID
WHERE pg.ProjectGroupDefID = 11 AND lst.StatusDefID = 500 AND lst.BasePrice > 0
AND l.City = '<city>'
ORDER BY p.Desc1, lst.SeqOrder;
```

**A city may have MULTIPLE projects with different rates.** Average them or use a weighted average. Long Beach had 5 separate projects (Alamitos Bay, Grand Prix, Queensway Bay, Beach/Marinas, Parks & Rec) with rates ranging 30%+ apart.

### Step 3: Pull nearby city rates for competitive context

Query TRIM IT for the same service types in nearby cities. Use DBH-banded rates only (skip flat rates and species-specific rates for comparison). The competitive column tells you the market floor and ceiling.

### Step 4: Pull historical bids from the warehouse

The municipal-archive warehouse at `/opt/data/municipal-archive/` has our prior bid submissions and competitor pricing. Extract with pymupdf. Look for:
- `Schedule of Compensation.pdf` files (our prior contract rates)
- `Bid Proposal.pdf` and `Bid Results.pdf` (competitor pricing)

**HIGHEST-VALUE FIND: `Bid Results.xlsx` (not the PDF).** When a city posts bid results on PlanetBids, the warehouse often contains a `Bid Results.xlsx` with a per-bidder sheet — every bidder's unit price side by side on every line item, plus the per-bidder annual total. This is far richer than the scanned PDF. The Pomona 2025 results file had 7 sheets (one per bidder) + an "All Bids" comparison sheet showing all 7 prices per line. Load it with openpyxl (`data_only=True` to get cached values) and read the "All Bids" sheet first — it shows the competitive floor, the median, and any bidder outliers (WCA bid $0 on Prune Backup — an error to ignore; Golden West bid $565K — suspiciously low).

Also look for:
- `Staff Report - Contract Award.pdf` — names the winner and shows the evaluation criteria + scores (if qualification-weighted)
- `eBidSummary*.pdf` — PlanetBids confirmation of our own submission
- Prior-round folders (`1st Bid/`, `2nd Bid/`) — if we're re-bidding, our own prior submitted prices are in a `Cost Proposal.xlsx` in the prior-round folder. Start there, not from scratch.

### Step 5: Compare Commercial Price Buddy with Municipal Grid History (MANDATORY)

Price Buddy is based on GSTS historical **commercial** work. Municipal work usually differs because of street access, traffic control, parking, crew deployment, density, species mix, and cycle scheduling. PB remains useful, but it is a **reference signal—not a municipal hard floor or sole cost authority**.

Pull two distinct datasets and preserve their provenance:
1. **Commercial Price Buddy:** historical commercial average billing and cycle-time reference by DBH band.
2. **Municipal grid history:** actual municipal grid-cycle average billing and cycle-time reference by DBH band.

Show their dollar and percentage spread in every bid report. See `references/commercial-price-buddy-vs-municipal-grid.md` for the required fields, caveat, cohort definition, and tool implementation contract.

**Critical:** If the standard Price Buddy function does not expose both cohorts, rebuild them from `WorkOrderLines` with explicit commercial-versus-municipal filters.

#### ⚠ USE A SEPARATE MUNICIPAL GRID COHORT — DO NOT RELABEL COMMERCIAL PB

**Do not mix commercial PB records with municipal work and call the result one floor.** The historical PB cohort is commercial; the municipal grid cohort is a separate comparison built from municipal grid-cycle work. On Long Beach PW25-648, mixing service requests and grid work produced misleading results in both directions. Keep both sources visible, show the spread, sample sizes, and caveat, and use them alongside incumbent actual rates—not as interchangeable hard floors.

**Municipal Grid Comparison Query (verified starting cohort — review sample quality on each run):**

```sql
SET NOCOUNT ON;
WITH GridLines AS (
    SELECT
        wol.CycleTimeEach,
        wol.Price,
        CASE 
            WHEN wol.SizeCode IN ('0-6','0-4','S','SML') THEN '0-6'
            WHEN wol.SizeCode IN ('07-12','7-12','M','MED') THEN '7-12'
            WHEN wol.SizeCode IN ('13-18','L','LRG') THEN '13-18'
            WHEN wol.SizeCode IN ('19-24','XLRG') THEN '19-24'
            WHEN wol.SizeCode IN ('24-30','25-30') THEN '24-30'
            WHEN wol.SizeCode IN ('31+','XXLRG','31-36') THEN '31+'
            ELSE NULL
        END AS Band
    FROM gsts.dbo.WorkOrderLines wol WITH (NOLOCK)
    JOIN gsts.dbo.WorkOrders wo WITH (NOLOCK) ON wol.WorkOrderID = wo.WorkOrderID
    JOIN gsts.dbo.ServiceTypes st WITH (NOLOCK) ON wol.ServiceTypeID = st.ServiceTypeID
    JOIN gsts.dbo.Projects p WITH (NOLOCK) ON wo.ProjectID = p.ProjectID
    JOIN gsts.dbo.ProjectGroups pg WITH (NOLOCK) ON pg.ProjectID = p.ProjectID AND pg.ProjectGroupDefID = 11
    WHERE wol.StatusDefID = 68
      AND wol.Qty = 1
      AND st.ServiceClassID = 1
      AND wol.CycleTimeEach > 0 AND wol.CycleTimeEach < 600
      -- GRID FILTER: WorkOrders with 100+ completed lines = true grid-cycle work
      -- (50-200+ trees per WO). Excludes service requests (1-5 trees per WO).
      AND wo.WorkOrderID IN (
          SELECT wol2.WorkOrderID
          FROM gsts.dbo.WorkOrderLines wol2 WITH (NOLOCK)
          WHERE wol2.StatusDefID = 68
          GROUP BY wol2.WorkOrderID
          HAVING COUNT(*) >= 100
      )
      AND (st.Desc1 LIKE '%Prune%' OR st.Desc1 LIKE '%Trim%' OR st.Desc1 LIKE '%Thin%')
)
SELECT
    Band,
    COUNT(*) AS N,
    ROUND(AVG(CycleTimeEach), 1) AS AvgCycleMin,
    ROUND(AVG(CycleTimeEach) / 60.0 * 130.0, 2) AS CostFloor_130,
    ROUND(AVG(Price), 2) AS AvgBilledPrice,
    ROUND(MIN(Price), 2) AS MinPrice,
    ROUND(MAX(Price), 2) AS MaxPrice
FROM GridLines
WHERE Band IS NOT NULL
GROUP BY Band
ORDER BY Band;
```

**Three filters make this grid-only (vs the contaminated blended query):**
1. `ProjectGroupDefID = 11` — municipal projects only (not commercial/residential)
2. `HAVING COUNT(*) >= 100` — WorkOrders with 100+ completed lines = true grid-cycle trimming
3. `st.Desc1 LIKE '%Prune%' OR '%Trim%' OR '%Thin%'` — pruning service types only

#### AvgBilledPrice is a municipal benchmark—not proof of job-specific margin

The municipal cohort returns `AvgBilledPrice`: what GSTS historically billed on municipal grid-cycle work across other contracts. Compare the proposed bid to it, but preserve the city-specific caveat. A bid above the cross-city average is encouraging; it does **not** by itself prove profitability because scope, traffic control, density, species, prevailing conditions, and crew productivity vary by city.

| Signal | Meaning | Action |
|--------|---------|--------|
| Bid > Municipal AvgBilledPrice | Encouraging cross-city municipal comparison | Continue validation against target-city scope and incumbent rates |
| Bid < Municipal AvgBilledPrice | Potentially thin relative to municipal history | Flag and investigate operating differences |
| PB and municipal grid diverge materially | Sources are not apples-to-apples or samples differ | Show spread, sample size, and context; do not silently clamp |

**Long Beach PW25-648 lesson (2026-07-21):** The comparison exposed large source-dependent spreads. The durable lesson is to report commercial PB and municipal grid separately—not to declare either one universally authoritative.

**⚠ Price Buddy and municipal grid history are different sources** (Skipper guidance 2026-07-21). PB is historically commercial-based. The municipal query filtered with `ProjectGroupDefID = 11` is **not Price Buddy**; it is a separate municipal-grid benchmark. Reports must label them separately and show commercial PB average, municipal grid average, dollar spread, percentage spread, proposed bid, and bid-versus-grid spread. Use both as references alongside the incumbent's actual rates and the target city's scope.

**Two PB floor formulas exist — use the right one:**
1. **`CycleTimeEach / 60 × $130`** (time-based, preferred when CycleTimeEach is populated): Direct per-tree cost floor from the actual cycle time. This is the cleaner formula — it measures how long the work takes and multiplies by our hourly target. Use when the prompt or data provides `CycleTimeEach`.
2. **`AvgPrice / AvgEstTPH × $130`** (price-derived): Derives hours from average billed price divided by average TPH. Use when `CycleTimeEach` is sparse/missing but `Price` and `EstTPH` are available.

**⚠ Keep the commercial PB and municipal-grid cohorts separate:** A generic qty=1 sample can mix commercial, municipal, service-request, and grid-cycle economics. Do not use that mixed sample as a municipal hard floor. The municipal cohort below is for comparison with commercial PB, and both must retain source labels.

**Municipal Grid Benchmark Query (run alongside—not instead of—commercial PB):**
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

**Validated Long Beach results (N=48,379 grid-cycle lines):**

| Band | Grid Floor | Avg Billed | Blended Floor (old) |
|------|-----------|------------|---------------------|
| 0-6 | $84 | $42 | $44 |
| 7-12 | $132 | $67 | $104 |
| 13-18 | $143 | $73 | $221 |
| 19-24 | $187 | $94 | $279 |
| 24-30 | $240 | $121 | $162 |
| 31+ | $280 | $133 | $151 |

**The `AvgBilledPrice` column is a municipal historical benchmark.** It shows what GSTS billed per tree in the selected municipal grid cohort. Compare the proposed bid to it and show the delta, but do not call that delta proof of margin: target-city access, traffic control, species, density, scope, and productivity may differ. Investigate material gaps and triangulate with incumbent current rates and city-specific evidence.

**On challenger bids, use this validation chain:** (1) target-city scope and inventory, (2) incumbent's current actual rate card, (3) municipal grid average billing and sample size, (4) commercial PB as reference, and (5) crew review. Report conflicts instead of silently allowing either PB or the municipal benchmark to dictate the price.

### Step 6: Pull tree inventory from the RFP packet

The city's pricing worksheet has species × DBH band tree counts. Weight every pricing decision by volume. The bands with the most trees drive the most revenue and determine whether we win.

### Step 7: Pull invoice billing history (frequency signal) — source depends on incumbent status

**Purpose:** Identify which bid line items get billed MOST FREQUENTLY under a live municipal contract — these are the items we absolutely must price correctly to ensure a successful resulting contract. A line item that drives 40% of actual invoices matters far more than one that's never billed. **The usage MIX (which items the city actually calls in) transfers regardless of who holds the contract** — that's the signal.

**⚠️ SOURCE DEPENDS ON WHETHER WE HOLD THE CONTRACT (determine this in Step 8's incumbent check FIRST, or ask the Skipper):**

#### Path A — We ARE the incumbent (we hold the contract)
Query **TRIM IT** for our own invoice-line billing history:

```sql
SET NOCOUNT ON;
DECLARE @cityName varchar(100) = '<city>';

SELECT
    st.Desc1                                       AS LineItem,
    il.SizeCode,
    COUNT(*)                                       AS TimesBilled,
    SUM(il.Qty)                                    AS TotalQtyBilled,
    SUM(il.TotalPrice)                             AS TotalRevenue,
    AVG(il.Price)                                  AS AvgUnitPrice
FROM gsts.dbo.InvoiceLines   il WITH (NOLOCK)
JOIN gsts.dbo.Invoices       i  WITH (NOLOCK) ON il.InvoiceID = i.InvoiceID
JOIN gsts.dbo.Projects       p  WITH (NOLOCK) ON i.ProjectID = p.ProjectID
JOIN gsts.dbo.ProjectGroups  pg WITH (NOLOCK) ON pg.ProjectID = p.ProjectID AND pg.ProjectGroupDefID = 11
JOIN gsts.dbo.Companies      c  WITH (NOLOCK) ON i.CompanyID = c.CompanyID
JOIN gsts.dbo.ServiceTypes   st WITH (NOLOCK) ON il.ServiceTypeID = st.ServiceTypeID
WHERE c.PublishedName = @cityName
  AND i.StatusDefID NOT IN (138, 255, 258, 24, 140)   -- exclude Voided/Deleted
  AND il.ServiceTypeID IS NOT NULL
  AND i.InvoiceDate >= DATEADD(year, -3, GETDATE())    -- last 3 years
GROUP BY st.Desc1, il.SizeCode
ORDER BY TimesBilled DESC;
```

#### Path B — We are the CHALLENGER (incumbent holds the contract) — WAREHOUSE PRR
The warehouse has **Public Records Request (PRR)** folders containing the **incumbent's actual invoices** — obtained via records requests. This is challenger-bid gold: it shows exactly which line items the city actually uses under the live contract.

**Find PRR invoice data in the warehouse:**
```bash
# Search the city's warehouse folder for invoice/billing/PRR content
find "/opt/data/municipal-archive/<county> County/<city>/" \
  -type f \( -iname "*invoice*" -o -iname "*billing*" \) 2>/dev/null
# Also check PRR / Public Records folders directly:
find "/opt/data/municipal-archive/<county> County/<city>/" \
  -type d \( -iname "*PRR*" -o -iname "*public*record*" -o -iname "*records*" \) 2>/dev/null
```

**Two PRR data shapes exist — handle each differently:**

1. **Line-item invoice PDFs** (e.g. Glendora: `WCA_FY 2024 Invoices.pdf`, 738 pages of actual invoices). Parseable with pymupdf (text, not scans). Each invoice page shows: line description, unit price, qty, line total, unit. Extract the line-item frequency by parsing each page and counting occurrences of each service × size band. The text pattern per line is roughly:
   ```
   Tree & Stump Removal 13-18 DSH
   $680.00          5          $3,400.00    Each
   ```
   Parse with regex: capture description (text line), then unit price + qty + total on the following lines. Group by normalized line-item name (map "13-18 DSH" → 13-18 band, "Full Prune" / "Prune" → pruning, etc.).

2. **Invoice register XLSX** (e.g. Diamond Bar: `WCA Invoices July 2020 to Present.xlsx`). Columns: Invoice Number, Posted, Status, Vendor, Document, Description, Journal Number, Journal Year. This is **summary-level** (one row per invoice, no line items). Less granular — use it to derive **billing cadence** (how many invoices/month, total annual spend) but NOT per-line-item frequency. If only this exists (no line-item PDFs), fall back to the contract's Schedule of Compensation rate card + the invoice total count to estimate which items drive revenue.

**⚠️ PRR data is not always present.** Not every city's warehouse folder has PRR invoice data. If no PRR invoices exist for the target city, use a **comparable city where we DO have PRR data** (or where we're the incumbent in TRIM IT) as a frequency proxy — the billing mix transfers across similar cities even if the price level doesn't. Document the proxy choice in the debrief's `source_gaps.md`.

**How this signal feeds Step 8 (Synthesis):**
- **High-frequency items** (top 20% by TimesBilled — typically Full Prune 13-18 / 19-24 / 24-30): pricing errors compound across thousands of invoices. These are the **must-get-right items** — verify against cost floor, competitor comps, AND current billing actuals. Getting these right = a successful contract.
- **Low-frequency items** (bottom 50%, billed <10 times/year): pricing errors are low-impact. Don't over-invest in precision; protect margin instead.
- **Never-billed items**: zero billing history = scope-expansion line the city rarely uses. Price for margin (high) — won't affect competitiveness.
- **Revenue concentration**: if 3 line items drive 80% of revenue (the usual Pareto pattern), those 3 MUST be priced correctly AND competitively. Everything else is secondary.

**Tag each line in the deliverable** with its billing-frequency tier (High / Med / Low / Never) so the Skipper can see at a glance where precision matters most.

### Step 8: Synthesize into specific prices

This is the core step. The tool makes THE CALL — specific dollar amounts with a one-sentence "why" per line. Not a comparison table. Not options.

**⚠️ FIRST: determine if this is lowest-bid-wins or qualification-scored.** Read the RFP Overview §8 ("Awarding Factors: Lowest Bid Yes/No, Most Comprehensive Yes/No"). The strategy forks here:

- **Lowest-bid-wins (Pomona IFB# 2026-17):** pure price competition. Price 5-8% under the incumbent's escalated bid on volume lines. Don't leave money on the table on low-volume lines — they don't affect the score enough to matter.
- **Qualification-scored (Bell Gardens 2020, Pomona 2021 — cost = ~30% of score, qual = ~70%):** **price AT the incumbent's escalated level, not under.** Being cheapest does NOT win these — Bell Gardens 2020, we bid $282K vs WCA's $322K and still lost. Win on the proposal narrative, references, and key personnel. Hold margin. Don't undercut yourself on a bid where price is 30% of the score. The deliverable should flag this to the Skipper: *"This is a qualification-weighted RFP — the pricing matters less than the proposal narrative. Want help with that?"*

**For challenger bids (we don't hold the contract), lowest-bid-wins:**
1. Start from the incumbent's inflation-adjusted bid (Step 4 competitor extraction)
2. Target 5-10% under the escalated estimate on volume bands (bands driving >15% of revenue)
3. Compare against both municipal grid history and commercial PB (Step 5). Neither is an automatic hard floor; flag material conflicts and validate with city-specific scope and incumbent actuals.
4. Price low-volume bands (<5% of trees) above all comps — protect margin, won't hurt bid score
5. The 24-30 band is typically the hardest: it's 25-35% of revenue but the grid floor may exceed the incumbent's bid. Accept the gap and bet on grid efficiency.

**For challenger bids, qualification-scored:**
1. Price AT the incumbent's escalated level (don't undercut — it doesn't help and erodes margin)
2. Focus energy on the qualification narrative — that's where 70% of the score lives
3. Flag any disqualification risks (missed pre-bid meetings, missing forms — see pitfall #30)

**For incumbent bids (we hold the contract):**
1. Start from current rates
2. Hold or slightly raise, keeping under the most expensive comp
3. Use Price Buddy to verify margin on every band
4. This is the easier scenario — we're not fighting to take the contract

**TPH target is universal.** $130/hr applies to every municipal bid this year regardless of prevailing-wage status (see Key Rule #2). The RFP's prevailing-wage field is still worth noting for competitive analysis — on DIR/PW jobs everyone pays the same Davis-Bacon rates, so there's no labor advantage between bidders; on non-PW jobs competitors may price cheaper labor. But our own target stays $130 either way until the Skipper adjusts the yearly parameter.

**For all bids, per line type (overlay with billing-frequency tiers from Step 7):**
1. **High volume + high revenue + HIGH billing frequency** (e.g., 13-18, 19-24, 24-30 Full Prune) → **price to WIN, verify to the dollar.** These are the must-get-right items — check against cost floor AND competitor comp AND current billing actuals (Step 7 AvgUnitPrice). A pricing error here compounds across thousands of invoices under the resulting contract.
2. **Low volume** (e.g., 0-6, 31+) → **price for MARGIN.** Won't hurt bid score at 3-6% of volume.
3. **Premium lines** (hourly, emergency, arborist) → **HOLD at current.** City can't shop around. No reason to cut.
4. **Single-tree/service-request** → **Price ABOVE all grid rates** to prevent adverse selection.
5. **Removals/stumps** → If pricing basis changed (per-inch → per-tree), convert using band midpoints and flag for review.
6. **Low/never-billed items** (Step 7 frequency tier = Low or Never) → **price for margin.** Don't over-invest in precision on lines the city rarely calls in — they won't swing the bid score or the resulting contract's P&L.

### Step 9: Crew review (Kimi K3 + Gemini 3.1 Pro)

Two independent model judges sanity-check the pricing before it goes to the Skipper. Scripts: `/opt/data/home/crew/kimi-ask.py` and `/opt/data/home/crew/gemini-ask.py`. Both are LIVE and tested (2026-07-20, Skipper + Gilligan). Keys at `/opt/data/.secrets/{kimi,gemini}.json` (0600).

**How to call them (feed evidence INLINE — they can't run your tools/queries):**
```sh
# Kimi K3 (reasoning model, max_tokens=40000 default):
python3 /opt/data/home/crew/kimi-ask.py < /path/to/bid_check_brief.txt

# Gemini 3.1 Pro (temp=0, most reliable judge):
python3 /opt/data/home/crew/gemini-ask.py < /path/to/bid_check_brief.txt
```

**The brief should include:** all line items with bid prices + quantities, commercial PB references by band, municipal grid averages and sample sizes, the PB-to-grid spreads, the explicit note that PB is commercial-based and reference-only, the $130 fully-loaded TPH parameter, the adverse-selection rule (single-tree > highest grid rate), the Crown Raise/Stump no-blank rule, and scope assumptions. Ask each to "return each error with the corrected figure, or NO ERRORS FOUND."

**Reconcile adversarially:** ask both independently. If they disagree, dig in before deciding. They catch:
- Prices that conflict materially with municipal history, commercial PB, or incumbent actuals without documented explanation
- Structural issues (flat pricing where progression needed, adverse selection traps)
- Premium lines being unnecessarily cut
- Escalation cap inadequacy
- Missing/blank required lines (Crown Raise, Stump Grinding)

**They are advisors, not deciders.** You still own the bid. Synthesize their feedback, fix real issues, finalize. Keep crew-review details OUT of the deliverable (internal only).

**Fallback:** if a judge is down (503/timeout), proceed with the other and note it. If both are down, flag to the Skipper that the crew-review pass was skipped and let him be the review. Override Gemini model via `GEMINI_MODEL=gemini-2.5-pro` if 3.1-pro is overloaded.

### Step 10: Deliver

Build an Excel spreadsheet (openpyxl in `/opt/data/.venv/bin/python`) with:
- Sheet 1: Cost Proposal (all line items with tree counts, annual values, editable price column, **billing-frequency tier from Step 7**)
- Sheet 2: Commercial PB vs Municipal Grid (both sources by band, sample sizes, dollar spread, percentage spread, proposed bid, bid-vs-grid delta, and explicit reference-only caveat)
- Sheet 3: Volume Analysis (DBH distribution + contract projections)
- Sheet 4: Regional Comparison (our prices vs nearby cities)
- Sheet 5: Top Species (inventory breakdown)
- Sheet 6: Billing Frequency (invoice history from Step 7 — TimesBilled, TotalRevenue, AvgUnitPrice per line item, sorted by frequency)

**No internal change notes, version history, or crew review details in the deliverable.** Those are for us, not the team.

**Add a WCA/Incumbent Benchmark & Frequency sheet when competitor invoice history is available.** When Brent provides a competitor invoice-history workbook (e.g., `WCA Invoicing.xlsx`), add it as a new sheet to the deliverable showing: (a) incumbent unit price history by FY with CPI escalation %, (b) annual quantities by line item, (c) 3-year averages for quantity/revenue, (d) our prices side-by-side with variance flags, (e) revenue ranking per line item, and (f) auto-generated strategic notes flagging top revenue drivers. Brent's directive: "the frequency of each line item is the most valuable information — it lets me weigh each item by usage so I know which will be our true money makers." FY25-26 incumbent pricing may be a gap — flag it and ask Brent to provide the current schedule.

**If the RFP requires two service levels (Level A / Level B), build BOTH as separate sheets** — the form will be rejected as non-responsive if either is missing (Pomona IFB# 2026-17 explicitly states "both cost proposals for Level A and Level B must be completed to be considered responsive"). They usually share the same Extra Work unit prices and differ only in the grid tree counts per year. Add a "Competitive Analysis" sheet showing key line items vs the incumbent + the full bidder field from `Bid Results.xlsx` — the Skipper reviews this to sanity-check the pricing before submission.

**Verify before delivery:** run `scripts/verify_no_blanks.py <path>`. The current script is generic (scans all sheets, detects priced rows by unit-token heuristic, does not hard-fail on section counts) — it works on any bid form shape. Earlier versions hardcoded a `"Cost Proposal"` sheet name and Long Beach section structure; those broke on Pomona. If you add sheets with names containing "analysis"/"comparison"/"reference"/"notes", the verifier skips them automatically.

**Build the debrief zip package (MANDATORY).** Alongside the spreadsheet deliverable, produce a source-data debrief zip so the Skipper can confirm the tool chose its source data correctly. Package the PRIMARY source documents the tool actually read during this bid run:

```
<City>_<RFP#>_debrief_<YYYY-MM-DD>.zip
├── 00_MANIFEST.md          ← what each file is, where it came from, how it was used
├── rfp/
│   ├── cost_proposal_form.pdf       (or .xlsx — the city's blank form we filled)
│   └── rfp_specifications.pdf       (scope, award factors, term, escalation rules)
├── trim_it/                  (incumbent bids only — our own invoice history from Path A)
│   ├── current_rates.csv            (Step 2 output — our current contract rates)
│   ├── nearby_city_rates.csv        (Step 3 — competitive context)
│   ├── price_buddy_costfloor.csv    (Step 5 — cost floor per band)
│   ├── invoice_billing_history.csv  (Step 7 Path A — frequency signal, IF we hold the contract)
│   └── tree_inventory.csv           (Step 6 — species × DBH counts from pricing worksheet)
├── warehouse/
│   ├── bid_results.xlsx             (Step 4 — competitor unit prices side-by-side, if found)
│   ├── prior_schedule_of_compensation.pdf  (our prior contract rates, if found)
│   ├── staff_report_award.pdf       (winner + evaluation scores, if found)
│   └── prr_invoices/                (Step 7 Path B — incumbent's actual invoices from PRR, IF challenger bid)
│       ├── wca_invoice_pages_parsed.csv    (line-item frequency extracted from PRR invoice PDFs)
│       └── [original PRR invoice PDFs/xlsx copied or referenced]
└── analysis/
    ├── frequency_tiers.csv          (each bid line tagged High/Med/Low/Never billing frequency)
    └── source_gaps.md               (what we looked for but DIDN'T find — missing comps, no bid results, etc.)
```

**The MANIFEST is the key file.** It lists every source document, where it was sourced from (TRIM IT query / warehouse path / RFP packet), which pricing step consumed it, and a one-line note on its quality/completeness. This lets the Skipper audit the tool's source-data choices without re-running the pipeline. Use `python3 -m zipfile` or `zip` to build the archive. **Every file in the zip must be one the tool actually read** — do NOT pad with generic reference docs the tool didn't use for this specific bid.

**Surface both deliverables together:** the Cost Proposal spreadsheet AND the debrief zip, as two separate `MEDIA:` paths. The Skipper reviews the spreadsheet for the prices, the debrief for the sourcing.

## Key Rules (Skipper-confirmed)

1. **THE TOOL DECIDES.** Come back with recommended prices and the reasoning. Do not present option tables for the Skipper to choose from. The Skipper said: "The idea of this tool is to come up with numbers that will win us the bid and make us money. You are presenting data for us to decide."
2. **TPH target = $130/hr (this year, 2026), FULLY-LOADED, applies to ALL municipal bids.** Labor + equipment + overhead + profit. Do NOT add equipment on top. This is our universal labor target for every muni bid regardless of prevailing-wage status — not a DIR/PW-only floor (Skipper-corrected 2026-07-20). **It is a yearly parameter**, not a permanent constant: revisit at the start of each year and adjust as costs shift. The prevailing-wage field on the RFP no longer changes the floor. Skipper confirmed $130 is fully-loaded when crew review models incorrectly assumed it was labor-only.
3. **Weight by tree inventory.** Volume-weighted pricing is mandatory. The Skipper asked "did we weight the number of trees in each line item?" — it's a core expectation.
4. **Use commercial Price Buddy and municipal grid history as distinct signals.** PB is historically commercial-based; municipal work usually differs. Show both, their spread, sample sizes, and source caveat. Neither source alone is the municipal cost authority.
5. **Hold premium lines at current.** Emergency, hourly, arborist rates — city can't shop around.
6. **No change notes in deliverables.** Internal rationale stays internal. The Skipper said "remove the pricing change notes from the spreadsheet the team doesn't need those."
7. **Average multiple project rates.** A city may have several TRIM IT projects with different rates. The Skipper said "I would use an average" when we discovered Long Beach had 5 different rate cards.
8. **Crew review is LIVE (Kimi K3 + Gemini 3.1 Pro, 2026-07-20).** Two independent judges, called single-shot via `/opt/data/home/crew/{kimi,gemini}-ask.py`. Feed evidence inline, ask adversarially, reconcile disagreements. They are advisors, not deciders — you own the bid.
9. **DIR prevailing wage = same labor costs for everyone.** Competitor hourly rates are their TPH, not cheaper labor. Skipper corrected this when we wrongly assumed WCA had a labor cost advantage.
10. **Don't be too aggressive with price cuts.** Bump thin bands up. Compare every line against the target scope, incumbent actuals, municipal grid history, and commercial PB reference; investigate conflicts rather than treating PB as a hard municipal floor.
11. **Deliver a spreadsheet, not a PDF.** The Skipper said "it would be better to extract the info from the pdf into a spreadsheet and populate that so we can manipulate the numbers easily."
12. **Include the PB-versus-municipal-grid comparison in the deliverable.** For each DBH band show commercial PB average, municipal grid average, dollar spread, percentage spread, proposed bid, bid-versus-grid delta, sample sizes, and the reference-only caveat.
13. **Invoice billing frequency drives precision priorities — source depends on incumbent status.** The Skipper said (2026-07-20): "include invoice history data so it knows which bid items will be billed most frequently thus it knows the ones we absolutely need to get correct so that if we win the bid we have a successful resulting contract." Pull invoice history BEFORE synthesis, tag every line with its billing-frequency tier, and concentrate pricing precision on the high-frequency items. **Source:** if we HOLD the contract → TRIM IT `InvoiceLines` (our own billing data). If we are the CHALLENGER → warehouse PRR folders (Public Records Request — the incumbent's actual invoices, e.g. Glendora `WCA_FY 2024 Invoices.pdf`, Diamond Bar `WCA Invoices July 2020 to Present.xlsx`). The usage MIX transfers across similar cities — use a comparable city as a frequency proxy if no PRR data exists for the target.
14. **Every bid ships with a source-data debrief zip.** The Skipper said (2026-07-20): "I would want a debrief zip file package that includes the primary data it sourced from the warehouse so I can confirm it chose its source data correctly." The debrief zip packages the actual source files the tool read (TRIM IT query outputs, warehouse PDFs/xlsx, RFP forms) plus a MANIFEST explaining each file's provenance and role. This is MANDATORY alongside the spreadsheet deliverable — not optional, not only-when-asked.
15. **When Brent provides a competitor invoice-history workbook, frequency is the gold.** Brent said (2026-07-21): "The most valuable information here is the frequency of each line item — it should allow us to weigh each line item by its usage so I know which line items will be our true money makers once we get the contract." Unit prices serve as the incumbent benchmark + reveal CPI escalation patterns. FY25-26 pricing may be a gap — flag and request. The Municipal Invoice History SOP (for building these workbooks from PRA productions) is a SEPARATE workflow — do not merge into this skill. See the vault note at `/opt/data/home/municipal-knowledge/references/municipal-invoice-history-sop.md`.
16. **Brent audits column-level data provenance — label every column's source explicitly.** (2026-07-22). When Brent reviews a deliverable, he asks "where did Column X come from?" for each column. Computed estimates must be labeled as estimates — not presented as raw data. A spreadsheet that can't pass a provenance audit is a trust failure. This is embedded in the skill as pitfall #41 and verification checklist items.

## Pitfalls

1. **pymupdf is in the venv, not system Python.** Use `/opt/data/.venv/bin/python` for PDF extraction.
2. **Himalaya does NOT support attachments.** Use Python `smtplib` directly for file attachments.
3. **WorkOrderLines StatusDefID = 68** for completed lines (NOT 48, which is WO-level).
4. **SizeCodes use BOTH formats** in WorkOrderLines: DBH bands (`0-6`, `07-12`, `13-18`) AND S/M/L/XLRG. Map both.
5. **Pricing Worksheet.xlsx may be large (5-30MB)** but often loads fine with `openpyxl.load_workbook(path, data_only=True, read_only=True)`. The `read_only=True` flag streams the file instead of loading it all into memory — a 5MB Long Beach worksheet with 142K rows loaded instantly this way. If `read_only` still times out (30MB+ files with embedded images), fall back to the PDF version or the `Pivot Table` sheet which is usually a clean species×DBH summary. **Always check for a `Pivot Table` sheet first** — it has pre-aggregated species×DBH counts without the raw 100K+ row inventory, which is what you actually need for volume weighting.
6. **Blended Price Buddy data overstates large-band cost** (inflated by slow service requests). For precision, filter to grid-only WOs (100+ completed lines per WO). The grid-only CTE query is in Step 5 above — use it instead of the raw qty=1 query. **Always also pull `AVG(Price)` as AvgBilledPrice** from the same grid-only sample — if your bid is above what we actually charge on other municipal grid contracts, you have margin regardless of what the formula floor says. The floor formula (CycleTimeEach ÷ 60 × $130) captures travel + setup + non-productive minutes and systematically overstates true per-tree cost.
7. **31+ is an unbounded band.** A 32" and a 60" tree can't share one price. Flag for extraordinary-size provision.
8. **Single-tree line is an adverse selection trap.** Price it ABOVE all grid rates so the city always saves by routing through grid trimming.
9. **Escalation at 5% per renewal ≠ 5% per year.** 3 renewals × 5% = 16% cumulative. Propose annual CPI adjustment.
10. **NEVER leave Crown Raise or Stump Grinding blank — but "35%" is a blank-prevention FLOOR, not a pricing rule.** The "Crown Raise = 35% of Full Prune" / "Stump = 35% of Removal" figures are **derivation fallbacks for when no competitor comp exists** — they guarantee the line is populated (non-responsive risk avoided). When you HAVE the incumbent's actual raise/stump bids (from warehouse `Bid Results.xlsx`), price against the competitor (5-8% under), NOT against the 35% derivation. Taking 35% of removal at face value on a challenger bid produces stump prices 60-70% ABOVE the incumbent — confirmed on Long Beach PW25-648 (2026-07-18). Priority: (1) competitor comp if available, (2) 35% derivation as fallback, (3) never blank.
11. **NEVER price labor below $130/hr.** This is the fully-loaded TPH floor. Day rate floor = 3 persons × 8 hrs × $130 = $3,120.
12. **Differentiate palm species.** Date Palm clean ≠ Fan Palm clean. Date is premium work, Fan is easier. Price Date Palm clean at 8% under WCA. Price Fan Palm clean at 40% under WCA (WCA overcharges for fan palm clean — it's fast work).
13. **Variable discount by volume band.** Do NOT apply a flat 7% discount everywhere. 10% under WCA on volume bands (13-18, 19-24, 24-30), 8% standard, 5% on low-volume bands (0-6, 31+) to protect margin.
14. **MuniBot HOME=/root.** Scripts must run by full path (`/opt/data/home/bid_engine.py`), not `~/`.
15. **Crew review models may wrongly assume TPH is labor-only.** When Kimi/Gemini say "add equipment on top of $130," they are WRONG. $130 is fully-loaded. Ignore their recommendation to add equipment/overhead — it double-counts. State the "$130 fully-loaded" rule explicitly in the review brief to prevent this.
16. **Competitor hourly rates are their TPH, not their labor cost.** On DIR prevailing wage jobs, everyone pays the same Davis-Bacon rates. WCA's $94/hr in 2021 was their fully-loaded TPH — same metric as our $130 today. Their TPH has risen alongside ours.
17. **Determine incumbent status BEFORE pricing.** Ask the Skipper who holds the contract. If we are the challenger, the benchmark is the incumbent's actual prior bid (from warehouse Bid Results), not our own current rates. Getting this wrong leads to pricing as an incumbent when you should be pricing as a challenger.
18. **Competitor bid data is in the warehouse.** Bid Results PDFs show actual bidder unit prices side by side. This is the most valuable competitive intel available. The `competitor_extractor.py` script parses these automatically.
19. **MuniBot first test (2026-07-17) found 4 bugs:** blank Crown Raise/Stump lines, labor below $130 floor, flat 7% discount, no palm differentiation. All fixed in v2 scripts — verify the output prints "✅ All items priced. Zero blanks." after every run.
20. **Floor-enforced count varies with PB data freshness (7–9 items).** The 0-6" and 7-12" full-prune bands flip to floor-enforced when PB blended floors are current (PB 0-6 = $61, PB 7-12 = $84 — both above WCA's escalated estimates of $52/$76). Do NOT assume only labor rates hit the floor. Small-tree bands where WCA underbids will also clamp. The count depends on which PB query run is in the signals.json.
21. **Tree inventory PDFs use a column-per-band layout where numbers appear on separate text lines, not inline with species names.** A naive regex parser looking for 6+ numbers on one line returns 0 rows. The `generate_bid_spreadsheet.py` template has hardcoded tree counts (`inventory = {'0-6': 5606, '7-12': 15667, '13-18': 21590, '19-24': 19054, '24-30': 22603, '31+': 2709}`) from a prior verified parse. If pricing a different city, you MUST update these counts — extract them from the city's pricing worksheet manually (sum each DBH column across all species) and patch the dict in the template before running the generator.
22. **Verified manual pipeline (2026-07-17).** When `bid_engine.py` references stale paths, run the pipeline manually in 3 steps. This is the proven sequence:
    ```bash
    # Step 1: Price all line items
    /opt/data/.venv/bin/python scripts/price_bid.py \
      --competitor-bids /path/to/competitor_bids.json \
      --signals /path/to/signals.json \
      --output /path/to/priced.json \
      --escalation-rate 0.035 --years 5

    # Step 2: Generate 4-tab spreadsheet
    /opt/data/.venv/bin/python templates/generate_bid_spreadsheet.py \
      --priced /path/to/priced.json \
      --signals /path/to/signals.json \
      --output /path/to/Cost_Proposal.xlsx \
      --city "Long Beach" --rfp "PW25-648" --renewal-caps 7,7,7

    # Step 3: Verify zero blanks (MUST pass before delivery)
    /opt/data/.venv/bin/python scripts/verify_no_blanks.py /path/to/Cost_Proposal.xlsx
    ```
    The `competitor_bids.json` is a flat array of `{description, unit, bidder1_price}` objects. The `signals.json` must have a `price_buddy` dict keyed by DBH band with `blended_floor` values. See `references/bid-engine-internals.md` for the exact JSON shapes.
23. **Price Buddy SizeCode mapping — the authoritative list.** TRIM IT WorkOrderLines uses ~20 different SizeCode formats. Query `SELECT TOP 20 SizeCode, COUNT(*) FROM WorkOrderLines ... GROUP BY SizeCode ORDER BY COUNT(*) DESC` to discover them. The mapping that works: `0-6/0-4/S/SML→0-6`, `07-12/7-12/M/MED→7-12`, `13-18/L/LRG→13-18`, `19-24/XLRG→19-24`, `24-30/25-30→24-30`, `31+/XXLRG→31+`. Exclude `---` and `------` (sentinel values). Note: `LRG` maps to 13-18 (not 19-24) based on actual data distribution.
24. **WorkOrderLines has no `Hours` column.** Use `EstTPH` (trees per hour estimate), `TotalMinutes`, `TrimMinutes`, `CycleTimeMinutes`, or `DirectCost` instead. The cost floor formula: `(60 / EstTPH) × $130 = per-tree floor at $130/hr TPH`.
25. **NEVER bid a flat per-tree grid rate across all canopy categories on a flat-category bid (Pomona IFB shape).** We lost Pomona Oct 2025 bidding $139/tree flat on Street/Park/Elm/Phillips — WCA bid species/district-sensitive ($83 Street / $143 Park / $233 Elm / $133 Phillips) and beat us by 67% on the highest-volume line. Price each grid category against the incumbent's actual per-category bid, not against a single blended rate. This is the #1 way to lose a flat-category IFB.
26. **`Bid Results.xlsx` > `Bid Results.pdf`.** The xlsx (one sheet per bidder + an "All Bids" comparison) is structured and complete; the PDF is a scanned image that returns blank from pymupdf. Always check for the xlsx version first. Load with `openpyxl.load_workbook(path, data_only=True)` to get cached formula values.
27. **City contracts, schedules of compensation, and Q&A addenda are frequently scanned images**, not text PDFs. pymupdf returns 0 chars. Render to PNG (`page.get_pixmap(matrix=Matrix(2.5,2.5))`) and read visually, or invoke marker-pdf for OCR. Don't conclude "the file is empty" — it's a scan. Tesseract is NOT installed on this host; marker-pdf (~5GB) is the OCR path if visual reading isn't enough.
28. **Two-level bids (Level A / Level B) require BOTH levels completed or the bid is non-responsive.** They share Extra Work unit prices and differ only in grid tree counts/cycles. Don't waste time pricing Extra Work twice — copy prices across both sheets and only vary the grid section. (Pomona IFB# 2026-17, Level A = 5-yr Street / 3-yr Park / 10-yr Phillips; Level B = 5-yr Street / 4-yr Park / 15-yr Phillips.)
29. **Qualification-scored RFPs need a DIFFERENT strategy than lowest-bid-wins.** Read RFP Overview §8 first. Bell Gardens 2020: we bid $282K vs WCA $322K — CHEAPER — and lost because cost was only 30% of the score. Don't undercut on a qual-weighted bid; price at the incumbent's level and win on the narrative. Conversely, Pomona IFB 2026 is lowest-bid-wins — undercut aggressively on volume lines. Getting this backwards wastes a bid.
30. **Pre-bid meeting requirements are often added via ADDENDUM, not the original RFP.** Bell Gardens 2025: original RFP (Aug 12) had no pre-bid meeting; Addendum 1 (Aug 20) added mandatory meetings on Aug 26/28 — AFTER the question deadline. We missed it, were disqualified, and Scott Griffiths filed a formal protest that failed. **When a bid folder shows Addenda, scan them ALL for "mandatory" requirements before the Skipper commits to bidding.** Surface disqualification risks as the first item in any bid review.
31. **$130/hr TPH is the universal target for ALL muni bids this year (2026), not just prevailing-wage jobs.** Skipper-corrected 2026-07-20: "We always want to target $130 TPH this year. Going forward this may change." It is a **yearly parameter** — revisit at the start of each year and adjust as costs shift. Do NOT drop to $75/man-hr on non-PW bids; that was the old rule and it is retired. The prevailing-wage field is still relevant for competitive analysis (DIR/PW = same Davis-Bacon labor for everyone; non-PW = competitors may price cheaper), but it no longer changes our own TPH target.
32. **Protest letters are in the warehouse** under `<city>/<contract>/Protest/`. If we've been disqualified before, read the prior protest before re-bidding — it tells you exactly what procedural trap to avoid this round. (Bell Gardens protest: `/opt/data/municipal-archive/Los Angeles County/Bell Gardens/2025-XXXX CONTRACT/Protest/`)
33. **Boss Herman sends large RFP packets as 3 chunked Gmail attachments** (Gmail's 25MB/message cap). Each email carries one `lb_chunk_0N` file. Extract all three via IMAP UID fetch, rejoin with `cat chunk_00 chunk_01 chunk_02 > packet.tar.gz`, and **verify SHA-256** against the hash in his email body before extracting. The `email.policy` module can throw `AttributeError: message_factory` on some Python builds — use plain `email.message_from_bytes(raw)` (no `policy=policy` kwarg). Fetching large attachments: use `mail.uid('fetch', uid, '(BODY.PEEK[])')` not sequence-number fetch, and handle multi-packet responses (the tuple with bytes may be at index `[0][1]`, not the last element). Full recipe in `references/rfp-packet-extraction.md`.
34. **The Skipper (Jason Wade, jwade@gstsinc.com) reviews bids and wants deliverables surfaced immediately as `MEDIA:/path` — don't re-explain how to download, don't summarize what's in the file if he can see it, don't ask "want me to send it?" unless he asks for email.** When he says "surface the file" or "send it to [address]," the whole job is: produce the path or hit send. Context and strategy belong in the message that accompanied the file *before* he asked to see it. On Telegram, large xlsx files can't be drag-saved cleanly — offer email proactively as the delivery fallback, but route to HIS address (jwade), not Brent's (bbeller), unless he specifies otherwise.
35. **PRR (Public Records Request) invoice data comes in two shapes — handle each differently.** (1) **Line-item invoice PDFs** (e.g. Glendora `WCA_FY 2024 Invoices.pdf`, 738 pages): parseable text with item/price/qty/total per line — extract per-line-item frequency. (2) **Invoice register XLSX** (e.g. Diamond Bar `WCA Invoices July 2020 to Present.xlsx`): one row per invoice with Vendor/Status/Year but NO line items — use for billing cadence only, not per-line frequency. Always check which shape you have before parsing. Not every city's warehouse folder has PRR data — fall back to a comparable-city proxy and document in `source_gaps.md`.
36. **Incumbent invoice history source depends on who holds the contract — get this right or the frequency signal is empty.** If we HOLD the contract, our own billing is in TRIM IT `InvoiceLines` (Step 7 Path A). If we are the CHALLENGER, our TRIM IT history for that city is thin/absent — pull from warehouse PRR folders instead (Step 7 Path B). Running the TRIM IT query on a city we don't hold returns near-zero rows and produces a useless "Never billed" tier across every line. Always determine incumbent status (Step 8 check or ask the Skipper) BEFORE choosing the invoice-history source.
37. **Use the GRID-ONLY Price Buddy query — NOT the blended floor. (Skipper-confirmed 2026-07-21).** The default blended PB query (all WorkOrderLines, Qty=1, ServiceClassID=1) is contaminated by slow service-request work mixed into the sample. On Long Beach PW25-648 it produced floors 49-143% above the incumbent's profitable actual rates, falsely flagging 7-12, 13-18, and 19-24 as "below cost." The grid-only query adds three filters: (1) `ProjectGroupDefID = 11` (municipal only), (2) `HAVING COUNT(*) >= 100` on the WorkOrder subquery (true grid-cycle WOs with 100+ trees, not 1-5 tree service requests), (3) pruning service types only (`LIKE '%Prune%' OR '%Trim%' OR '%Thin%'`). Always use the grid-only query as the primary cost floor. The `AvgBilledPrice` column it returns is the real margin check — if your bid is above what we actually charge on other municipal grid contracts, you have real margin regardless of what the floor formula says. The floor formula (`CycleTimeEach ÷ 60 × $130`) overstates true cost because it captures travel, setup, and non-productive minutes spread across the cycle.
37. **Incumbent's CURRENT CPI-escalated rate card is in the warehouse PRA folder — use it BEFORE escalating from the original bid.** Long Beach: `PUBLIC WORKS/2021-2026 CONTRACT/PRA/WCA_Rates_2024-2025.pdf` contains WCA's rates already escalated through 3 renewal periods (2021→2024). This is the highest-value competitor benchmark available — it shows the incumbent's actual contractual pricing, not an estimate. Search the warehouse for `PRA/`, `*Rates*`, `*Fee Schedule*`, `*Schedule of Compensation*` under the current contract folder before falling back to manual CPI escalation from the original bid.
38. **Crown Raise bands must show SIZE PROGRESSION — do not flat-top the large bands.** Both crew-review judges (Kimi + Gemini) independently caught Crown Raise 24-30 and 31+ priced identically at $74.46 on Long Beach PW25-648 (2026-07-21). A 31"+ crown raise cannot cost the same as a 19-24". If the incumbent collapses bands (WCA uses 3 tiers: 0-12, 13-18, 19+), still split into 6 bands with proper progression — each band should step up ~15-20% over the prior. This is a recurring structural error pattern: the bid FORM asks for 6 bands, but if you copy the incumbent's collapsed pricing, you produce flat tops.
39. **Crew review $130 TPH rule — Gemini may misinterpret $130 as per-person billing rate.** On Long Beach PW25-648, Gemini flagged individual hourly rates ($109/hr per person) as "violating the $130 floor." This is WRONG: $130 is the crew-level fully-loaded cost floor (what a 3-person crew costs per hour total), NOT what each individual bills. The individual per-person rates are competitive positioning against WCA's $102/hr. The 3-person emergency crew rate ($502/hr = $167/person) clears $130 comfortably. When Gemini says "hourly rate is below $130," check whether it's a per-person rate or a crew rate before acting.
40. **Qualification-scored RFPs with cost = only 10/100 points: price to win but don't over-discount.** Long Beach PW25-648 scores Cost at 10 of 100 points (Method of Approach = 40, Org Capacity = 30, Communications = 20). Crew review (Kimi) correctly advised easing the volume-band discount from 8% to 6% on 13-18 and 19-24 (46.6% of inventory) because the 2% margin sacrifice buys negligible scoring benefit on a 10-point cost component. On qual-scored bids, protect margin on volume bands more than you would on a lowest-bid-wins IFB.
41. **DATA PROVENANCE DISCIPLINE — Brent will ask "where did this data come from?" for every column. (2026-07-22).** When Brent reviews a pricing tool deliverable, he traces each column to its source. If a column is computed, derived, or estimated, it must be labeled as such — not presented as if it were raw data. The spreadsheet must include source annotations or a "Data Sources" sheet documenting: (a) which columns come from the RFP packet, (b) which come from TRIM IT queries, (c) which come from warehouse competitor data, (d) which are computed/estimated by the pricing engine and the formula used. **A spreadsheet that can't pass a provenance audit is a trust failure.**
42. **INVENTORY TOTAL MUST MATCH THE CITY'S PRICING WORKSHEET — not a TRIM IT inventory query. (2026-07-22).** On Long Beach PW25-648, the v2 spreadsheet used 66,223 trees (from a TRIM IT inventory query) instead of the City's official Pricing Worksheet total of 87,229 trees. This caused: species omissions (Queen Palm #3 at 6,286 trees was missing), wrong volume distributions, and wrong annual production estimates. **ALWAYS use the tree counts from the city's own RFP Pricing Worksheet** (the PDF or XLSX in the RFP packet), NOT from TRIM IT InventoryDetail — the city's worksheet is the authoritative source for bid pricing because it's what the city's own analysis is based on. The TRIM IT inventory may differ due to project scoping, vacancy exclusions, or data-lag.
43. **NEVER merge deliverables from different build sessions without reconciling. (2026-07-22).** The Long Beach v2 tool was built across two sessions (July 17 and July 21) with different data sources, different inventory totals, and different species lists. The resulting spreadsheet had inconsistent sheets — the Cost Proposal used one data set, the Volume Analysis another. When updating or extending a deliverable from a prior session, **re-read every sheet and verify the data is consistent across all tabs** before sending. If the build script or data has changed, rebuild from scratch rather than patching on top of stale data.
44. **Spreadsheet generation is blind — verify the output before delivery. (2026-07-22).** I build spreadsheets via openpyxl (Python code that generates a file I never see). This causes: merged-cell crashes, wrong column widths, type-coercion bugs (numeric data stored as strings that crash sorting/formulas), and formatting that looks wrong to the human opening it. **Mitigation:** (a) after generating, re-read the file back with `openpyxl.load_workbook(path, data_only=True)` and print key cells to verify structure; (b) use `safe_num()` coercion on all data from external sources (xlsx values can come through as `#DIV/0!` strings); (c) avoid merged cells in data areas — they break `ws.cell(row, col).value` writes; (d) when Brent asks "where did this data come from," the answer must be specific and traceable, not "it was computed." The long-term fix is Google Sheets (live collaboration with visual verification) — pending Jason's approval.
45. **Brent audits column-level data provenance — label every column's source explicitly. (2026-07-22).** When Brent reviews a spreadsheet deliverable, he asks "where did Column X come from?" for each column. Every column must be traceable to a specific source: (a) RFP packet document, (b) TRIM IT SQL query, (c) warehouse competitor file, or (d) computed/estimated with the formula documented. Do NOT present computed estimates as raw data. If a column is an estimate (e.g., annual quantities derived from inventory share × annual cap), label it as such. **A spreadsheet that can't pass a column-by-column provenance audit is a trust failure.**
46. **TRIM IT UI proposal numbers are LegacyRef, NOT ProposalID. (2026-07-21).** When Brent gives a proposal number from the TRIM IT UI (e.g., "proposal 428345"), do NOT query `Proposals.ProposalID = 428345` — that returns the wrong proposal entirely. The UI displays `LegacyRef`, a sequential number separate from the database PK. Always: `SELECT * FROM Proposals WHERE LegacyRef = '<number>'`. Cross-verify by matching the project, description, and date Brent mentions.

## Email Attachment Pattern

Himalaya `template send` does NOT support `--attachment`. For file attachments, use Python SMTP:

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

msg = MIMEMultipart()
msg['From'] = 'bossherman.gsts@gmail.com'
msg['To'] = 'jwade@gstsinc.com'
msg['Subject'] = 'Subject here'
msg.attach(MIMEText(body, 'plain'))

with open(filepath, 'rb') as f:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment', filename=filename)
    msg.attach(part)

with open('/opt/data/.secrets/gmail-app.txt') as f:
    password = f.read().strip()
server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
server.login('bossherman.gsts@gmail.com', password)
server.send_message(msg)
server.quit()
```

## Challenger Pricing — When We're Not the Incumbent (2026-07-17)

**CRITICAL:** Before pricing, determine whether we HOLD the contract or are trying to WIN IT BACK. The pricing strategy is completely different.

### Determine incumbent status

1. Search the warehouse for `Notice of Intent to Award` or `Staff Report - Contract Award` — these name the winner
2. If TRIM IT shows active rates for us on that city/contract, we may still hold it — but verify the specific contract (Parks vs Public Works may be held by different companies)
3. **Ask the Skipper** if unclear — he knows who holds what

### If we are the CHALLENGER

The benchmark is the **incumbent's actual prior bid**, not our own current rates. Steps:

1. **Find the incumbent's CURRENT CPI-escalated rate card FIRST** — before escalating from the original bid. The warehouse often has the incumbent's already-escalated Schedule of Compensation in `PRA/` (Public Records Act) folders under the current contract. Example: Long Beach `PUBLIC WORKS/2021-2026 CONTRACT/PRA/WCA_Rates_2024-2025.pdf` has WCA's rates already escalated through 3 renewal periods. This is a far better benchmark than manually escalating a 5-year-old bid — it reflects actual contractual CPI adjustments, not estimates.
2. **If no current rate card exists, find the original bid** in the warehouse `Bid Results.xlsx` (preferred) or `Bid Results.pdf`. This shows both bidders' unit prices side by side.
3. **Inflation-adjust** to the bid year (if using the original bid, not the current rate card):
   - 5-year-old bid: multiply by ~1.19 (3.5% CPI/year)
   - 10-year-old bid: multiply by ~1.50-1.70
4. **Price 5-10% under** the escalated estimate on volume bands (bands driving >15% of revenue)
5. **Accept we may not beat them on every line** — price to win on the bands that drive 80%+ of revenue
6. **Lean on quality and track record** — RFPs are often qualification-weighted, not purely lowest-price

### Long Beach worked example

- WE held Public Works 2015-2021 (bid $29-129/tree)
- WCA took Public Works 2021-2026 (bid $44-174/tree — their actual bid from warehouse Bid Results PDF)
- WE still hold Parks & Rec (separate, higher rates)
- For 2027-2032 we are the CHALLENGER — must beat WCA's inflation-adjusted prices, not our own Parks rates

**Updated benchmark (2026-07-21 run):** WCA's current 2024-2025 CPI-escalated rate card found in warehouse `PRA/WCA_Rates_2024-2025.pdf` — Full Prune: $48/70/91/124/189/189 by band. This is the incumbent's ACTUAL current pricing (already escalated through 3 renewals), used directly as the challenger benchmark instead of manually escalating from the 2021 original bid. Full bid intel captured in `references/long-beach-pw25-648-challenger-bid.md`.

## DIR Prevailing Wage — Same Labor Costs for Everyone (2026-07-17)

**CORRECTION:** Municipal contracts with Davis-Bacon/DIR prevailing wage mean ALL contractors pay the same labor rates. There is NO labor cost advantage between bidders.

When you see a competitor's hourly rate (e.g., WCA bid $94/hr in 2021), that is their **TPH at that time** — their fully-loaded rate including overhead, equipment, and profit. It is NOT evidence of cheaper labor. Their TPH has risen alongside ours.

- WCA's $94/hr in 2021 ≈ our TPH from that era
- WCA's 2026 TPH is likely $110-130 — same range as our $130
- Do NOT assume "they have lower labor costs" — that is wrong on DIR jobs
- The only real cost differences between bidders are crew efficiency, route knowledge, and overhead structure

## Tool Scripts

This skill ships with three executable scripts in `scripts/` and `templates/`:

| Script | Purpose | Command |
|--------|---------|---------|
| `scripts/price_bid.py` | Prices all line items from competitor bids + Price Buddy signals | `/opt/data/.venv/bin/python scripts/price_bid.py --competitor-bids <.json> --signals <.json> --output <.json>` |
| `templates/generate_bid_spreadsheet.py` | Builds the 4-tab Excel deliverable from priced JSON | `/opt/data/.venv/bin/python templates/generate_bid_spreadsheet.py --priced <.json> --signals <.json> --output <.xlsx>` |
| `scripts/verify_no_blanks.py` | Verifies zero blank prices + Crown Raise/Stump complete | `/opt/data/.venv/bin/python scripts/verify_no_blanks.py <.xlsx>` |

See pitfall #22 for the full proven pipeline sequence. Also see `references/bid-engine-internals.md` for the JSON shapes and SQL queries that feed these scripts.

## Related

- **`references/long-beach-pw25-648-challenger-bid.md`** (this skill) — Full Long Beach PW25-648 challenger bid pattern: WCA current rate card location, pricing decisions, DBH revenue distribution, and the blended PB floor overstatement evidence. Updated 2026-07-21 after the complete bid run.
- **`references/price-buddy-grid-only-floor.md`** (this skill) — The grid-only PB cost floor method: why blended floors overstate cost, the 100+ WO filter query, and the `AvgBilledPrice` validation chain. USE THIS instead of the raw blended query.
- **`references/rfp-packet-extraction.md`** (this skill) — IMAP extraction of chunked Gmail RFP packets (Boss Herman's 3-part split), SHA-256 verification, and rejoin recipe. Use when the Skipper forwards "chunk N of 3" emails.
- **`references/pomona-ifb-2026-17-competitive-intel.md`** (this skill) — 7-bidder competitive matrix from Pomona Oct 2025; WCA pricing patterns + loss-leader anomalies; reusable for any SoCal muni bid against the same field.
- **`references/socal-muni-bidder-field.md`** (this skill) — the ~7 firms that bid every SoCal municipal tree contract (WCA, Golden West, Innovative, North Star, Mario's, Mariposa, GSTS). Their pricing signatures, the low-ball trap (Golden West), the loss-leader pattern (WCA small-tree Full Prune), and the ceiling reference (Mariposa). Consult before any new SoCal bid to predict the competitive floor.
- **`references/wca-benchmark-frequency-sheet.md`** (this skill) — pattern for adding a competitor invoice-history benchmark sheet to the bid deliverable: unit price history, quantities, revenue ranking, CPI escalation, and our-vs-their variance. Built when Brent provides a WCA/competitor invoice workbook.
- **`municipal-smart-bidding`** (gsts-operations) — the build/architecture skill (the tool itself: Pricing Brain, Bid Filler, Layer 1/2 design). This skill (`municipal-bid-pricing`) is the how-to-price methodology. They overlap and should eventually consolidate.
- `trim-it-operations` → `references/price-buddy-cost-floor.md` (cost floor derivation)
- `trim-it-operations` → `references/municipal-pricing-schema.md` (schedule of comp + canonical bands)
- `trim-it-operations` → `references/municipal-bid-warehouse.md` (warehouse map + extraction)
- `trim-it-operations` → `references/municipal-bid-extraction.md` (competitive range signal pipeline)
- **Crew review** — Kimi K3 + Gemini 3.1 Pro via `/opt/data/home/crew/{kimi,gemini}-ask.py` (API-key models, bind-mounted under MuniBot home). Guide: `/opt/data/home/crew/README.md`.
