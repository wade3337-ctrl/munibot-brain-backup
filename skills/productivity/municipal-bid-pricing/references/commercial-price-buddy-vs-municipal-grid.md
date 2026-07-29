# Commercial Price Buddy vs Municipal Grid Pricing

## Durable distinction

Price Buddy is based on GSTS historical **commercial** work. Municipal production is not apples-to-apples: street access, traffic control, parking, crew deployment, tree density, species mix, and cycle scheduling can materially change unit economics.

Use Price Buddy as a useful comparison signal, **not as a municipal hard floor or sole pricing authority**.

## Required bid-report comparison

For every standard DBH band, show:

| Field | Meaning |
|---|---|
| Commercial PB average | Historical commercial billing/reference rate |
| Commercial PB cycle reference | `AvgCycleTimeEach / 60 * yearly TPH` from commercial history |
| Municipal grid average billed | Actual average billing from municipal grid-cycle work |
| Municipal grid cycle reference | Cycle-time reference from municipal grid-cycle work |
| Spread $ | `Municipal grid average - Commercial PB average` |
| Spread % | `Spread $ / Commercial PB average` |
| Proposed bid | Current bid unit rate |
| Bid vs municipal grid | `Proposed bid - Municipal grid average` |
| Context | Explicitly state sources are different and comparison is reference-only |

The report caveat must say substantially:

> Price Buddy is based on historical commercial work. Municipal work usually differs; this comparison is useful for reference and is not a municipal hard floor.

## Municipal grid cohort

Use a separate municipal cohort rather than relabeling PB data:

1. `ProjectGroupDefID = 11` (municipal only).
2. Completed work-order lines (`StatusDefID = 68`), `Qty = 1`, pruning service class.
3. Work orders with at least 100 completed lines to isolate grid-cycle production from one-off service requests.
4. Prune/trim/thin service descriptions only.
5. Normalize TRIM IT size-code variants into the six standard DBH bands.

The `100+ lines` rule is a verified starting threshold, not an eternal truth. Report sample size by band and review the cohort if a future city's operating pattern indicates a different cutoff.

## Pricing decision hierarchy

Use multiple signals:

1. Incumbent's current actual rate card and escalation.
2. Target city's scope, inventory mix, annual cap, and operating constraints.
3. GSTS municipal grid average billing and sample size.
4. Commercial Price Buddy as a comparison/reference.
5. Crew review and explicit review flags for weak or conflicting signals.

Do not automatically clamp a municipal bid to the commercial PB cycle reference. If the bid falls below municipal grid history or another validated economic floor, flag it for review with the evidence rather than silently changing it.

## Tool implementation contract

The bid engine must produce separate fields for commercial PB and municipal grid data. The workbook must calculate dollar and percentage spreads and carry the caveat above. Validation should fail closed if the municipal comparison fields or report caveat are absent.

When changing this methodology, update all three layers in the same task:

1. `municipal-bid-pricing` procedure and this reference.
2. Atomic municipal knowledge vault.
3. Live bid-engine/output tool and its tests.

A tested staging copy is not deployment. Copy/promote the verified implementation to the live tool paths and run the live verification before reporting completion.
