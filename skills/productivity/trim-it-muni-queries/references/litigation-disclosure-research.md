# Litigation Disclosure Research (Bid Support)

When Brent is preparing a bid/proposal and needs to disclose litigation history
tied to municipal contracts, he may ask Muni Bot to research public court records
and identify which contracting agency each case is tied to.

## Context

Bid documents (e.g. OCTA, City of Riverside) require disclosure of past/present
contracts where the firm has been involved in litigation with the contracting
authority. Brent's attorney provides a litigation list, but it often lacks the
specific contracting agency association — that's what Muni Bot needs to fill in.

## Source material

Brent typically emails:
- A disclosure document (may be legacy `.doc` format — see § Legacy .doc extraction below)
- The exact disclosure language from the bid document
- Sometimes an image attachment (usually letterhead/logo, not data)

## Legacy .doc extraction (no LibreOffice/antiword installed)

When the attachment is a binary `.doc` (not `.docx`) and no office tools are
available, use `olefile` in a temporary venv:

```bash
uv venv /tmp/docvenv && source /tmp/docvenv/bin/activate
uv pip install olefile
python3 << 'PYEOF'
import olefile, re
ole = olefile.OleFileIO("/tmp/filename.doc")
data = ole.openstream("WordDocument").read()
text = data.decode("latin-1", errors="ignore")
readable = re.findall(r"[\x20-\x7e]{10,}", text)
for r in readable:
    print(r)
ole.close()
PYEOF
```

This extracts readable ASCII strings from the WordDocument OLE stream. It's not
perfect formatting but captures all case numbers, descriptions, and structured
content. The `re.findall(r"[\x20-\x7e]{10,}", text)` pattern pulls consecutive
printable ASCII runs of 10+ characters.

## Court records research strategy

### Searchability by court jurisdiction (verified 2026-07-16)

| Court | Case format | Web-indexed? | Where to find |
|-------|-------------|-------------|---------------|
| LA County Superior | `22STCVNNNNN`, `24LBCVNNNNN` | ✅ Yes | DocketAlarm.com, DocketBird.com |
| Orange County Superior | `30-YYYY-NNNNNNNN` | ❌ No | Must use OC court portal directly (occourts.org) |

**Critical gap:** Orange County Superior Court cases (`30-` prefix) are **not
indexed by Google, DocketAlarm, UniCourt, or DocketBird**. Web searches for
these case numbers return zero results. To research OC cases, you must use the
OC court's online case access portal at `occourts.org/online-services/case-access`
(name search required, not case-number search).

### Verified search approaches

1. **DocketAlarm** — search by case number for LA County cases. Shows party
   names, case type, and defendant lists. URL pattern:
   `docketalarm.com/cases/California_State_Los_Angeles_County_Superior_Court/<case_no>/`

2. **DocketBird** — LA County civil case index, browsable by year and title.
   URL pattern: `docketbird.com/find-court-cases/los-angeles-county/civil/<year>/`

3. **News coverage** — high-value verdicts (e.g. $5.19M Robinson v. Long Beach)
   are covered by local press (Long Beach Post, EIN Presswire). Search for
   `[case type] [city] [amount] verdict`.

4. **Municipal bid protest records** — GSTS's own protest letters are published
   in city council records (e.g. Rosemead Granicus). These reference GSTS and
   other contractors (WCA) in relation to specific cities. Search:
   `site:granicus.com "Great Scott Tree"`

### When web research is insufficient

For OC cases that can't be found online:
- Report honestly what could and could not be verified
- Identify case types that likely have NO contracting agency tie (employment/PAGA
  matters, vehicle accidents, infractions — these are internal/insurance matters)
- Flag the cases that most likely DO have an agency tie (premises liability, PI/PD
  where GSTS was joined as a Doe defendant on a public property)
- Recommend Brent check the OC court portal directly or ask his attorney

## Confirmed case research (2026-07-16)

From GSTS disclosure document prepared for City of Riverside bid:

