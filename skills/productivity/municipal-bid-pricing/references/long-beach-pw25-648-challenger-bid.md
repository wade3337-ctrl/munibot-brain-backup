---
title: Long Beach PW25-648 Challenger Bid Pattern
type: reference
tags: [long-beach, challenger-bid, wca, bid-pricing, warehouse, grid-only-floor]
updated: 2026-07-21
---

# Long Beach PW25-648 — Challenger Bid Pattern

## Key Facts
- **City:** Long Beach, Department of Public Works
- **RFP:** PW25-648, As-Needed Tree Trimming & Related Services
- **Contract:** 2yr base + 3×1yr renewal (max 5yr)
- **Scoring:** Qualification-scored — Cost = only 10/100 points (Method=40, Org Capacity=30, Comms=20, Cost=10). Being cheapest does NOT win this.
- **Incumbent:** WCA (West Coast Arborists) — 2021-2026 contract
- **We are:** CHALLENGER. We held Public Works 2015-2021 but lost to WCA.
- **Inventory:** 87,229 street trees (92K city + 4K port). ~16,680 palms.
- **Annual cap:** 20,000 trees trimmed (incl 3,600 palms), 500 removals, 1,000 planted, 1,000 watered.

## WCA Benchmark Sources (Warehouse)
- **Current rates (2024-2025):** `/PUBLIC WORKS/2021-2026 CONTRACT/PRA/WCA_Rates_2024-2025.pdf` — CPI-escalated through 3 renewal periods. PRIMARY BENCHMARK. Text PDF, 3 pages.
- **2021 original bid:** `/PUBLIC WORKS/2021-2026 CONTRACT/WORKING FILES/Bid Results.xlsx` — WCA vs GSTS side-by-side, pre-escalation. Single sheet "BID RESULTS", 46 lines.
- **WCA proposal:** `/PUBLIC WORKS/2021-2026 CONTRACT/PRA/WCA_Proposal_RFP_PW-20-032.pdf`
- **WCA invoices (PRR):** `/PUBLIC WORKS/2021-2026 CONTRACT/PRA/Invoices/` — summary-level register XLSX + individual invoice PDFs in Archived/Other/.

## WCA Pricing Patterns
- WCA charges the SAME rate for all 3 hourly roles (Ground/Equip/Trimmer): $102.15/hr (2024-25)
- WCA collapses Crown Raise bands: 0-12, 13-18, 19+ (3 tiers instead of 6)
- WCA Full Prune 24-30 = 31+ at same rate ($189.05) — flat top structure
- WCA Emergency: same rate day/night ($469.50/hr crew rate = ~$156/person)
- WCA Trunk Clean: same rate for Date and Fan ($58.70/ft)
- WCA 2021 → 2024 escalation was roughly +8%/year cumulative across 3 CPI periods

## WCA 2024-2025 Rate Card (from PRA, verified)
| Line Item | WCA Rate |
|-----------|----------|
| Full Prune 0-6 | $47.80 |
| Full Prune 7-12 | $69.55 |
| Full Prune 13-18 | $91.30 |
| Full Prune 19-24 | $123.85 |
| Full Prune 25+ | $189.05 |
| Raise/Clearance 0-12 | $36.95 |
| Raise/Clearance 13-18 | $53.25 |
| Raise/Clearance 19+ | $69.55 |
| Date Palm Prune | $189.05 |
| Fan Palm Prune | $91.30 |
| Other Palm Prune | $69.55 |
| Palm Trunk Clean (any) | $58.70/ft |
| Service Request Prune | $515.10 |
| Removal 0-6 | $156.50 |
| Removal 7-12 | $384.70 |
| Removal 13-18 | $710.70 |
| Removal 19-24 | $949.80 |
| Removal 25-30 | $1,069.35 |
| Removal >30 | $1,188.90 |
| Stump 0-6 | $80.40 |
| Stump 7-12 | $102.15 |
| Stump 13-18 | $134.75 |
| Stump 19-24 | $189.05 |
| Stump 25-30 | $210.85 |
| Stump 31+ | $243.40 |
| Hourly (all roles) | $102.15 |
| Crew Rental | $296.40/hr (= $2,371/day) |
| Emergency Response | $469.50/hr |
| Arborist / Pest | $167.35 |
| Qualified Applicator | $123.85 |
| Plant 15gal | $189.05 |
| Plant 24" box | $395.55 |
| Plant 36" box | $1,036.75 |
| Plant 48" box | $1,906.15 |
| Plant Fan Palm (lump) | $2,123.45 |
| Plant Fan Palm (per ft) | $156.50 |
| Tree Watering | $817.20/day |

## 2027 Escalation
WCA rates above are from April 2024. For 2027 bid, project 2 more years at 3.5% CPI: × 1.0712.

## Price Buddy Cost Floor — Grid-Only (verified 2026-07-21)

The blended PB floor (all qty=1 WO lines) massively overstates mid-band cost. The grid-only variant (WOs with 100+ completed lines, municipal projects only, N=48,379) gives the real picture:

| Band | Blended Floor | Grid-Only Floor | Our Avg Billed | Our Bid |
|------|:---:|:---:|:---:|:---:|
| 0-6 | $44 | $84 | $42 | $47 |
| 7-12 | $104 | $132 | $67 | $69 |
| 13-18 | $221 | $143 | $73 | $92 |
| 19-24 | $279 | $187 | $94 | $125 |
| 24-30 | $162 | $240 | $121 | $186 |
| 31+ | $151 | $280 | $133 | $186 |

**Every bid price is above our own average billed price.** The formula floor overstates cost because it captures travel/setup/non-productive time. See `references/price-buddy-grid-only-floor.md` for the full query.

## Pricing Decisions Applied
- Volume bands (13-18, 19-24, 24-30): 6-8% under WCA 2027 estimate
- Low-volume bands (0-6, 31+): 5% under (protect margin)
- Premium lines (hourly, emergency, arborist): at WCA escalated parity
- Single tree: 5% ABOVE WCA (adverse selection protection)
- Crown Raise: split WCA's collapsed tiers into 6-band progression
- Crew review caught: flat Crown Raise 24-30/31+ → fixed with progression ($93/$112)

## DBH Band Revenue Distribution
| Band | Inventory | % | Annual Trim | Revenue Weight |
|------|-----------|---|-------------|----------------|
| 0-6 | 5,606 | 6.4% | ~1,317 | Low |
| 7-12 | 15,667 | 18.0% | ~3,682 | Medium |
| 13-18 | 21,590 | 24.8% | ~5,073 | **HIGH** |
| 19-24 | 19,054 | 21.8% | ~4,476 | **HIGH** |
| 24-30 | 22,603 | 25.9% | ~5,314 | **HIGHEST** |
| 31+ | 2,709 | 3.1% | ~637 | Low |

13-18 + 19-24 + 24-30 = **71.3% of inventory**. These 3 bands determine whether we win.

## Crew Review Catches (2026-07-21)
Both Kimi K3 and Gemini 3.1 Pro independently caught:
1. **Crown Raise 24-30 and 31+ flat at $74.46** → Fixed: $93.00 / $112.00 (progression needed)
2. **Full Prune 13-18 and 19-24 too thin** → Fixed: eased discount from 8% to 6% ($91.93 / $124.71)

Gemini also flagged hourly rates ($109/hr) as violating $130 TPH — **overruled**: $130 is crew-level cost floor, not per-person billing rate. The 3-person emergency crew ($502/hr = $167/person) clears $130.
