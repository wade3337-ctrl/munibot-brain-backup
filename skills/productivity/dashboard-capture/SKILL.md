---
name: dashboard-capture
description: "Use when Brent or the Skipper asks to SEE, PULL UP, SCREENSHOT, or be SENT any TRIM IT dashboard/board by name — e.g. 'show me city budgets', 'send me the sales cockpit', 'screenshot the crew performance board', 'pull up revenue'. Captures a live authenticated screenshot of the matching dashboard and delivers it as an image."
version: 2.0.0
author: Muni Bot
license: MIT
metadata:
  hermes:
    tags: [dashboard, screenshot, trim-it, brent-beller, capture, image, city-budgets]
    related_skills: [trim-it-muni-queries]
---
# Dashboard Capture (TRIM IT) — any board, by name

Capture a **live screenshot** of any TRIM IT dashboard and send it to whoever asked. You DON'T need to know the URL — the tool keeps its own index of every dashboard (built from the pages' own titles) and fuzzy-matches whatever name the person used. The welcome modal is auto-dismissed on every board, so the image is always clean.

## When to use
- Anyone asks to see / pull up / screenshot / be sent a dashboard or board by name (city budgets, sales cockpit, crew performance, revenue, production, sales queue, pipeline, etc.).

## How to run
1. Tell the person you're pulling it up (capture takes ~15–25s), then run — pass their words as-is:
   ```
   bash /opt/data/home/dashboard-capture/capture.sh <the board name they said>
   ```
   e.g. `bash /opt/data/home/dashboard-capture/capture.sh city budgets`
2. Read the one-line result and act on it:
   - **`OK <png-path>  (Board Name)`** → success. Reply to the person with the image by putting, on its own line, exactly:
     ```
     MEDIA:<png-path>
     ```
     plus a short caption (e.g. "Here's the live Sales Cockpit 📊").
   - **`AMBIG: A | B | C`** → the name matched more than one board. Ask the person which one they meant (list A/B/C), then re-run with the specific name.
   - **`NOMATCH: <full list>`** → no match. Tell the person the available boards (the list after NOMATCH) and ask which they want.
   - **`ERR: not authorized ...`** → MuniBot lost dashboard access (a play refresh may have wiped it) — tell the Skipper, don't retry blindly.

## Post-restart recovery (if capture fails)

A container restart or rebuild can break three things in this tool. Fix in this order:

1. **Playwright module missing** (`Cannot find module ... playwright-core`):
   ```sh
   cd /opt/data/home/dashboard-capture && npm install playwright-core
   ```
2. **Hardcoded npx path in capture.js** (if the npx cache got wiped, the require points to a dead path):
   - The script should use `require("playwright-core")` (bare module name), NOT a hardcoded `/root/.npm/_npx/...` path. If it still has the old hardcoded path, patch line 4 of `capture.js` to the bare require.
3. **Output directory root-owned** (`EACCES: permission denied, open .../out/...`):
   - The `out/` dir may be owned by root after a rebuild. The script now writes to `/tmp` instead. If `outDir` in capture.js still points to the root-owned path, change it to `/tmp`.

After all three fixes, re-run `bash /opt/data/home/dashboard-capture/capture.sh "city budgets"` to verify.

## Filtering the Sales Cockpit by rep

The default capture shows **"Whole team"** — all reps mixed together. When someone asks about a specific sales rep's pipeline (e.g. "how much does Scott have in Working?"), use the rep-filtered capture:

```sh
cd /opt/data/home/dashboard-capture && set -a && . /opt/data/home/.secrets/trimit-web-login.env && set +a && node capture-rep.js "Scott Griffiths"
```

This logs in, navigates to the Sales Cockpit (`/GSTS/Dashboard-SalesCockpit.cfm`), selects the rep from the Book dropdown, waits for reload, and captures + dumps the column totals as text. The output includes both a screenshot (`OK /tmp/dashboard-salescockpit-<rep>.png`) and the page text with each column's dollar total and account count.

**How it works:** the Book dropdown is a custom UI element (not a native `<select>`). The script finds it by looking for a select containing "Whole team", then fuzzy-matches the rep name against option text. If the rep name doesn't match, it returns the full list of available reps.

**Rep names available** (as of 2026-07-21): Carlos Alcaraz, Ethan Chesley, Garrett Cornish, Rebekah Barker, Scott Griffiths, plus "(No arborist assigned)".

**Reading the data:** the script prints `PAGE_TEXT_START` / `PAGE_TEXT_END` markers with the full board text between them. Column headers show `$<total>` and account count. Individual cards show account name, contact, management company, assigned rep, dates, and dollar amounts. Use `vision_analyze` on the screenshot for visual confirmation of column totals.

## Vision analysis of screenshots — caution with small text

When you capture a dashboard and then use `vision_analyze` to read specific data from the screenshot, **small text (clocks, dates, tiny numbers in system trays or card footers) is unreliable.** Vision models hallucinate plausible-looking but wrong values from tiny pixel patterns. This was confirmed on 2026-07-21: two independent vision passes both read a taskbar clock as "7/28/2023" when the actual date was 7/21/2026 — the user corrected it immediately.

**Rules for vision on captured screenshots:**
- ✅ Good: reading large text, column headers, dollar totals, card titles, layout structure, color-coded sections
- ❌ Bad: reading small clocks/dates in system trays, tiny per-card dollar amounts, fine-print numbers
- If you need exact small numbers, prefer the **PAGE_TEXT output** from `capture-rep.js` (it dumps the board's `innerText`) over vision reading
- Never confidently state a time/date/number from tiny text without hedging — say "looks like" or cross-reference with another source
- When the user corrects a vision-based claim, accept it immediately — don't argue with what they can see on their own screen

## Important URL gotcha

Dashboard URLs in `boards.json` include the `/GSTS/` prefix (e.g. `/GSTS/Dashboard-SalesCockpit.cfm`). If you write custom capture scripts, always prepend the full URL from `boards.json` — NOT just the filename. Navigating to `/Dashboard-SalesCockpit.cfm` (without `/GSTS/`) returns a 404.

## Notes
- It's a **live** capture (current play-server data), read-only (only logs in + screenshots).
- Covers all TRIM IT dashboards automatically. If a new board is added and isn't found, rebuild the index once: `bash /opt/data/home/dashboard-capture/refresh-boards.sh`
- Output goes to `/tmp/` (writable by all users). The old `out/` directory under the skill dir may be root-owned after a rebuild — don't rely on it.
- `capture-rep.js` is at `/opt/data/home/dashboard-capture/capture-rep.js` (NOT in the skill dir — it's a working tool script under the dashboard-capture home).
