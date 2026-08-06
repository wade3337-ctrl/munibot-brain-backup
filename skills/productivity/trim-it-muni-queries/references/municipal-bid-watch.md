# Municipal Bid and Renewal Watch

Use this when asked which cities are going out to bid soon.

## Core distinction

Keep three statuses separate:

1. **Confirmed open solicitation** — an official city procurement source publishes a title, issue date, due date, and link.
2. **Likely near-term bid/renewal watch** — TRIM IT shows an approaching/expired contract or missing new-FY budget, but no official open posting is verified.
3. **PO/extension follow-up** — a budget is missing or `PONumber` is `TBD`; this may be an annual authorization issue rather than a competitive rebid.

Never turn an internal expiration or blank budget into a claim that a city is definitely going to bid.

## Internal screening

1. Scope to `ProjectGroupDefID = 11`, Approved, non-homeowner contracts.
2. Inspect all approved contract components per city.
3. Capture contract start/end dates, PO numbers, and all five FY label/budget pairs.
4. Rank cities with:
   - expired contract and no new-FY budget;
   - contract ending within 12 months;
   - missing new-FY budget or `TBD` PO;
   - invalid placeholder dates requiring external verification.
5. Reduce false alarms:
   - a separate approved component may carry the new-year budget;
   - an entered new-FY budget/PO can indicate an extension even when another row's end date has passed;
   - annual PO gaps do not necessarily mean the underlying multi-year contract is rebidding.

## Public-source verification

Search official sources first:

- city bids/RFP page;
- PlanetBids, Public Purchase, OpenGov, BidNet, or the city's named vendor portal;
- City Council agendas, staff reports, minutes, and award/extension amendments;
- procurement and public-works pages.

For each claimed open bid, verify:

- exact scope/title;
- issuing city;
- publication date;
- questions/pre-bid date if applicable;
- submission deadline;
- official URL;
- whether the opportunity is open, closed, awarded, extended, or archived.

Search-engine snippets and third-party bid aggregators are leads, not final proof. Dynamic procurement portals may not index cleanly; say when no official open posting was found rather than claiming none exists.

## Reporting format

Use a confidence-ranked table:

| Priority | City | Internal signal | Public evidence | Status / expected window |
|---|---|---|---|---|

Then state clearly:

- **Confirmed currently open bids**;
- **Immediate renewal/procurement investigations**;
- **6–12 month watchlist**;
- **Not expected soon**, with contract horizon.

Use explicit dates and an as-of date. If timing is inferred from expiration, label the window **estimated**, not confirmed.
