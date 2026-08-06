# Commercial-Contract Proposals (Irvine Company and similar)

Brent also manages larger commercial accounts with formal contracts (e.g. Irvine
Company retail properties). This work is **in scope** for Muni Bot but must be
**compartmentalized from municipal** — different segment, different company IDs,
do not mix in reports or totals.

## Contract hierarchy (company vs project level)

TRIM IT has two contract layers:

| Level | Table | Key | Scope |
|-------|-------|-----|-------|
| Company | `CompanyContracts` | `CompanyContractID` | Master agreement for a company (e.g. Irvine Company Retail Portfolio) |
| Project | `Contracts` (via `Projects.ContractID`) | `ContractID` | Per-project contract terms, budgets, year-by-year breakdowns |

When Brent asks about contracts at the **company level**, query `CompanyContracts`.
See `references/company-contracts.md` for the full schema and query patterns.

The Irvine Company (CompanyID 295656) has 3 company-level contracts:
- Contract No. RX-1208 (General Trimming) — Inactive
- Contract Agreement No RX-1209 (CI Palms) — Inactive
- Olive Tree Care — Inactive

Note: the retail portfolio entity (CompanyID 301642) does not currently have any
company-level contracts in the table — its contracts are at the project level.

## Scope rule (Brent's directive, 2026-07-15)

- Municipal = Track 1, `ProjectGroupDefID = 11`, city customers.
- Commercial contracts (Irvine Company, etc.) = Brent's larger formal-contract
  commercial accounts. **In bounds.** Keep separate from municipal processes.
- This is NOT general commercial (one-off HOAs, one-shot jobs). Only formal
  contracted commercial accounts Brent manages.

## The Proposal ID Mismatch (critical pitfall)

**When Brent pastes Proposal IDs from his TRIM IT UI into an email, those IDs may
not match the database.** The UI may show a worksheet/legacy/sequential ID that
differs from the `Proposals.ProposalID` stored in the database.

### Root cause: the UI shows `LegacyRef`, not `ProposalID`

**SOLVED (2026-07-21).** The TRIM IT UI Proposals tab displays the **`LegacyRef`**
column as the visible proposal number, NOT the database `ProposalID`. The two are
completely different numbering sequences:

| What Brent sees in UI | What's in the DB | Example |
|----------------------|-------------------|---------|
| Proposal "428345" | `LegacyRef = '428345'` | Maps to `ProposalID 801xxx` (Cypress) |
| Proposal "424185" | `LegacyRef = '424185'` | Maps to `ProposalID 797xxx` (Irvine Co) |

The UI proposal numbers are ~420K–428K range; the DB ProposalIDs are ~780K–802K
range. Querying `WHERE ProposalID = <UI number>` returns the wrong proposal every time.

### Correct lookup: by LegacyRef

```sql
SELECT ProposalID, Desc1, ProjectID, CompanyID, Total, StatusDefID, LegacyRef
FROM gsts.dbo.Proposals
WHERE LegacyRef = '<UI number Brent pasted>';
```

### Fallback: search by description keywords

If the proposal is too new for the play replica (dated within ~24h), `LegacyRef`
may not exist yet. Fall back to content search:

```sql
SELECT ProposalID, Desc1, LegacyRef
FROM gsts.dbo.Proposals
WHERE Desc1 LIKE '%<keyword>%'
ORDER BY ProposalDate DESC;
```

### Summary

1. **The UI number = `LegacyRef`.** Always look up by `LegacyRef` first.
2. **If LegacyRef not found**, the proposal may be newer than the replica —
   fall back to description search.
3. **Cross-validate** on CompanyID and ProposalDate.
4. **Confirm with Brent** if there's any ambiguity.

## Proposal Species Extraction Workflow

When Brent asks for species breakdown across multiple proposals:

### Step 1: Find the proposals by description

```sql
SELECT ProposalID, Desc1, ProjectID, CompanyID
FROM gsts.dbo.Proposals
WHERE Desc1 LIKE '%<keyword>%'
ORDER BY ProposalID DESC;
```

### Step 2: Get tree counts per proposal

```sql
SELECT p.ProposalID, p.Desc1, COUNT(DISTINCT pl.InventoryDetailID) AS TreeCount
FROM gsts.dbo.Proposals p
JOIN gsts.dbo.ProposalLines pl ON p.ProposalID = pl.ProposalID
WHERE p.ProposalID IN (...)
GROUP BY p.ProposalID, p.Desc1
ORDER BY p.Desc1;
```

### Step 3: Pull species breakdown per proposal

```sql
SELECT
    p.Desc1 AS ProposalName,
    idt.SpeciesRef AS Species,
    COUNT(*) AS TreeCount
FROM gsts.dbo.Proposals p
JOIN gsts.dbo.ProposalLines pl ON p.ProposalID = pl.ProposalID
JOIN gsts.dbo.InventoryDetail idt ON pl.InventoryDetailID = idt.InventoryDetailID
WHERE p.ProposalID IN (...)
GROUP BY p.Desc1, idt.SpeciesRef
ORDER BY p.Desc1, TreeCount DESC;
```

### Key tables in the join chain

| Table | Role | Key columns |
|-------|------|-------------|
| `Proposals` | The proposal header | `ProposalID`, `Desc1`, `ProjectID`, `CompanyID` |
| `ProposalLines` | Per-tree line items | `ProposalID`, `InventoryDetailID`, `SizeCode`, `ServiceTypeID` |
| `InventoryDetail` | The tree record (species) | `InventoryDetailID`, `SpeciesRef`, `DBH`, `SizeCode` |

## Known commercial-contract accounts

| Account | CompanyID(s) | Notes |
|---------|-------------|-------|
| The Irvine Company (retail) | 301642 | Primary retail entity; also 295656, 297592, 301642 |
| Irvine Company (office) | 301442, 301450, 301452, 301469, 301600, 301611, 301619, 301620, 301624 | Multiple office zone entities |
| Irvine Company (apartments) | 296243, 297531 | Apartment management entities |

⚠️ Irvine Company is fragmented across many CompanyIDs. Always verify which entity
a given set of proposals belongs to before reporting totals.

## Irvine Company Retail Portfolio structure (verified 2026-07-17)

The "Retail Properties (2023-2026)" portfolio Brent refers to is **CompanyID 301642**
("The Irvine Company"). Key facts:

| Entity | ID |
|--------|-----|
| Company | CompanyID **301642** |
| Parent project | `==Irvine Company Retail Portfolio==` (ProjectID 1098302, LocationID 1277450) |
| Child projects | 38 retail centers, each with its own LocationID |
| Total base map attachments | 201 records (IsBaseMap=1) |

The 38 retail centers are organized by collection/region (shown in project name
parentheticals): Coastal, Spectrum, Foothill, Central Irvine, University.

**The parent project** (LocationID 1277450) holds portfolio-level attachments:
bid summary, collection-level bid sheets (Central, Coastal, Foothill, Spectrum,
University, The Marketplace, Spectrum Interchange), contract agreements, POs,
and the GSTS response proposal.

**Each child project** holds its own base maps, removal maps, crew maps, sounding
reports, and field photos — typically a 2019 legacy map, a 2023/2024/2025 Arc
base map, CI Palm maps, and various work-order-specific maps.
