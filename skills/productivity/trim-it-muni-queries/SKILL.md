---
name: trim-it-muni-queries
description: "Use when querying Great Scott Tree Care's TRIM IT database for municipal (Track-1) data — city customers, contract budgets, invoicing, PO tracking, GPS tree inventory (InventoryDetail), pruning-cycle analysis, Schedule of Compensation rate cards, cost estimation, city contact discovery, outreach email drafting, and downloading project attachments (Base Maps, Specialty Maps, images) from TRIM IT storage. Covers the read-only SQL query mechanism, verified query patterns, the PO-gated-budget data quirk, the Maps/attachments table and bulk-download workflow, and known data-hygiene pitfalls (duplicates, typos, department fragmentation)."
version: 1.8.0
author: Muni Bot
license: MIT
metadata:
  hermes:
    tags: [trim-it, municipal, tree-care, read-only-query, po-gated-budgets, brent-beller, sql]
    related_skills: []
---

# TRIM IT Municipal Queries (Great Scott Tree Care)

## Overview

Brent Beller (Contract Admin, TRIM IT UserID 40) owns the municipal budgets in **TRIM IT**, Great Scott Tree Care's operational system. Muni Bot reads TRIM IT **read-only** to answer municipal questions: which cities we serve, contract budgets, invoicing, renewals, and the PO-pending gap.

The municipal segment is identified by `ProjectGroupDefID = 11`. The knowledge base lives at `~/home/municipal-knowledge/` — read it when available; this skill captures the verified query layer and the data-quality rules that govern interpretation.

## When to Use

- Brent asks about municipal customers, city budgets, contract amounts, invoicing, or renewals.
- Comparing a TRIM-IT-sourced municipal total against an outside report (Nate's Sales Report, Brent's Excel).
- Building a budget/PO tracking view or forecasting artifact for municipal work.
- Identifying cities that need PO or renewal follow-up for a new fiscal year. Use `references/po-follow-up-identification.md`; aggregate **all approved contract components per city** before assigning city-level status.
- Building a municipal bid watchlist. Use `references/municipal-bid-watch.md`; distinguish a confirmed official open solicitation from an internally inferred renewal/expiration watch item.
- Scanning broadly for Orange County public-sector tree opportunities beyond existing TRIM IT customers. Use `references/orange-county-public-bid-scan.md`; cover cities, County/OC Parks, public agencies, and school districts, and verify every lead against an official source.
- Measuring average field staffing on municipal work. Use `references/municipal-workforce-headcount.md`; validate named assignment coverage and report an hours-supported equivalent headcount when assignments do not reconcile to actual attendance.
- **Querying a city's GPS tree inventory** — per-tree census data (lat/long, species, DBH, zone/district/area, pruning cycle, condition, maintenance scheduling). Use `references/inventory-gps-tree-census.md`; the tree records live in `InventoryDetail` (274 columns, ~1.79M rows company-wide), scoped by `ProjectID`. Pruning-cycle year assignment is the `PruningFrequency` column (integer year, e.g. 2024).
- **Pulling a city's Schedule of Compensation** — the per-service, per-size rate card (pruning by DBH, palm trimming by species, removal + stump grinding by DBH, planting by container size). Lives in `LocationServiceTypes`, reached via `Locations.ProjectID` → `LocationID`. See `references/inventory-gps-tree-census.md` § Schedule of Compensation.
- **Estimating pruning costs for a scoped tree set** (district + cycle year). Join `InventoryDetail` to `LocationServiceTypes` to produce a per-size cost breakdown. Exclude "Vacant Site" records (`SizeCode = '---'`). See `references/inventory-cost-estimates-and-contacts.md` § Pruning Cost Estimate.
- **Finding a city contact and drafting outreach email** — city contacts live in `Contacts` (note: `email` not `EMail`, `PrimaryPhone` not `Phone`). Emails with budget updates, cycle proposals, and cost estimates follow a standard structure. Draft for Brent's approval; never send external email autonomously. See `references/inventory-cost-estimates-and-contacts.md` § City Contact Discovery and § Email Drafting Workflow.
- Any "what's the story with City X?" question on the Track-1 (municipal) side.

- **Analyzing commercial-contract proposals** (Irvine Company and similar formal-contract accounts Brent manages). Extract species breakdowns, tree counts, and property-level analysis from `Proposals` → `ProposalLines` → `InventoryDetail`. Use `references/commercial-contract-proposals.md`; compartmentalize from municipal — different segment, different CompanyIDs, never mix in reports or totals.

