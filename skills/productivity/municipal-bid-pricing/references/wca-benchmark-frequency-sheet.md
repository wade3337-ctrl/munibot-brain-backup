# WCA/Incumbent Benchmark & Frequency Sheet

Pattern for adding competitor invoice-history data as a sheet in the bid pricing deliverable.

## When to build this

When Brent provides a competitor invoice-history workbook (e.g., `WCA Invoicing.xlsx` from a PRA/municipal-invoice-history-sop build). This is a **reference data layer** in the pricing tool, NOT part of the invoice-history SOP workflow — they are separate.

## What the sheet shows

| Section | Content |
|---------|---------|
| **Unit Price History** | FY22-23, FY23-24, FY24-25 prices per line item |
| **Annual Quantity** | How many of each item WCA actually billed per year |
| **Extended Totals** | Revenue per line item per year |
| **3-Year Average** | Avg qty, avg % of total work, avg revenue |
| **Our Price** | Matched to our bid pricing; variance % flagged (red/green) |
| **Revenue Rank** | Every line ranked by avg revenue — #1 = biggest money maker |
| **Strategic Notes** | Auto-flagged: `*** TOP REVENUE DRIVER ***` for >$100K/yr avg |
| **CPI Escalation Analysis** | Year-over-year escalation % per item, 2-yr avg |

## Key findings pattern (Long Beach example)

Top revenue items by 3-yr avg:
1. Full Prune 25+ DSH: $750K/yr (28.4% of work)
2. Service Request Prune: $343K (13.0%)
3. Full Prune 19-24 DSH: $270K (10.2%)
4. Crown Reduction Prune: $192K
5. Removal >30 DSH: $132K

These are the **must-get-right** items when pricing — they drive 70%+ of contract revenue.

## Implementation notes

- Uses openpyxl to build the sheet and insert it at position 1 (after Cost Proposal)
- Merged cells for group headers require care — don't write to merged cell ranges at row 4
- WCA data may contain `#DIV/0!` strings for FY25-26 (no data yet) — use `safe_num()` coercion
- Match our prices to WCA line items by keyword pattern (full prune + DBH band, palm species, etc.)
- Revenue rank sorted by `avg_total` column descending
- CPI escalation: `(p2-p1)/p1` year-over-year, flag if >5%

## Related
- The Municipal Invoice History SOP (`/opt/data/home/municipal-knowledge/references/municipal-invoice-history-sop.md`) — how to BUILD the WCA workbook from PRA productions
- This reference — how to USE it in the pricing deliverable
- These are separate workflows (Brent's directive 2026-07-21)
