# ChatGPT / Claude Data Export Prompt

Copy-paste this into any ChatGPT or Claude chat to extract all data in a format
Muni Bot can ingest. Originally finalized with Brent on 2026-07-15.

---

Copy everything below this line into your ChatGPT chat:

---

I need to extract all valuable data from this conversation so I can transfer it to another AI assistant (Muni Bot, for Great Scott Tree Care). Please review our entire conversation history in this chat and produce a comprehensive data export in the following format.

**At the top of your response, before the data, generate a filename for this export using this convention:**

```
chagpt-export-[YYYY-MM-DD]-[short-topic-kebab-case].md
```

For example: `chatgpt-export-2026-07-16-city-of-industry-pricing.md` or `chatgpt-export-2026-07-16-octa-bid-strategy.md`

**Then output everything as a single markdown document with these sections (include only sections that have relevant data — skip empty ones):**

## SUMMARY
A 2-3 sentence description of what this chat was about and what it accomplished.

## KEY DATA TABLES
Export any tabular data we discussed (budgets, pricing, counts, schedules, contracts, etc.) as markdown tables with clear column headers.

## CONTACTS & RELATIONSHIPS
Any people, companies, agencies, or vendors mentioned, with their roles, contact info, and relationship to the topic.

## DECISIONS & CONCLUSIONS
Any decisions made, conclusions reached, or recommendations agreed upon.

## PROCESSES & WORKFLOWS
Any step-by-step processes, methodologies, or how-to information documented in this chat.

## FINANCIAL DATA
Any dollar figures, budgets, costs, rates, PO numbers, or contract values discussed.

## OPEN ITEMS & TODOs
Anything left unfinished, pending, or flagged for follow-up.

## CONTEXT & BACKGROUND
Any important context, history, or background information that would help another assistant understand the full picture.

**Rules:**
- Be exhaustive — I would rather have too much than miss something
- Preserve exact numbers, names, dates, and identifiers
- Do not summarize or round financial figures
- Include any file names, document titles, or external references mentioned
- If we created any templates, prompts, or documents, include their full text
- Flag anything that seems sensitive or confidential with [CONFIDENTIAL]

**After generating the full export, print this footer:**

```
---
FILE NAME: [the filename you generated above]
DELIVERY: Copy this entire response into a text file with the filename above, then email it to munibot.gsts@gmail.com or save it to the shared folder. Muni Bot will ingest it on receipt.
---
```
