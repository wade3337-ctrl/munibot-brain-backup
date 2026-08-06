# Orange County Public-Sector Tree Bid Scan

Use this reference for broad geographic searches beyond Great Scott's existing TRIM IT municipal accounts. It supplements `municipal-bid-watch.md`; it does not replace official solicitation verification.

## Coverage ladder

Search in this order:

1. **Orange County and OC Parks** — County Procurement/OpenGov.
2. **All Orange County cities** — each city's official bids/RFP page and its linked vendor portal.
3. **Large public agencies** — OCTA/CAMMNET, OC San/PlanetBids, water districts, cemetery districts, and joint powers authorities.
4. **School districts and OCDE** — district purchasing and facilities bid pages.
5. **Third-party aggregators** — BidNet, California Bid Network, ConstructConnect, etc., only to discover leads.

Useful official entry points include:

- County of Orange: `https://cpo.oc.gov/open-bids-county-contracts-portal`
- City of Orange: `https://www.cityoforange.org/business/current-bids-proposals`
- Santa Ana: `https://www.santa-ana.org/bidding-information/`
- Laguna Beach: `https://www.lagunabeachcity.net/do-business-here/rfps-bids`
- Mission Viejo: `https://www.cityofmissionviejo.org/government/request-proposals-bid-opportunities`
- Rancho Santa Margarita: `https://www.cityofrsm.org/171/Bids-Request-For-Proposals`
- Placentia: `https://www.placentia.org/890/Bids-RFPs`
- OCTA: `https://cammnet.octa.net/procurements/`
- OC San: `https://www.ocsd.com/businesses/bids-and-rfps`

## Search vocabulary

Run multiple searches because agencies classify the same work differently:

- tree maintenance, tree trimming, tree pruning, tree removal;
- arborist, urban forestry, stump grinding, root pruning;
- landscape maintenance, vegetation management, fuel modification;
- emergency tree services, line clearance, right-of-way maintenance.

Search exact titles in quotes after discovering a lead. Add the city/agency name, solicitation number, year, and `site:` restriction.

## Verification discipline

A lead is **confirmed open** only when an official source or the issuing agency's vendor portal establishes:

- issuing agency;
- solicitation number/title;
- scope relevant to tree care;
- publication date;
- closing date and time;
- status still open as of the report date;
- official link or portal path.

Do not treat these as proof:

- a search result labeled “open bids” without a visible closing date;
- a third-party page hiding the buyer behind login;
- an archived CivicEngage bid page;
- a current city bid index that surfaces an old tree solicitation;
- a landscape contract that mentions only incidental pruning.

When an official PDF is available, extract and verify it directly. One practical pattern is:

```bash
curl -L --fail --silent --show-error 'OFFICIAL_PDF_URL' -o /tmp/solicitation.pdf
uv run --with pypdf python - <<'PY'
from pypdf import PdfReader
text='\n'.join((p.extract_text() or '') for p in PdfReader('/tmp/solicitation.pdf').pages)
print(text)
PY
```

Check the cover page, tentative schedule, addenda, and scope. A posting can remain indexed after its deadline.

## Reporting categories

Report in four explicit buckets:

1. **Confirmed open and actionable**
2. **Closing soon / addendum risk**
3. **Recently closed or award pending**
4. **Watchlist only — no confirmed posting**

If the scan finds no verified open opportunities, say exactly that. Also list recent closed solicitations and login-only portals checked so the result is useful without overstating completeness.

## Session benchmark — 2026-07-15

A broad Orange County scan found no additional confirmed open municipal tree-maintenance solicitation. Useful false-positive examples:

- **Brea RFP 26-02 Landscape Maintenance Services** closed May 14, 2026; the official 62-page RFP showed only a small amount of tree pruning, so it was related but not a direct tree-maintenance opportunity.
- **Yorba Linda Citywide Tree Maintenance Services** was an archived posting that closed October 1, 2024 despite appearing in current search results.
- **La Habra Heights Tree Trimming Maintenance Services** had already closed April 1, 2026.
- A California Bid Network “Tree Pruning and Removal Services” lead hid the buyer/location and could not be verified as Orange County; it was excluded.

Treat this benchmark as historical evidence, not current opportunity status. Re-run the official portals for every new request.
