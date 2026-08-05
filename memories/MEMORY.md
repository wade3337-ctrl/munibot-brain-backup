TRIM IT access: read-only SQL via `/opt/data/home/trimit-query.sh` (pipe SQL on stdin, SSH to play replica ~24h behind, pipe-delimited output). Abs path only — `$HOME=/opt/data` so `~/home/` double-paths. Municipal segment = `ProjectGroupDefID=11`. Column traps: Companies.`PublishedName` (not CompanyName), InvoiceMasters.`Total` (not Amount). Vault: `/opt/data/home/municipal-knowledge/`. Skill: trim-it-muni-queries.
§
GPS tree inventory: InventoryDetail (274 cols). PruningFreq=year. District=DistrictID. Rate card: LocationServiceTypes. Maps: LocationID.
§
TRIM IT attachments: `Maps` table (keyed by `LocationID` not `ProjectID`). Sub-tabs: IsBaseMap=1, IsRemovalMap=1, RecordType='Image'/'Attachment'. Rate card in `LocationServiceTypes` (149=prune,47=removal,21=planting).
§
Email rule: Send only when explicitly asked. Recipients: Brent (bbeller@gstsinc.com), Jason/Skipper (jwade@gstsinc.com), gilligan.gsts@gmail.com. Bid deliverables default to Jason. When he says "surface" or "send to X," just produce MEDIA: path or hit send — no re-explanation, no "want me to email?"
§
Brent Beller, Contract Admin GSTS. Email: bbeller@gstsinc.com. TRIM IT UserID 40. Owns municipal budgets + formal-contract commercial (Irvine Co retail portfolio = CompanyID 301642, 39 projects; parent ProjectID 1098302). Compartmentalize muni vs commercial. Jason Wade = COO. Justin Aguilar (jaguilar@cnc-eng.com, 626-893-8221) = City of Industry contact at CNC Engineering; secondary Sylvia Salvillo.
§
Brent communicates casually and conversationally (e.g. 'my guys need work', 'kick the tires'). He gives corrections mid-stream without warning (e.g. 'Stop' then redirects). Keep responses tight — he knows his data, doesn't need hand-holding through municipal concepts. Gets excited when the bot finds things ('That's awesome!', 'You found it.').
§
Himalaya: always use --config /opt/data/.config/himalaya/config.toml. For complex email bodies, write to file then pipe (heredoc with && triggers foreground rejection).
§
Municipal archive: /opt/data/municipal-archive/ by county. ~42GB, NOT in git. Read directly, never commit.
§
BID PRICING: Renewal caps=7%. TPH=$130/hr universal (2026), yearly param. Old $75 non-PW rule RETIRED. PB FLOOR: use grid-only filter (WOs with 100+ completed lines) — blended qty=1 query LIES (overstates mid-bands 49-143%). Always pull AVG(Price): if bid > our avg billed, margin is real. Crew review: Kimi K3 + Gemini 3.1 Pro via /opt/data/home/crew/{kimi,gemini}-ask.py. Skill: municipal-bid-pricing.
§
VISION CAVEAT: Small text in screenshots (taskbar clocks, dates, system-tray captions) is unreliable — vision can hallucinate values. Prefilled "[user sent an image~]" descriptions are ALSO unreliable on small text. Always verify specifics with vision_analyze before stating as facts. Skipper caught a misread date 7/28/2023 when actual was 7/21/26. Flag uncertainty on tiny-text details; large-format text reads fine.
§
Google Sheets proposal (pending Jason, 2026-08-04): Brent + Muni Bot proposed gspread for live spreadsheet collaboration. Fixes blind-openpyxl. Brent will email Jason.