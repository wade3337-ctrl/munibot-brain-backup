# Legacy .doc Extraction and Court Records Research

## Extracting text from binary .doc files (OLE format)

When Brent emails a `.doc` attachment (not `.docx`) and no office tools (antiword, catdoc, libreoffice) are installed, use `olefile` in a temp venv:

```bash
# Create a temp venv and install olefile
uv venv /tmp/docvenv && source /tmp/docvenv/bin/activate && uv pip install olefile

# Extract readable text
python3 << 'PYEOF'
import olefile

ole = olefile.OleFileIO("/tmp/filename.doc")
data = ole.openstream('WordDocument').read()

import re
text = data.decode('latin-1', errors='ignore')
readable = re.findall(r'[\x20-\x7e]{10,}', text)
for r in readable:
    print(r)
ole.close()
PYEOF
```

This extracts ASCII-readable strings from the binary OLE stream. Tables and structured data come through as space-delimited text — parse carefully.

**Limitation:** PIL/Pillow and vision_analyze may not work for image attachments if the model doesn't have vision permission. Don't block on reading images — focus on the text content.

## Court Records Searchability by Jurisdiction

### LA County Superior Court — WEB-INDEXED ✅
- **DocketAlarm:** Case details, party names, docket entries. Good for Long Beach cases (prefix `24LBCV`, `22STCV`).
  - URL: https://www.docketalarm.com
  - Search by case number or party name
- **DocketBird:** Civil case index, organized by year and title prefix.
  - URL: https://www.docketbird.com/find-court-cases/los-angeles-county/civil/
- **UniCourt:** Sometimes has case details and related-case links.
  - URL: https://unicourt.com

### Orange County Superior Court — NOT WEB-INDEXED ❌
- OC court cases (prefix `30-`) do NOT appear in Google, DocketAlarm, DocketBird, or UniCourt search results.
- The OC court portal at `courtindex.occourts.org` has a case-number search, but it only searches Criminal/Traffic effectively — Civil/Small Claims case-number searches return "No results found."
- **For OC cases: use the attorney's files as the primary source.** GSTS's attorney prepared the disclosure document and has full pleadings for every case.

### Bid Protest Documents — WEB-INDEXED ✅
- City council meeting documents on Granicus (e.g., `cityofrosemead.granicus.com`) are publicly accessible and sometimes reference GSTS litigation history in the context of bid protests.
- These can provide context about contracting agency relationships.

## Verified Research Approach

1. Start with the attorney-prepared disclosure document (extract via olefile if .doc)
2. Search LA County cases on DocketAlarm/DocketBird by case number
3. Search for party names + "Great Scott Tree" on Google for news coverage
4. For OC cases: acknowledge the gap and flag for attorney review
5. Cross-reference any city names found against TRIM IT municipal contracts (`ProjectGroupDefID = 11`)
6. Document all sources with URLs and retrieval dates

## Deliverable Format

- **Draft One:** Research log with all cases, agency attribution attempts, confidence levels
- **Adversarial Review:** Delegate to subagent — ask it to check whether the draft answers the ACTUAL bid question (not just lists litigation)
- **Draft Two:** Revised after critique — leads with the direct answer, strips metadata, adds attorney review checklist
- Email both drafts to Brent with a summary of what changed