- **Downloading project attachments (Base Maps, Specialty Maps, images, documents).** TRIM IT stores all project attachments in `dbo.Maps`, keyed by `LocationID` (NOT `ProjectID`, which is NULL). The `ImagePath` column holds directly-downloadable HTTP URLs (`https://www.greatscotttreeservice.com/gsts/Storage/Data/{LocationID}/<file>.pdf`) — no auth header needed, just URL-encode spaces. Filter sub-tabs: Base Maps = `IsBaseMap = 1`, Specialty Maps = `IsRemovalMap = 1`, Images = `RecordType = 'Image'`, Other = `RecordType = 'Attachment'`. See `references/maps-and-attachments.md` for the full bulk-download workflow, the sub-tab-to-flag mapping, UNC-path pitfalls, and the Irvine Company Retail Portfolio as a worked example (201 base maps, 39 projects, 247 MB).

- **Querying company-level contracts.** When Brent asks "how many company contracts do I have?" or wants a contracts overview table, query `dbo.CompanyContracts` joined to `Companies` and `StatusDefs`. The table has 146 rows with 7 status types (Approved, Archived, Inactive, InProcess, Deleted, Not Approved, Pending). No `ProjectID` column — these sit above projects. See `references/company-contracts.md` for schema, status codes, query patterns, and the CSV-delivery workflow.

- **Researching litigation disclosure for bid support.** When Brent is preparing a municipal bid (OCTA, Riverside, etc.) and needs to identify contracting agency ties for litigation history, research public court records to fill in the agency column. Use `references/litigation-disclosure-research.md`; includes the legacy `.doc` extraction technique (olefile in a temp venv), the OC vs LA County court records searchability gap, and verified search approaches (DocketAlarm, DocketBird, news coverage, granicus bid protests).

- **Pricing a municipal bid / RFP cost proposal.** Use the `municipal-bid-pricing` skill — it runs `bid_engine.py` (which queries TRIM IT for Price Buddy cost floors and current rates) and `competitor_extractor.py` (which parses competitor bid PDFs from the warehouse), then generates a priced cost-proposal spreadsheet. This skill provides the underlying TRIM IT data; the bid-pricing skill orchestrates the full workflow.

- **Building a competitor invoice-history report from PRA productions** (for cities where we are NOT the incumbent). This is a separate, standalone workflow from the Pricing Tool. It takes raw public-records invoice PDFs from the competitor/incumbent and produces a multi-year invoice-history workbook showing price trends, quantities, and frequency by line item. See the vault note `references/municipal-invoice-history-sop.md` (in `/opt/data/home/municipal-knowledge/`) for the full 17-phase process and the Long Beach/WCA case study. **⚠ BRENT'S DIRECTIVE: keep this workflow SEPARATE from the Pricing Tool — do not merge.**

**Do not use for:**
- Track-2 / arbor-core / BLACK material — out of scope, never surface it.
- Writes to TRIM IT — the connection is read-only (verified: `CREATE TABLE` → permission denied).
- General commercial (one-off HOAs, one-shot jobs) — only Brent's formal contracted commercial accounts (e.g. Irvine Company) are in scope.

## The Query Mechanism

Pipe SQL on stdin to the read-only wrapper:

```bash
echo "SELECT ... ;" | /opt/data/home/trimit-query.sh
```

**Path note:** the script lives at `/opt/data/home/trimit-query.sh`. Do NOT write `~/home/trimit-query.sh` — with `$HOME=/opt/data`, `~/home/` expands to `/opt/data/home/home/` which does not exist. Always use the absolute path or `$HOME/home/trimit-query.sh`.

The script SSHes into the TRIM IT play replica (~24h behind live) with BatchMode and StrictHostKeyChecking=accept-new. **Read-only.** Writes are denied and have been verified denied.

Output is pipe-delimited (`|`) with a header row, e.g. `CompanyID|PublishedName`. Parse accordingly.

## Verified Query Patterns

See `references/muni-query-patterns.md` for the full catalog and `references/po-gap-reconciliation.md` for the repeatable city-by-city reconciliation workflow. Core queries:

- **City customers:** `SELECT CompanyID, PublishedName FROM gsts.dbo.Companies WHERE PublishedName LIKE '%City of%' ORDER BY PublishedName;`
  - ⚠️ The name column is **`PublishedName`**, not `CompanyName`. Using the wrong column returns nothing.
- **A city's contract budget:** contracts have five label/budget pairs—`Year01Label`/`Year01Budget` through `Year05Label`/`Year05Budget`. Match the requested fiscal-year label across those pairs; there is no `Year26Budget` convention. Scope to Approved contracts (`StatusDefID = 287`), exclude `PONumber = 'Homeowner'`, and join through `ProjectGroups` with `ProjectGroupDefID = 11`.
- **Cities needing PO/renewal follow-up:** normalize the year-label pairs, then aggregate **all approved contract components at city level**. Do not keep only the newest contract: Cypress and Long Beach demonstrated that an older approved component can carry the new-FY budget even when the newest row does not. Missing new-FY budget is a follow-up signal, not definitive proof that a PO is outstanding. See `references/po-follow-up-identification.md`.
- **Invoiced by FY:** sum `InvoiceMasters` grouped by `ProjectYearLabel`.
  - ⚠️ The invoice total column is **`Total`**, not `Amount`. Using `Amount` returns `Invalid column name 'Amount'`.
  - Other useful `InvoiceMasters` columns: `InvoiceDate`, `TotalHours`, `TPH` (target $/hr), `Desc1` (invoice description), `StatusDefID` (297 = posted/approved).

