# Maps & Attachments (Downloading from TRIM IT Storage)

How to find and bulk-download project attachments — Base Maps, Specialty Maps,
images, and other documents — from the `dbo.Maps` table. This covers both
municipal (Track 1) and commercial-contract (Irvine Company, etc.) projects.

## The `dbo.Maps` table — the attachment catalog

TRIM IT stores ALL project-level attachments (maps, images, documents) in a
single table: **`gsts.dbo.Maps`**. Despite the name, it holds much more than maps.

### Key columns

| Column | Purpose |
|--------|---------|
| `MapID` | Primary key |
| `Desc1` | Human-readable description (e.g. "2023 Arc Base Map") |
| `LocationID` | **The scoping key** — links to `Projects.LocationID` |
| `ProjectID` | Usually NULL — do NOT join on this |
| `RecordType` | 'Map', 'Attachment', 'Image', 'SoundingReport', 'Incident' |
| `IsBaseMap` | Bit — **1 = filed under "Base Maps" sub-tab** |
| `IsRemovalMap` | Bit — 1 = also marked as a removal map (maps can be both) |
| `IsApproved` | Bit — 1 = approved/active status |
| `StatusDefID` | 181 = Active, 180 = Pending, 182 = Approved (varies) |
| `ImagePath` | **The download URL** — HTTP or UNC path |

### Critical: scope by `LocationID`, NOT `ProjectID`

`Maps.ProjectID` is almost always NULL. The join is:
```sql
SELECT m.* FROM gsts.dbo.Maps m
JOIN gsts.dbo.Projects p ON p.LocationID = m.LocationID
WHERE p.CompanyID = <companyID>;
```

### Sub-tab semantics (how TRIM IT UI maps to flags)

| TRIM IT Attachments sub-tab | DB filter |
|-----------------------------|-----------|
| **Base Maps** | `IsBaseMap = 1` |
| **Specialty Maps** | `IsRemovalMap = 1` (removal maps, crew maps, marked-up maps) |
| **Images** | `RecordType = 'Image'` |
| **Other** | `RecordType = 'Attachment'` (RFPs, contracts, POs, bid sheets) |
| **Sounding Reports** | `RecordType = 'SoundingReport'` |

Note: a single map record can carry BOTH `IsBaseMap = 1` AND `IsRemovalMap = 1`.
The Base Maps sub-tab shows everything with `IsBaseMap = 1` regardless of
`RecordType`.

## Downloading attachments

### `ImagePath` is directly downloadable

Most `ImagePath` values are HTTP URLs on the GSTS storage server:
```
https://www.greatscotttreeservice.com/gsts/Storage/Data/{LocationID}/<filename>.pdf
```

**These URLs return HTTP 200 and the file directly — no auth header needed.**
URL-encode spaces in filenames (`%20`).

### Legacy UNC paths (not downloadable)

Some older entries use UNC network paths:
```
\gsts\Customer\Maps\18963\
```
These are **not web-accessible** — they require someone at the office to pull
from the network share. Flag them and move on.

### Bulk download pattern (verified 2026-07-17)

1. **Query all target records:**
   ```sql
   SELECT m.MapID, m.Desc1, m.LocationID, m.RecordType,
          m.IsBaseMap, m.IsRemovalMap, m.IsApproved,
          m.ImagePath, p.Desc1 AS ProjectName
   FROM gsts.dbo.Maps m
   JOIN gsts.dbo.Projects p ON p.LocationID = m.LocationID
   WHERE p.CompanyID = <companyID>
     AND m.IsBaseMap = 1     -- or whatever sub-tab filter
   ORDER BY p.Desc1, m.Desc1;
   ```

2. **Parse pipe-delimited output** into records (JSON intermediate file works well).

3. **Download each HTTP URL** with curl, organized into per-project subdirectories:
   ```bash
   curl -sL -o "<project_dir>/<mapID>_<filename>" \
        "https://www.greatscotttreeservice.com/gsts/Storage/Data/<locID>/<encoded_filename>"
   ```
   - Use `-sL` (silent + follow redirects)
   - Check `os.path.getsize() > 0` and HTTP 200 to confirm success
   - Prefix filenames with MapID for traceability
   - Organize into subdirectories by project name

4. **Log everything** — a CSV/JSON download log with status, HTTP code, size,
   MapID, project, and description. Include failed and skipped entries.

### Scale reference

Irvine Company Retail Portfolio (CompanyID 301642): **201 Base Map records**
across 39 projects, downloading to ~247 MB. 199 of 201 were HTTP-downloadable;
2 were legacy UNC paths. Zero failures on the HTTP downloads.

## File type breakdown

Base Maps can include PDFs, PNGs, JPGs, and other image formats. The storage
server serves them all. Common patterns seen:
- `.pdf` — the majority (maps, bid sheets, contracts)
- `.png` / `.jpg` — some maps and photos
- `.PNG.pdf` — occasionally a PNG wrapped in PDF naming

## Known Irvine Company entities (for attachment queries)

