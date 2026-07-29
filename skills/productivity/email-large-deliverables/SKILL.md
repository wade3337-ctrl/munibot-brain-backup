---
name: email-large-deliverables
description: >
  Deliver large amounts of data/files (maps, reports, exports) to Brent via email
  by splitting into Gmail-safe batches. Covers filtering/sifting, size-aware batching,
  and himalaya MML multipart sending with per-email content manifests.
---

# Email Large Deliverables

Use when Brent (or Jason) asks you to email them a large set of files — maps, reports,
exports, documents — that exceed Gmail's **25 MB per-email attachment limit**.

## When to use this skill

- "Email me all the maps / attachments / files"
- "Send me everything for [project/company]"
- Any request to deliver more than ~25 MB of files via email
- **Tabular data** (contract lists, budget tables, inventory exports) — deliver as a
  CSV attachment on a single email (see § Tabular Data Delivery below)

## Workflow

### 1. Sift before you send
Before batching, ask (or check): does the recipient want **everything**, or a filtered subset?
Common filters that dramatically reduce volume:

- **File-name keyword** — e.g., only "Arc" maps (Brent's Irvine request: 201 → 44 files)
- **Newest per group** — only the most recent version per project/property
- **File type** — only PDFs, only images, etc.
- **Sub-tab** — Base Maps vs Specialty Maps vs other attachment categories

Always confirm the filter with the recipient before sending if the full set is huge.

### 1.5. Ask about file naming
**Before downloading and renaming anything**, ask Brent how he wants the files named.
Don't assume — even if he's expressed a preference before (project-name based), always
prompt first so he can specify. Common options:

- `[ProjectName] - [Desc1].pdf` (alphabetically sortable, cross-referenceable)
- `[ProjectName] - [MapID] - [Desc1].pdf` (adds TRIM IT ID for traceability)
- Just `[ProjectName].pdf` (simplest)

His stated default (2026-07-17): project name. But "best not to assume."

**Never** send files with the raw TRIM IT storage filename from `ImagePath` — it's a
meaningless URL path (e.g. `Revised Colored Map.pdf`) that does not match the display
name Brent sees in TRIM IT (`Desc1`, e.g. "2016 Arcview Base Map").

### 2. Check total size
After filtering, sum the file sizes:

```python
import os
total = sum(os.path.getsize(f) for f in file_list)
print(f"Total: {total/1024/1024:.1f} MB")
```

- **≤ 24 MB** → single email, no batching needed
- **> 24 MB** → batch (continue below)

### 3. Batch into Gmail-safe groups
Target **≤ 24 MB per batch** (safety margin under Gmail's 25 MB hard limit).
Greedy-fill algorithm:

```python
MAX_BATCH = 24 * 1024 * 1024  # 24 MB

batches = []
current = []
current_size = 0

for f in all_files_sorted_by_region_or_group:
    if current_size + f['size'] > MAX_BATCH and current:
        batches.append(current)
        current = []
        current_size = 0
    current.append(f)
    current_size += f['size']
if current:
    batches.append(current)
```

**Grouping strategy:** sort files by a logical dimension (region, project, type) before
greedy-filling so batches stay thematically coherent — easier for the recipient to navigate.

### 4. Send via himalaya MML multipart

**CRITICAL MML format gotchas** (learned the hard way):
- Headers → **blank line** → `<#multipart type=mixed>` tag immediately
- **NO body text between headers and the multipart tag**
- Wrap filenames in **double quotes** (paths with spaces/parens break otherwise)
- Each part: `<#part filename="/full/path/to/file.pdf"><#/part>`

MML template:

```
From: MuniBot.gsts@gmail.com
To: bbeller@gstsinc.com
Subject: [Topic] - [Filter] (Batch X of Y)

<#multipart type=mixed>
<#part type=text/plain>
Hi Brent,

Here are the [description] (Batch X of Y, N files).

Files in this batch:
  - [Project] — [Description] (MapID / ID: XXX)
  - ...

Muni Bot
<#/part>
<#part filename="/full/path/to/file1.pdf"><#/part>
<#part filename="/full/path/to/file2.pdf"><#/part>
<#/multipart>
```

### 5. Send each batch

```python
from hermes_tools import terminal

for batch in batches:
    mml = build_mml(batch)  # as above
    with open('/tmp/batch.mml', 'w') as f:
        f.write(mml)
    result = terminal(
        'cat /tmp/batch.mml | himalaya --config /opt/data/.config/himalaya/config.toml template send 2>&1',
        timeout=120
    )
```

### 6. Report results
After all batches are sent, give the recipient a summary table:

| Batch | Files | Size |
|-------|-------|------|
| 1 of N | X | XX.X MB |
| ... | ... | ... |
| **Total** | **XX** | **~XXX MB** |

## Rules & guardrails

- **SEND-GATE:** Only send to Brent (`bbeller@gstsinc.com`) or Jason. No external
  recipients (cities, vendors) without explicit per-instance approval.
- **No download links:** Brent's directive — no temporary download URLs or web servers.
  Email is the delivery channel.
- **Content manifest in every email:** Each email body lists what's attached so the
  recipient can cross-reference back to TRIM IT (include MapID / record IDs).
- **Filename convention — ASK FIRST.** Always prompt Brent about preferred naming
  format BEFORE sending files. Don't assume. His likely default: name files by
  project name (`[ProjectName] - [Desc1].pdf`) so he can sort alphabetically and
  cross-reference against his project list. But confirm every time. **Never** use
  raw TRIM IT storage filenames — the `ImagePath` URL filename (e.g.
  `Revised Colored Map.pdf`) is meaningless and does NOT match the TRIM IT display
  name (`Desc1`, e.g. "2016 Arcview Base Map"). Use `Desc1` or project name.
  (Brent's directive, 2026-07-17 debrief.)
- **Himalaya config:** Always use `--config /opt/data/.config/himalaya/config.toml`
  (not the default `~/.config/himalaya/`).

## Related skills

- `trim-it-muni-queries` → `references/maps-and-attachments.md` — how to query and
  bulk-download files from TRIM IT storage (the source of most large deliverables)
- `himalaya` → `references/message-composition.md` — MML syntax reference

## Templates

- `templates/chatgpt-claude-export-prompt.md` — the finalized prompt Brent uses to
  extract data from his ChatGPT/Claude chats for Muni Bot ingestion. When Brent asks
  "resend me the prompt," send the content of this file (optionally as a .docx).

## Pitfalls

- **MML parse errors:** Caused by body text before the multipart tag, or unquoted file
  paths with spaces. If `himalaya template send` fails with "cannot parse MML body",
  check these two things first.
- **Missing `<#/part>` closing tag:** Every `<#part type=text/plain>` block must be
  explicitly closed with `<#/part>` before the attachment parts. Omitting it is the
  most common MML parse failure when building emails programmatically.
- **Python f-string quoting conflict:** When building MML attachment lines in Python,
  the `filename="..."` attribute inside `<#part>` tags conflicts with f-string quoting.
  Use `.format()` instead:
  ```python
  # WRONG — SyntaxError from nested quotes:
  lines.append(f'<#part filename="{f["filepath"]}"><#/part>')

  # RIGHT — use .format():
  lines.append('<#part filename="{}"><#/part>'.format(filepath))
  ```
- **Size creep:** MIME encoding inflates attachments ~33%. A 24 MB raw batch can become
  ~32 MB in the email. Keep raw batch total at ≤ 24 MB to stay under Gmail's limit after
  encoding.
- **Legacy UNC paths:** Some TRIM IT attachments are stored as `\\\\gsts-server\\...` UNC
  network paths, not web URLs. These cannot be downloaded — flag them separately to the
  recipient as "needs manual pull from the network share."
- **Raw storage filenames are useless:** The `Maps.ImagePath` filename is a storage URL
  (e.g. `Revised Colored Map.pdf`), NOT the TRIM IT display name. Brent can't identify
  files from these names. Always rename to `[ProjectName] - [Desc1].pdf` (or whatever
  naming convention he specifies). This was the primary feedback from Brent's 2026-07-17
  debrief — he had to rename every file himself.

## Tabular Data Delivery (CSV)

When the deliverable is **structured data** (not files) — a contracts table, budget
breakdown, inventory export — deliver it as a CSV attachment on a single email.
CSVs are tiny (146 rows × 12 columns = ~20 KB) and open directly in Excel.

### Workflow

1. **Query** TRIM IT via `trimit-query.sh` (pipe-delimited output).
2. **Parse** the pipe-delimited output into a CSV with proper headers.
3. **Format** for readability:
   - Money columns → `$X,XXX.XX` format
   - Date columns → `YYYY-MM-DD` (strip the `00:00:00.000` time portion)
   - `NULL` → blank cell
4. **Save** as a CSV file.
5. **Email** with the CSV as a single attachment using MML `name=` attribute:

```
<#multipart type=mixed>
<#part type=text/plain>
Hi Brent,

[Summary in the body — status counts, key totals, any data-quality flags]

Muni Bot
<#/part>
<#part filename="/path/to/data.csv" name="DescriptiveName.csv"><#/part>
<#/multipart>
```

The `name=` attribute overrides the filename the recipient sees — use a clean,
descriptive name (e.g. `TrimIT_Company_Contracts.csv`), not the temp file path.

### Worked example

Brent asked "how many company contracts do I have in TRIM IT?" (2026-07-17):
- Queried `CompanyContracts` table → 146 rows
- Parsed pipe-delimited output → CSV with 12 columns, money formatted, dates cleaned
- 19.6 KB CSV → single email, no batching needed
- Email body included a status-summary table (55 Approved, 19 Archived, etc.)
- Sent via himalaya MML with `name="TrimIT_Company_Contracts.csv"`

### When to use CSV vs inline table

- **≤ 10 rows** → inline table in the email body (no attachment needed)
- **> 10 rows or Brent will want to sort/filter** → CSV attachment
- **Brent explicitly asks for a table in the email** → respect that, but offer CSV too

## Delivering Documents as .docx

When Brent asks for a Word document instead of .txt or .md:

1. **Install python-docx** (not in the default venv):
   ```bash
   uv pip install python-docx --python /opt/data/.venv/bin/python
   ```
2. **Build the .docx** by writing a Python script to `/opt/data/make_docx.py` first,
   then running `/opt/data/.venv/bin/python /opt/data/make_docx.py`. Heredoc Python
   with multi-line strings containing `---` causes SyntaxError unterminated string
   literals — always write to a .py file and execute it.
3. **Attach via MML** with a descriptive `name=` attribute:
   ```
   <#part filename="/opt/data/Document.docx" name="Document.docx"><#/part>
   ```