## The PO-Gated Budget Rule (critical interpretation rule)

**Brent does not enter a municipal contract budget into TRIM IT until the PO is issued.** A contract effectively won/renewed but whose PO hasn't landed has **no budget row, or a stale/zero one**, in TRIM IT.

**Consequence:** municipal totals in any TRIM-IT-sourced view **understate reality** until POs come in. This is a deliberate data-entry policy — not a dashboard bug, not Nate over-counting.

Confirmed benchmark (2026-07-14):
- SPM Classic-View muni (entered allocations): **$6.62M**
- Nate's Sales Report: **$8.75M**
- Gap (unbudgeted / PO-pending): **~$2.14M**
- Commercial reconciled to the dollar — the entire gap is municipal.

**Rule of thumb:** when a municipal number from TRIM IT is *lower* than an outside report, suspect **un-entered PO-pending budgets first**. Flag the gap and point to City Budgets → Renewals. **Never fabricate a budget** to make a total look complete. This gap is exactly what Muni Bot's budget/PO tracking targets.

## Data-Hygiene Pitfalls (discovered in city-customer pull)

The `Companies` table is messy. A raw `LIKE '%City of%'` returns **233 rows** but the true distinct-city count is ~180. Before reporting a customer list or counting cities, de-duplicate and classify:

1. **Duplicate CompanyIDs per city.** Same city, multiple rows from trailing whitespace or re-imports. Examples: Bellflower ×2, Covina ×2, Corona ×2, Irvine ×2, Pasadena ×2, La Puente ×3, Lake Forest ×3+. Normalize by stripping whitespace and matching on the base name.
2. **Department sub-rows.** One city split across divisions, each with its own CompanyID. **San Diego** is the worst — ≥8 rows (Parks, Libraries, Water Ops, Crew, Broadleaf, Palms, + base rows). Anaheim, Long Beach, LA, and Compton show the same pattern. When summing a city's totals, you must aggregate across all its sub-rows or you'll undercount.
3. **Typos creating phantom cities.** "Alsio Viejo" is a duplicate of Aliso Viejo. Flag, don't report as distinct.
4. **Phrasing variants.** "Los Angeles, City of" (reversed word order) is the same city as "City of Los Angeles" and carries LA's department sub-rows (Airports, Recreation & Parks, Urban Forestry).
5. **Junk/test rows.** e.g. `ZZZ=== CITY OF CARSON ===` and an Andrew Hamilton council-member contact row — filter these out.
6. **Ambiguous short names.** "City of Newport" may be Newport Beach or a truncated entry — verify before treating as distinct.

When a clean master list is needed, produce one that: collapses duplicates, rolls department sub-rows under their parent city, flags typos/junk, and notes which cities are fragmented.

## Common Pitfalls