| Entity | CompanyID | Projects |
|--------|-----------|----------|
| **Irvine Company Retail Portfolio** | **301642** | 39 retail properties + portfolio-level |
| Irvine Company (legacy/office) | 295656 | ~100 older retail/office projects |
| Irvine Company (Spectrum Center) | 297592 | Irvine Spectrum Center |
| Irvine Company (office zones) | Various (301442+) | Office property zones |

The "Retail Properties (2023-2026)" portfolio = CompanyID 301642. The parent
project is `==Irvine Company Retail Portfolio==` (ProjectID 1098302,
LocationID 1277450). It has 38 child retail-center projects, each with their
own LocationID.

## Emailing downloaded files to Brent

When Brent asks for attachments to be emailed, the Gmail 25 MB attachment limit
is the binding constraint. Strategy:

### Sift before sending (Brent's preference)

Brent prefers to narrow the scope before delivery rather than receiving
everything. In this session he asked for all base maps, then immediately said
"let's do some of the sifting first — only send me maps that had the word 'arc'
in the file display name." **Offer filtering options (by year, by type keyword,
newest only, etc.) before sending bulk files.**

### Batching strategy

1. **Calculate total size** of the filtered file set.
2. If under 25 MB → single email with all files as MML attachments.
3. If over 25 MB → split into batches of ≤24 MB each.
4. **Batching algorithm:** sort files by project/region, then greedily fill
   batches up to the size cap. This keeps related files together.

### MML multipart email with attachments (himalaya)

```
From: sender@example.com
To: bbeller@gstsinc.com
Subject: Arc Base Maps (Batch 1 of 6)

<#multipart type=mixed>
<#part type=text/plain>
Email body text here.
List the files in this batch.
<#/part>
<#part filename="/absolute/path/to/file1.pdf"><#/part>
<#part filename="/absolute/path/to/file2.pdf"><#/part>
<#/multipart>
```

**Key rules for MML with attachments:**
- The `<#multipart type=mixed>` tag comes immediately after the blank line
  separating headers from body. No plain text before the multipart tag.
- Each attachment is `<#part filename="/path"><#/part>` — quote the path.
- The text body goes inside its own `<#part type=text/plain>...<#/part>`.
- Send via: `cat message.mml | himalaya --config <config> template send`

### f-string quoting pitfall (Python → MML)

When building MML strings in Python, the `filename="..."` attribute inside
`<#part>` tags conflicts with f-string quoting. **Use `.format()` instead of
f-strings for the part lines:**

```python
# WRONG — SyntaxError from nested quotes:
lines.append(f'<#part filename="{f["filepath"]}"><#/part>')

# RIGHT — use .format():
lines.append('<#part filename="{}"><#/part>'.format(filepath))
```

### Scale reference (Irvine Company Arc maps, 2026-07-17)

Filtered 201 base maps down to 44 "Arc" maps (~125 MB). Split into 6 batches
(7/11/9/7/7/3 maps, 11–24 MB each). All 6 emails sent successfully to Brent.

## Company name → CompanyID discovery

Brent may refer to a portfolio by a label that doesn't exist verbatim in
`Companies.PublishedName`. Example: "The Irvine Company - Retail Properties
(2023-2026)" → no exact match. Discovery path:

1. Search `PublishedName LIKE '%Irvine Company%'` → returns multiple CompanyIDs.
2. Search `PublishedName LIKE '%Retail%'` → may return unrelated companies.
3. Search project descriptions: `SELECT * FROM Projects WHERE Desc1 LIKE '%Retail Portfolio%'`
4. The "Retail Properties (2023-2026)" label appears to be a **contract/portfolio
   label**, not a company name. The actual company is CompanyID 301642
   ("The Irvine Company"), with parent project `==Irvine Company Retail Portfolio==`.

## Pitfalls

1. **Joining `Maps` on `ProjectID` returns zero rows.** `Maps.ProjectID` is
   almost always NULL. Always join through `LocationID`.
2. **Don't confuse `RecordType` with sub-tab placement.** A record with
   `RecordType = 'Attachment'` and `IsBaseMap = 1` still appears under the Base
   Maps sub-tab. Filter on `IsBaseMap`, not on `RecordType`.
3. **UNC paths (`\\gsts\\...`) are not downloadable.** Don't try to curl them —
   they're internal network paths. Flag for manual retrieval.
4. **Duplicate URLs across MapIDs.** Some projects reuse the same file for
   multiple map records (e.g., a removals map re-uploaded with a new name).
   201 records may yield ~190 unique files. De-dupe by URL if only unique files
   are needed.
5. **Filenames with spaces.** URL-encode spaces as `%20` or curl will fail
   silently with a truncated URL.
6. **Brent's portfolio labels may not match `PublishedName`.** A label like
   "The Irvine Company - Retail Properties (2023-2026)" is a contract/portfolio
   name, not a company name. Search project descriptions and contracts to find
   the right CompanyID.
7. **Gmail 25 MB attachment limit.** Bulk file sets over 25 MB must be split
   into batched emails. Calculate total size first, then batch at ≤24 MB.
8. **MML f-string quoting conflict.** When building MML attachment lines in
   Python, use `.format()` not f-strings (nested quotes cause SyntaxError).