| Case No. | Type | Agency Tie | Source |
|----------|------|-----------|--------|
| 24LBCV00932 | Premises Liability | **City of Long Beach** (co-defendant, NOT adverse party) — Joseph Robinson v. City of Long Beach (El Dorado Park tree branch injury, $5.19M verdict). GSTS was third-party Doe defendant, dismissed Jun 2025. **NON-RESPONSIVE to bid question** — GSTS and City were co-defendants, not in litigation over a contract. | DocketAlarm, Long Beach Post |
| 22STCV28810 | Other PI/PD/WD | **City of Long Beach** (co-defendant, NOT adverse party) — Jenny Varley, et al. v. City of Long Beach, et al. (global settlement, dismissed Sept 2024). **NON-RESPONSIVE** — same co-defendant pattern. | DocketBird, LA County court index |
| 30-2022-01265052 | Wrongful Termination | Not found (OC case) — likely internal employment, no agency tie | — |
| 30-2023-01328795 | PI/PD/WD - Other | Not found (OC case) — filed against property management firm, GSTS joined as Doe | — |
| 30-2023-01364746 | Other employment (PAGA) | Not found (OC case) — internal labor code, unlikely agency tie | — |
| 30-2024-01443381 | Other employment (PAGA) | Not found (OC case) — related PAGA claim | — |
| 30-2025-01456947 | Other employment (PAGA) | Not found (OC case) — coordinated employment matter | — |
| 30-2025-01478942 | PI/PD/WD - Auto | Not found (OC case) — vehicular, insurance carrier | — |
| 30-2025-01491431 | PI/PD/WD - Auto | Not found (OC case) — vehicular, insurance carrier | — |
| 30-2026-01537789 | Non-PI/PD/WD tort | Not found (OC case) — recently filed general tort | — |
| 30-2026-01547317 | Small Claims | Not found (OC case) — $1,500 dispute | — |
| 00Q90005Q | Infraction | No agency tie — vehicle equipment citation | — |
| IRC183782 | Infraction | No agency tie — windshield transparency citation | — |

## ⚠️ CRITICAL: Answer the actual bid question, not "list all litigation"

**The #1 mistake** (caught by adversarial review, 2026-07-16): Draft One listed
all 13 cases and tried to attach agency labels to each. But OCTA's question is
narrower than "list all litigation." It asks:

> *"Contracts where the firm has provided services as a prime vendor or
> subcontractor during the past five (5) years in which the contract has been
> the subject of or may be involved in litigation with the contracting
> authority."*

This has **four gating elements**: (1) a specific contract existed, (2) GSTS
provided services on it, (3) THAT CONTRACT was the subject of litigation, and
(4) the litigation was WITH the contracting authority (adverse parties).

**Key distinction — co-defendant ≠ adverse party:**

The two Long Beach cases (Robinson, Varley) were initially flagged as
"confirmed" because the City of Long Beach is a named party. But GSTS and the
City were **co-defendants on the same side** of personal injury lawsuits —
GSTS was impleaded as a Doe tort defendant alongside the City. GSTS was NOT in
litigation WITH the City over a contract. Therefore these cases are
**non-responsive** to OCTA's question.

**The right approach:** Start from GSTS's contract list (TRIM IT
`ProjectGroupDefID = 11`), identify which agencies GSTS contracted with, then
cross-reference: was any of those specific contracts the subject of litigation
WITH that agency? If the answer is zero, lead with: *"GSTS has zero contracts
in the past 5 years that have been the subject of litigation with the
contracting authority."* Then provide non-responsive matters as context only.

**Do NOT over-disclose.** Listing 13 cases (including pending PAGA actions)
when the answer is "zero" makes GSTS appear more litigation-exposed than the
question requires. Scope the disclosure to what the bid asks.

## Deliverable format

Brent requested:
1. **Draft One** — original production (table with agency column added)
2. **Adversarial agent review** — spin up a subagent to critique the research
3. **Draft Two** — revised production after criticism

Use `delegate_task` to spawn the adversarial agent. Give it the draft file
path and ask it to critique across: accuracy, completeness, risk, language,
and (most importantly) whether the draft actually answers the bid question.

### Draft One structure
The table should preserve the original disclosure columns and add:
- **Contracting Agency** column (the research output)
- **Source/Confidence** column (how the agency tie was verified)

Present three confidence levels:
- **Verified** — confirmed via public court record or news source
- **Inferred** — case type suggests no agency tie (employment/PAGA/auto)
- **Unknown** — could not verify, needs direct court portal or attorney input

### Draft Two structure (after adversarial review)
- **Lead with the answer** to the bid question (zero / N contracts in litigation)
- Reclassify any cases where GSTS was a co-defendant (not adverse party) as
  non-responsive context
- Remove editorial characterizations ("routine," "de minimis")
- Add a 6-item attorney review checklist for items that couldn't be web-verified
- Strip all internal metadata (Muni Bot attribution, draft versioning)

### Emailing the deliverable
Write the email body to a file first, then pipe to himalaya:
```bash
cat /opt/data/litigation_email.txt | \
  himalaya --config /opt/data/.config/himalaya/config.toml template send
```
Do NOT use heredoc with `&&` or `&` in the email body — himalaya's foreground
process will reject it as backgrounding. Write to file, then pipe.