1. **Using `CompanyName` instead of `PublishedName`.** The customer-facing name lives in `PublishedName`. The wrong column silently returns zero rows.
2. **Reporting a raw row count as the city count.** 233 ≠ 180. Always de-duplicate first (see Data-Hygiene above).
3. **Summing a fragmented city across only one of its CompanyIDs.** San Diego/LA/Anaheim totals will be wrong unless you aggregate all sub-rows.
4. **Taking a TRIM-IT municipal budget total at face value.** It understates reality due to PO-gating. Cross-check against Nate's Sales Report or Brent's Excel before declaring a number final.
5. **Fabricating a budget to fill a gap.** Never. Report the gap and its cause instead.
6. **Forgetting `ProjectGroupDefID = 11`** when filtering to the municipal segment — without it you pull commercial and other segments too.
7. **Using only the newest contract to decide whether a city needs a PO.** Cities can have several simultaneous approved components; aggregate every approved component for the requested FY before assigning city-level status. Track component-level blanks separately.
8. **Calling a missing budget a confirmed outstanding PO.** PO-gating makes it a strong follow-up signal, but award/renewal status still requires an authoritative renewal tracker, correspondence, or PO source.
9. **Using sparse `CrewAssignments` as actual municipal headcount.** First reconcile positive assignment coverage against `CrewMemberCalendars`. If coverage is materially incomplete, use municipal completed crew-hours divided by actual hours per worker-day and label the result an equivalent daily headcount—not a named-person count.
10. **Trying to write.** The connection is read-only and verified read-only. Don't attempt INSERT/UPDATE/CREATE.
11. **Using `Amount` instead of `Total` in `InvoiceMasters`.** The invoice total column is `Total` — `Amount` does not exist. Same wrong-column trap as `CompanyName` vs `PublishedName`. When a table's column name errors out, `SELECT TOP 1 *` to inspect the real schema before guessing again.
12. **Querying `Inventories` for per-tree data.** `Inventories` is a summary/header table and is typically empty even when a project has thousands of trees in `InventoryDetail`. Always go to `InventoryDetail` for individual tree records.
13. **Using `CurrentYear` for pruning-cycle queries.** `CurrentYear` is NULL across all trees. The pruning-cycle year lives in **`PruningFrequency`** (integer year, e.g. 2024). See `references/inventory-gps-tree-census.md`.
14. **Filtering inventory by `DistrictRef` text label.** The text label (e.g. "EAST", "WEST") is only populated on ~25% of rows. The other ~75% have blank/NULL `DistrictRef` but still belong to the correct `DistrictID`. **Always filter on `DistrictID` (the integer FK)**, never on `DistrictRef` text, or you'll silently drop most of the district.
15. **Looking for the Schedule of Compensation in pricing tables.** `PricingSizes`, `PricingGroupRates`, and `InventoryPricingHistory` exist but may be empty. The rate card lives in **`LocationServiceTypes`**, reached via `Locations.ProjectID` → `LocationID`. See `references/inventory-gps-tree-census.md` § Schedule of Compensation.
16. **Including "Vacant Site" records in cost estimates.** Trees with `SizeCode = '---'` and `SpeciesRef = 'Vacant Site'` are empty planting sites (DBH = 0). They won't join to any rate on the Schedule of Compensation and will silently inflate your tree count without adding cost. Exclude them from cost estimates and flag them separately as planting opportunities. See `references/inventory-cost-estimates-and-contacts.md` § The "Vacant Site" pattern.
17. **Using wrong column names in `Contacts` table.** The column is `email` (not `EMail`), `PrimaryPhone` (not `Phone`), `ContactTitle` (not `Title`). Same wrong-column pattern as `CompanyName` vs `PublishedName` and `Amount` vs `Total`. When in doubt, `SELECT name FROM syscolumns WHERE id = OBJECT_ID('gsts.dbo.<table>')`.
18. **Sending external email without Brent's approval.** The SEND-GATE is absolute: anything outbound to a person (Brent, a city contact, anyone) is drafted for approval first. Self/test mail is fine. See `references/inventory-cost-estimates-and-contacts.md` § Email Drafting Workflow.
19. **Letting the knowledge vault drift from the skill.** The vault (`/opt/data/home/municipal-knowledge/`) and the skill's `references/` must stay in parity. When you add or update knowledge in one, mirror it to the other. See § Knowledge Vault Sync Protocol below. The vault path has the same `~/home/` expansion trap as the query script — always use the absolute path `/opt/data/home/municipal-knowledge/`.
20. **Trusting pasted Proposal IDs from Brent's email.** **SOLVED:** The TRIM IT UI displays the **`LegacyRef`** column as the proposal number, NOT `ProposalID`. The two are completely different sequences (UI shows ~420K–428K; DB `ProposalID` is ~780K–802K). Always look up by `WHERE LegacyRef = '<UI number>'` first. If not found (may be too new for the ~24h-behind replica), fall back to `Desc1 LIKE '%<keyword>%'`. See `references/commercial-contract-proposals.md` § The Proposal ID Mismatch.
21. **Emailing anyone other than Brent or Jason.** Brent's directive (2026-07-15): only send email when explicitly asked, and only to Brent (bbeller@gstsinc.com) or Jason. No external emails to cities, contacts, or anyone else — even after a draft is approved. Brent sends external emails himself. See `references/inventory-cost-estimates-and-contacts.md` § Email restriction rule.
22. **Forgetting the `--config` flag on himalaya.** The config is at `/opt/data/.config/himalaya/config.toml`, not the default `~/.config/himalaya/`. Always run: `himalaya --config /opt/data/.config/himalaya/config.toml <command>`.
23. **Mixing commercial-contract data into municipal reports.** Irvine Company and other commercial-contract work is in scope but must be compartmentalized. Different segment, different CompanyIDs, never mix in reports or totals. See `references/commercial-contract-proposals.md`.
24. **Expecting OC court records to be web-searchable.** Orange County Superior Court cases (`30-` prefix) are NOT indexed by Google, DocketAlarm, UniCourt, or DocketBird. Web searches for these case numbers return zero results. LA County cases (`22STCV`, `24LBCV`) ARE indexed. For OC cases, use the court's portal at `occourts.org/online-services/case-access` or tell Brent honestly what couldn't be verified. See `references/litigation-disclosure-research.md`.
25. **Ignoring legacy `.doc` email attachments.** When Brent emails a `.doc` (binary OLE format, not `.docx`) and no office tools are installed, use `olefile` in a temp venv to extract readable text. The technique is in `references/litigation-disclosure-research.md` § Legacy .doc extraction. Don't skip the attachment or ask Brent to reformat — just extract it.
26. **Substituting one entity's data as a proxy for another.** If a city's invoice data doesn't exist in TRIM IT, flag the gap and report it as missing. NEVER use invoicing from a "similar city" to estimate frequency, volume, or any metric. Each entity's data stands on its own. This is a hard rule from Brent (2026-07-17). Same principle as PO-gating: report the gap, never fabricate.
27. **Using the ImagePath filename when sending files.** `Maps.ImagePath` stores the GSTS storage URL (e.g. `Revised Colored Map.pdf`), which does **NOT** match `Maps.Desc1` (the TRIM IT display name, e.g. "2016 Arcview Base Map"). When emailing attachments, rename files using `Desc1` + project name so Brent can identify them. **Always ask Brent about preferred naming BEFORE sending** — his default is `[ProjectName] - [Desc1].pdf`, alphabetically sortable. (Brent's directive, 2026-07-17.)
28. **MML attachment/body mismatch.** When building multipart emails with `himalaya template send`, each `<#part filename="...">` tag must point to the exact file described in the body text. If the loop that builds MML parts iterates over a different list than the body-text list, recipients get wrong attachments. Verify file paths in MML parts match the body list before sending.
29. **Joining `Maps` via `ProjectID` instead of `LocationID`.** The `Maps` table has a `ProjectID` column but it is **NULL for every row**. Joining `Maps.ProjectID = Projects.ProjectID` returns zero rows. Always join `Maps.LocationID = Projects.LocationID`. See `references/maps-and-attachments.md`.
30. **Using Python/execute_code for bulk downloads.** `execute_code` has a 50-tool-call limit per script. Downloading 199 files one curl at a time in Python blows through that limit and crashes mid-download. Write a **bash script** instead and run it in a single `terminal()` call.
31. **URL-encoding spaces in `Maps.ImagePath` URLs.** The storage URLs contain spaces (e.g. `…/AltonMarketPlace 2024 Arc Base Map.pdf`). Raw spaces in curl cause silent failures. URL-encode spaces as `%20` before downloading.
32. **Querying `Contracts` or `CompanyContracts` with a `CompanyID` column.** The project-level `Contracts` table has **no** `CompanyID` column — it links to projects via `ProjectID`, and projects link to companies. The company-level `CompanyContracts` table **does** have `CompanyID`. When you get `Invalid column name 'CompanyID'` on Contracts, switch to `CompanyContracts` or join through `Projects`. See `references/company-contracts.md`.
33. **Confusing `Contracts` (project-level) with `CompanyContracts` (company-level).** TRIM IT has two separate contract tables at different hierarchy levels. `Contracts` (project-level, `ContractID`) holds per-project contract terms, budgets, and year-by-year breakdowns. `CompanyContracts` (company-level, `CompanyContractID`) holds the master agreement that sits above all projects for a company. When Brent asks "how many contracts do I have at the company level," query `CompanyContracts`, not `Contracts`. See `references/company-contracts.md`.
34. **Treating an empty `dbo.GetLevel4PriceRange$TPH` result as no Price Buddy history.** The function exists but returns zero rows through the play/read-only connection because it reads from the inaccessible Workbench database. Do not keep changing parameters or report that history is absent. Rebuild the signal directly from `WorkOrderLines`; for municipal bids, use the municipal grid-cycle cohort documented in `/opt/data/home/municipal-knowledge/concepts/grid-only-price-buddy-floor.md` and the verified SQL in the `municipal-bid-pricing` skill.
35. **"Vacant Site" has multiple definitions — Data Export ≠ Proposal Generation counts.** `SpeciesRef = 'Vacant Site'` (e.g. 4,505 for Cypress) and `SizeCode = '---'` (e.g. 3,202) yield different counts, and the TRIM IT UI's Data Export vs Proposal Generation screens use different filters, producing different totals for the same project. When Brent asks why two TRIM IT screens show different vacant-site figures, check both definitions and report which each screen likely uses. Additionally, the Arterial/Grids zone split in Data Export exports **cannot be reproduced via SQL** — `ZoneDefID` is NULL for ~99% of records and the zone resolution happens at the TRIM IT application layer (likely spatial via lat/long). Report this honestly rather than guessing. See `references/vacant-site-discrepancies.md`.
36. **TRIM IT zone assignments are mostly NULL in the database.** `InventoryDetail.ZoneDefID` is NULL for the vast majority of records (e.g. 21,909 of 22,019 for Cypress). TRIM IT's UI resolves zones (Arterial, Grids, Parks, etc.) at the application layer, not via a queryable column. `DistrictRef` text labels are also sparsely populated. Do not attempt to reproduce TRIM IT's zone-based exports via SQL alone — flag the limitation and ask Brent for the UI-exported data instead.

37. **Fabricating a failure narrative from circumstantial evidence.** When Brent replies on an email thread, do NOT assume the reply's content is about the attachments in that specific email. Brent chose Batch 6's thread as a convenient reply point for a general debrief — he was NOT saying Batch 6's attachments were wrong. Before reporting a bug or failure to the user, verify it against actual evidence. If you can't verify, ask — don't construct a narrative from the thread's position. (Brent's correction, 2026-07-17.)
38. **Substituting a similarly named historical proposal when the requested live proposal is missing from play.** The play replica can lag live by ~24 hours. For Cypress UI proposal `LegacyRef = 428345` (dated 2026-07-20), analyzing older full-inventory ProposalID 800600 produced a false 4,330-line explanation; Brent's actual screen showed 2,582 vacant sites. If the exact `LegacyRef` is not yet present, do not use a sibling proposal as though it were the requested one. Preserve the UI figures, query inventory definitions separately, and label screen-filter mappings as hypotheses until the exact proposal reaches play. See `/opt/data/home/municipal-knowledge/references/cypress-vacant-site-counts-2026-07-21.md`.

39. **Using `execute_code` in a cron job.** `execute_code` is **entirely blocked** when running as a scheduled cron job — it fails immediately, not just at the 50-tool-call limit (pitfall #30). Any Python work in a cron context must use `terminal()` with a script file or inline `python3 -c`. For libraries not installed globally (e.g. `openpyxl`), create a temp venv with `uv`. See `/opt/data/home/municipal-knowledge/concepts/execute-code-blocked-in-cron.md`.

41. **Cron jobs with `model: null / provider: null` can fall through to a keyless fallback and hard-fail.** A job that isn't pinned inherits the *live* provider chain at runtime. If the primary provider blips on that tick, the call walks down `fallback_providers` — and a fallback whose key env var is unset in the **cron runtime** (which does not inherit the interactive session's `.env`/memory the same way) sends `Authorization: Bearer None` and dies with `HTTP 401 invalid x-api-key`, classified `non_retryable_client_error` (4xx, not retried → repeats every tick until fixed). This is a latent bomb: the job can run fine for weeks until the first primary blip reaches the never-exercised fallback. **Two durable lessons:** (a) for scheduled jobs, **pin the provider+model** (`cronjob action=update`, or `hermes cron edit <id>`) — determinism beats resilience; (b) when a job shows `last_status: error`, the smoking gun is the **request dump** at `$HERMES_HOME/sessions/request_dump_cron_<job_id>_*.json` (parse `reason`, `request.url`, `request.headers.Authorization`, `response.body`), alongside the agent's own output log at `$HERMES_HOME/cron/output/<job_id>/`. Full forensic recipe in `references/knowledge-vault-maintenance.md` § Diagnosing a failed sweep run.

40. **Building a bid cost proposal from TRIM IT inventory instead of the City's Pricing Worksheet.** On the Long Beach PW25-648 bid, v2 was built from a TRIM IT InventoryDetail query (66,223 trees) instead of the City's official Pricing Worksheet (87,229 trees). This dropped 11 species (including Queen Palm at 6,286) and skewed all volume allocations. **The City's Pricing Worksheet is the source of truth for inventory volumes and species mix.** TRIM IT inventory is for reference/cross-check only. See `/opt/data/home/municipal-knowledge/references/long-beach-inventory-base-correction.md`.

42. **Contract status codes are scoped — `Approved` has different `StatusDefID`s per table.** The `StatusDefs` table holds statuses for every entity, disambiguated by a `Scope` column. **Company-level `CompanyContracts`** (Scope = `'CompanyContracts'`) uses IDs 291–296, 316 (295 = Approved, 292 = Inactive, 291 = Deleted, 316 = Archived). **Project-level `Contracts`** uses a different set: 135 = Active, 136 = Inactive, 161 = Pending, 162 = InProcess, **287 = Approved**, 288 = Not Approved, 346 = Complete. The municipal PO/budget queries that hardcode `StatusDefID = 287` are operating on `Contracts`, not `CompanyContracts` — mixing tables silently returns zero rows. **Always filter `StatusDefs` by `Scope` and confirm which contract table you're querying before hardcoding a status ID.** See `/opt/data/home/municipal-knowledge/concepts/trimit-contract-status-codes-scoped.md`.

## Verification Checklist

- [ ] Query uses `PublishedName` (not `CompanyName`) for company names
- [ ] Municipal filter includes `ProjectGroupDefID = 11` where a segment filter is needed
- [ ] Customer lists de-duplicated: duplicates collapsed, department sub-rows rolled up, typos/junk flagged
- [ ] PO-follow-up queries aggregate all approved contract components per city; partial component gaps are separated from city-level gaps
- [ ] Missing budget is labeled as an inferred PO/renewal follow-up signal unless confirmed by an authoritative source
- [ ] Historical municipal staffing uses reconciled actual worker-days/hours; any hours-supported result is labeled equivalent headcount
- [ ] Any budget total checked against the PO-gating rule — gaps flagged, not fabricated
- [ ] Output parsed from pipe-delimited format with awareness of the header row
- [ ] No write attempted — connection treated as read-only
- [ ] Cost estimates exclude "Vacant Site" records (`SizeCode = '---'`); vacant sites flagged separately as planting opportunities
- [ ] City contact queries use correct `Contacts` columns (`email`, `PrimaryPhone`, `ContactTitle`) — verified via `syscolumns` if unsure
- [ ] External emails drafted for Brent's approval — never sent autonomously (SEND-GATE)
- [ ] Cost estimates cross-checked against remaining contract budget; gaps flagged explicitly, not buried
- [ ] Knowledge vault synced with any new findings (vault path = `/opt/data/home/municipal-knowledge/`, not `~/home/`)
- [ ] Proposal IDs from Brent's email validated against DB — searched by description if IDs don't match
- [ ] Email sent only to Brent or Jason — no external recipients without per-instance approval
- [ ] Himalaya invoked with `--config /opt/data/.config/himalaya/config.toml`
- [ ] Commercial-contract data compartmentalized from municipal in all reports and totals
- [ ] Files emailed to Brent renamed using Desc1 + project name (NOT raw ImagePath filenames); asked about naming preference BEFORE sending
- [ ] MML `<#part filename=...>` tags verified to match body-text file list before sending
- [ ] Maps/attachments queries join via `LocationID` (NOT `ProjectID`, which is NULL)
- [ ] Bulk file downloads use a bash script, not Python (execute_code has a 50-tool-call limit)
- [ ] URLs with spaces URL-encoded (`%20`) before curl
- [ ] Large email sets filtered/sifted before batching (Brent prefers to narrow scope first)
- [ ] MML multipart emails have `<#multipart>` immediately after the header blank line (no body text before it)
- [ ] Company-level contract queries use `CompanyContracts` table (NOT `Contracts` or `Projects`); join `Companies` for names, `StatusDefs` for status labels; deliver as CSV for tabular data
- [ ] When investigating vacant-site count discrepancies, check BOTH `SpeciesRef = 'Vacant Site'` AND `SizeCode = '---'` — TRIM IT screens use different definitions; flag the gap if they can't be reconciled via SQL
- [ ] When investigating proposal vs export discrepancies, resolve the exact UI `LegacyRef` to its database `ProposalID` before analyzing `ProposalLines`; if the proposal has not reached play, do not substitute a sibling/historical proposal
- [ ] Do not attempt to reproduce TRIM IT zone-based UI exports (Arterial/Grids/Parks splits) via SQL — zone resolution is at the app layer, not in queryable columns
- [ ] When Brent replies on an email thread, do not assume the reply is about that specific email's attachments — verify against actual evidence before reporting a bug or failure
- [ ] Data deliverables (spreadsheets, reports) must pass a provenance audit: every column traceable to a named source, computed/estimated columns labeled as such
- [ ] Inventory totals in bid pricing tools must come from the City's RFP Pricing Worksheet, NOT from TRIM IT InventoryDetail
- [ ] When updating a deliverable from a prior session, re-read every sheet for data consistency before sending — do not patch stale data

## References

- `references/muni-query-patterns.md` — full verified SQL pattern catalog
- `references/po-gap-reconciliation.md` — city-by-city reconciliation workflow
- `references/po-follow-up-identification.md` — correctly infer new-FY PO/renewal follow-up at city level without newest-contract false positives
- `references/municipal-bid-watch.md` — combine internal expiration signals with official procurement verification; separate confirmed open bids from inferred renewal watch items
- `references/orange-county-public-bid-scan.md` — broad Orange County city/County/agency/school-district scan, portal map, PDF verification pattern, and false-positive controls
- `references/municipal-workforce-headcount.md` — calculate historical average municipal field staffing as a reconciled hours-supported equivalent when named assignments are incomplete
- `references/inventory-gps-tree-census.md` — query the per-tree GPS census (`InventoryDetail`): schema map (274 columns), pruning-cycle queries, key column reference, Schedule of Compensation (`LocationServiceTypes` rate card), and pitfalls (`PruningFrequency` not `CurrentYear`, `Inventories` table is a red herring, `DistrictRef` unreliable — use `DistrictID`, rate card is in `LocationServiceTypes` not pricing tables)
- `references/inventory-cost-estimates-and-contacts.md` — pruning cost estimate workflow (join `InventoryDetail` × `LocationServiceTypes` by district + cycle), the "Vacant Site" exclusion pattern, city contact discovery (`Contacts` table column names), email tool configuration (`--config` path), email restriction rule (Brent/Jason only), and the email-drafting workflow with SEND-GATE rules
- `references/commercial-contract-proposals.md` — Irvine Company and formal-contract commercial proposal analysis: scope rule (compartmentalized from municipal), the Proposal ID mismatch pitfall (pasted UI IDs may not match DB IDs — search by description), species extraction workflow (`Proposals` → `ProposalLines` → `InventoryDetail`), and known commercial CompanyIDs
- `references/maps-and-attachments.md` — downloading project attachments (Base Maps, Specialty Maps, images, documents) from TRIM IT storage: the `dbo.Maps` table schema, `LocationID` join (NOT `ProjectID`), sub-tab-to-flag mapping (`IsBaseMap`/`IsRemovalMap`/`RecordType`), the bulk-download workflow (query → JSON → curl → per-project subdirs), UNC-path pitfalls, and the Irvine Company Retail Portfolio worked example
- `references/litigation-disclosure-research.md` — bid-support litigation research: legacy `.doc` extraction via olefile, court records searchability by jurisdiction (LA County = web-indexed on DocketAlarm/DocketBird; OC Superior = NOT indexed, must use court portal), verified case research from GSTS disclosure document, and deliverable format (Draft One → adversarial review → Draft Two)
- `references/company-contracts.md` — the `dbo.CompanyContracts` table: schema (51 columns), status codes (7 types), standard query patterns, data-quality notes (bogus 1930 end dates, placeholder rows, test companies), and the CSV-delivery workflow for contract tables
- `references/vacant-site-discrepancies.md` — why TRIM IT screens show different vacant-site counts (SpeciesRef vs SizeCode definitions), the zone reproduction gap (zone resolution is app-layer, not SQL-reproducible), and the verified breakdown query
- `references/knowledge-vault-maintenance.md` — the self-improvement protocol: nightly knowledge sweep, weekly vault housekeeping, atomic note writing rules, and cron job IDs for manual triggering. **Cron schedules are NOT authoritative here** — see the vault note `cron-schedule-and-staggering.md` (in `/opt/data/home/municipal-knowledge/`) or run `cronjob action=list` for the live schedule.
- `templates/chatgpt-export-prompt.txt` — the finalized ChatGPT/Claude data extraction prompt Brent uses to export his AI chat histories for Muni Bot ingestion. Generates a filename, exports into structured markdown sections, and includes delivery instructions. When Brent asks for "the prompt," this is it.
- `~/home/municipal-knowledge/` — the on-disk knowledge vault (concepts, references, Brent's history). Read when present; it is the deeper source of truth on methodology and Brent's working style.

## Knowledge Vault Sync Protocol

The skill's `references/` files and the Obsidian vault at `/opt/data/home/municipal-knowledge/` (OBSIDIAN_VAULT_PATH) **must stay in parity**. The vault is Brent-facing shared knowledge; the skill is the agent's operational layer. When either side gains new knowledge, mirror it to the other.

**Same path trap as the query script:** the vault is at `/opt/data/home/municipal-knowledge/`. Do NOT write `~/home/municipal-knowledge/` — with `$HOME=/opt/data`, `~/home/` expands to `/opt/data/home/home/` which does not exist.

### Vault structure
- `00-start-here/README.md` — vault map with `[[wikilinks]]` (update when adding files)
- `concepts/` — core rules and interpretations (po-gated-budgets, data-hygiene-pitfalls, brent-178k-artifact)
- `references/` — detailed workflows and verified data (mirrors skill `references/`)
- `query-playbook/` — verified SQL patterns with column-trap reference table
- `brent-history/` — Brent's municipal-history file base (ingested documents)

### When to sync
- After adding a new reference file to the skill → create the corresponding vault file.
- After discovering a new verified query pattern, column trap, or data-quality rule → update both the skill pitfall list AND the vault query-playbook.
- After Brent corrects terminology, workflow, or states a preference → update `references/brent-profile.md` in the vault.
- After learning new TRIM IT schema details → update `references/gps-tree-inventory.md` (vault) and the corresponding skill reference.

### Automated maintenance
Two cron jobs keep the vault healthy (see `references/knowledge-vault-maintenance.md`; the authoritative cron schedule lives in the vault note `cron-schedule-and-staggering.md`):
- **Nightly sweep** (11 PM PT, `0 6 * * *` UTC): reviews the day's sessions, writes new findings as atomic notes, patches this skill's pitfall list.
- **Weekly housekeeping** (Sun 11:30 PM PT, `30 6 * * 1` UTC — staggered 30 min after the nightly sweep so they don't collide): archives orphaned/duplicate/stale notes to `_archive/`, updates README and skill references.

> **Schedules drift.** The cron times above were accurate as of 2026-07-20 but cron schedules are edited via the `cronjob` tool, not this doc. Before quoting a cron time as fact, run `cronjob action=list` to verify the live schedule. The vault note `cron-schedule-and-staggering.md` is the source of truth.

Both rules are surfaced at chat start via user-profile memory.

### Sync method
1. Write the vault file using `write_file` with the full absolute path.
2. Use `[[wikilink]]` syntax to cross-link related vault notes.
3. Update `00-start-here/README.md` if a new file was added.
4. `git add -A && git commit` in the vault directory.
5. The vault git identity is `MuniBot.gsts@gmail.com` / `Muni Bot` (set per-repo, not global).
