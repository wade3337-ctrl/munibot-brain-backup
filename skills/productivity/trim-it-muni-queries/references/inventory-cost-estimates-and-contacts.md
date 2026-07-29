# Pruning Cost Estimates & City Contact Discovery

Two recurring workflows that build on the inventory and Schedule of Compensation
queries: (1) estimating pruning costs for a scoped tree set, and (2) finding city
contacts for outreach/email drafting.

## Pruning Cost Estimate (InventoryDetail × LocationServiceTypes)

### When to use

Brent asks for a cost estimate on a subset of trees — typically scoped by
district and/or pruning cycle. "What would it cost to prune the 2024 cycle trees
in East District?"

### Verified workflow (2026-07-15, City of Industry)

1. **Scope the tree set** (district + cycle year):
   ```sql
   SELECT SizeCode, ServiceTypeID, COUNT(*) AS TreeCount
   FROM gsts.dbo.InventoryDetail
   WHERE ProjectID = <pid>
     AND PruningFrequency = <year>
     AND DistrictID = <district_id>
   GROUP BY SizeCode, ServiceTypeID
   ORDER BY SizeCode;
   ```

2. **Join to the Schedule of Compensation** for rates:
   ```sql
   SELECT
       d.SizeCode,
       COUNT(*) AS Trees,
       lst.BasePrice AS Rate,
       COUNT(*) * lst.BasePrice AS Subtotal
   FROM gsts.dbo.InventoryDetail d
   JOIN gsts.dbo.LocationServiceTypes lst
     ON lst.LocationID = <locid>
    AND lst.ServiceTypeID = d.ServiceTypeID
    AND lst.SizeCode = d.SizeCode
   WHERE d.ProjectID = <pid>
     AND d.PruningFrequency = <year>
     AND d.DistrictID = <district_id>
   GROUP BY d.SizeCode, lst.BasePrice
   ORDER BY d.SizeCode;
   ```

3. **Get the LocationID first** (one lookup per project):
   ```sql
   SELECT LocationID FROM gsts.dbo.Locations WHERE ProjectID = <pid>;
   ```

### The "Vacant Site" pattern

Trees with `SizeCode = '---'` and `SpeciesRef = 'Vacant Site'` will NOT join to
any rate on the Schedule of Compensation. These are empty planting sites, not
trees — DBH is 0 or NULL, no species. They appear in district/cycle counts but
should be:

- **Excluded from cost estimates** (they have no pruning cost).
- **Flagged separately** as potential planting/revenue opportunities.
- **Reported transparently** — "1,334 records → 1,310 trees + 24 vacant sites."

Example (City of Industry East District, 2024 cycle):
- Total records in scope: 1,334
- Rate-matched trees: 1,310 → $368,620
- Vacant sites (SizeCode '---'): 24 → $0 (planting opportunity)

### Budget gap flagging

When the cost estimate exceeds remaining contract budget, flag it explicitly
rather than burying it. Brent needs the real number to have an honest
conversation with the city contact.

City of Industry FY26 example:
- Annual contract budget: $666,667
- Invoiced YTD: $380,375
- Remaining: $286,291
- 2024 East cycle estimate: $368,620
- **Gap: ~$82K over remaining budget**

Present the full picture in any email draft and let Brent decide how to frame
the budget mechanics with the city.

## City Contact Discovery (Contacts table)

### Table schema notes

The `Contacts` table uses non-obvious column names. Verified columns:

| Correct column | Wrong guess | Error if wrong |
|----------------|-------------|----------------|
| `email` | `EMail` | Invalid column name |
| `PrimaryPhone` | `Phone` | Invalid column name |
| `ContactTitle` | `Title` | Invalid column name |
| `FullName` | — | Display name (First + Last) |
| `IsPrimary` | — | Bit flag for primary contact |

### Verified query pattern

```sql
SELECT ContactID, FirstName, LastName, FullName, email, PrimaryPhone, ContactTitle
FROM gsts.dbo.Contacts
WHERE CompanyID = <cid>
  AND (FirstName LIKE '%<name>%' OR LastName LIKE '%<name>%' OR email LIKE '%<name>%');
```

### Data quirks

- **Multiple emails in one field.** The `email` column can hold semicolon-separated
  addresses (e.g. `jaguilar@cnc-eng.com; scalvillo@cnc-eng.com`). Parse and ask Brent
  who to include as To vs CC.
- **ContactTitle may be NULL** even for key contacts. Don't rely on title for filtering.

## Email Drafting Workflow (SEND-GATE)

### Email tool configuration

Himalaya config lives at `/opt/data/.config/himalaya/config.toml`. Must pass
`--config` explicitly — himalaya defaults to `~/.config/himalaya/` which does not
resolve on this system. Always use:

```bash
himalaya --config /opt/data/.config/himalaya/config.toml <command>
```

Mailbox: `MuniBot.gsts@gmail.com` (display name: "Muni Bot - Great Scott Tree Care").

### Email restriction rule (Brent's directive, 2026-07-15)

**Only send email when Brent explicitly asks.** **Only send to Brent
(bbeller@gstsinc.com) or Jason.** Never email anyone else — no cities, no
contacts, no external parties — without explicit per-instance approval. This
is stricter than the general SEND-GATE: even if Brent approved a draft for
Justin, Muni Bot does not send it to Justin. Brent sends external emails
himself; Muni Bot only delivers drafts and internal mail to Brent/Jason.

### Brent's outreach emails follow a consistent pattern. When he asks to draft an email
to a city contact:

1. **Pull the data first** — budget position, cycle status, cost estimate, scope.
   The email should be backed by real TRIM IT numbers.
2. **Draft for approval** — NEVER send external email without Brent's explicit
   approval. Present the draft inline with To/CC/Subject/Body.
3. **Flag gaps and unknowns** — budget shortfalls, missing data, assumptions made.
4. **Use the Schedule of Compensation rates** — cite specific per-size rates in a
   table so the city contact can see the breakdown.
5. **Frame the win** — Brent sells on cycle improvement, risk management, urban
   forest health. "Completing this cycle brings the district to a 2-year rotation"
   is the kind of closer that resonates.
6. **Tone: professional, data-driven, concise.** Tables over prose. Let the numbers
   make the case.

### Email structure that worked (City of Industry → Justin Aguilar)

```
Subject: City of Industry — FY26 Budget Update & 2024 Cycle Pruning Proposal (East District)

1. Budget position table (annual budget, invoiced YTD, remaining)
2. Current cycle status (what's wrapping up)
3. Proposal with cost breakdown table (by DBH size, tree count, rate, subtotal)
4. "The Win" paragraph (cycle improvement, risk management framing)
5. Call to action (offer to discuss timeline)
```
