# Knowledge Vault Maintenance — Self-Improvement Protocol

Muni Bot maintains its own knowledge through two automated mechanisms plus
a standing rule to surface them at chat start. Set by the Skipper, 2026-07-17.

## The Three Components

### 1. End-of-Day Knowledge Sweep (nightly, 11 PM PT)

**Cron job:** `bf46e2d41835` — "End-of-Day Knowledge Sweep"
**Schedule:** `0 6 * * *` (6:00 AM UTC = 11:00 PM Pacific)

**What it does:**
- Reviews all sessions from the last 24 hours
- Identifies genuinely new learnings (TRIM IT gotchas, query patterns, Brent
  preferences, municipal facts, workflow discoveries)
- Writes each as a NEW atomic note in the vault (`concepts/` or `references/`)
- Patches the skill's Common Pitfalls list if new query/schema issues were found
- Commits to git
- Goes silent (`[SILENT]`) if nothing new was learned

**What NOT to capture** (transient, not durable):
- Environment-dependent failures (missing binaries, path mismatches)
- Session-specific errors that resolved on retry
- One-off task narratives
- Negative claims about tools ("X doesn't work")

### 2. Weekly Vault Housekeeping (Sundays, 9 AM PT)

**Cron job:** `f7f5d8f8586d` — "Weekly Vault Housekeeping"
**Schedule:** `0 16 * * 0` (4:00 PM UTC = 9:00 AM Pacific Sunday)

**What it does:**
- Scans the vault for orphaned files (no incoming wikilinks, not foundational)
- Identifies duplicate/overlapping notes
- Flags stale info (60+ days old with specific data that may have changed)
- Archives to `_archive/` (NEVER deletes) with a reason header
- Updates README.md and skill references to remove dead links
- Goes silent if the vault is already clean

**Foundational files (never archive):**
- `00-start-here/README.md`
- `references/brent-profile.md`
- Anything in `brent-history/`

**Conservative rule:** when unsure whether something is orphaned or duplicate,
LEAVE IT IN PLACE and note it for review.

### 3. Standing Rule (visible at every chat start)

Both maintenance rules are saved in user-profile memory so they're injected
into every new session. This ensures the agent knows about the maintenance
schedule even if a cron job is paused or fails.

## Vault Structure Reference

```
/opt/data/home/municipal-knowledge/
├── 00-start-here/README.md     ← vault map with [[wikilinks]]
├── concepts/                   ← rules, how-it-works (NEW notes go here)
├── references/                 ← facts, lookups, detailed workflows
├── query-playbook/             ← verified SQL patterns
├── brent-history/              ← ingested source documents
├── _archive/                   ← archived files (never deleted)
└── .git/                       ← version-controlled
```

**Path warning:** always use the absolute path `/opt/data/home/municipal-knowledge/`.
The `~/home/` shorthand expands to `/opt/data/home/home/` (double path) because
`$HOME=/opt/data`.

**Git identity (per-repo):**
```bash
cd /opt/data/home/municipal-knowledge
git config user.email "MuniBot.gsts@gmail.com"
git config user.name "Muni Bot"
```

## Atomic Note Writing Rules

When writing a NEW note (from the nightly sweep or during a session):

1. **Location:** `concepts/` for rules/how-it-works, `references/` for facts/lookups
2. **Filename:** fresh kebab-case (e.g. `maps-locationid-join-gotcha.md`)
3. **Frontmatter:** `title`, `type`, `tags`, `updated` (today's date)
4. **Body:** include `[[wikilinks]]` to cross-link related notes
5. **Write NEW notes — don't edit existing curated ones** (new notes are
   auto-collected to the shared vault; edits to existing notes are not)
6. **Track-1 only** — never write arbor-core / Track-2 / confidential material

## Cron Job Management

To check job status:
```
cronjob action=list
```

To pause/resume a sweep:
```
cronjob action=pause job_id=bf46e2d41835    # nightly sweep
cronjob action=pause job_id=f7f5d8f8586d    # weekly housekeeping
```

To run manually (e.g. after a big session):
```
cronjob action=run job_id=bf46e2d41835
```

## Diagnosing a failed sweep run

When the nightly sweep (or any vault cron job) comes back `last_status: error`,
the failure is almost always at the model/provider layer, not the prompt. The
full record is on disk — work the dump, not the prompt.

### 1. Confirm and locate

```
cronjob action=list        # read last_status, last_run_at, state; grab job_id
```

Two artifacts are written per run under `$HERMES_HOME` (`/opt/data` here):
- **Output log** — what the agent produced before dying:
  `$HERMES_HOME/cron/output/<job_id>/<YYYY-MM-DD_HH-MM-SS>.md`. A long history
  of successful `.md` files here means the job is healthy in general and the
  failure is recent/transient. The failed run's file ends with a `## Error`
  section (e.g. `RuntimeError: HTTP 401: invalid x-api-key`).
- **Request dump** — the exact HTTP request + response that failed:
  `$HERMES_HOME/sessions/request_dump_cron_<job_id>_<start>_<end>_<pid>.json`.
  Glob by job_id:
  `find $HERMES_HOME/sessions -name "request_dump_cron_<job_id>*"`.

### 2. Parse the dump (don't eyeball the blob)

```python
import json
d = json.load(open("request_dump_cron_<job_id>_*.json"))
print("REASON:", d.get("reason"))                       # non_retryable_client_error = hard-killed (4xx, not retried)
req = d.get("request", {})
print("URL:", req.get("url"))                           # which provider endpoint actually got the call
print("MODEL:", req.get("body", {}).get("model"))
print("AUTH:", req.get("headers", {}).get("Authorization"))  # 'Bearer None' = key env var unset in cron env
resp = d.get("response") or d.get("error") or {}
print("STATUS:", resp.get("response_status") or resp.get("status_code"))
print("BODY:", json.dumps(resp.get("body", {}), indent=2))   # upstream provider's error, verbatim
```

Key signatures:
- `reason: non_retryable_client_error` → 4xx (except 429), NOT retried, will
  repeat identically every tick until config is fixed. (5xx / 429 are retried.)
- `Authorization: Bearer None` → the call reached a provider whose key is
  unset in the **cron runtime** (cron sessions don't inherit the interactive
  session's `.env`/memory the same way — a key that works in chat can be
  missing in a cron run).
- `request.url` tells you which provider actually got the call vs. the
  configured primary — a mismatch means the call fell through the chain.

### 3. Check pinning vs. the live chain

```bash
# job pinning (null/null = inherits live chain at runtime)
python3 -c "import json; [print(j['name'],'model=',j.get('model'),'provider=',j.get('provider')) for j in json.load(open('/opt/data/cron/jobs.json'))]"
# live provider chain + fallbacks
grep -iE "model|provider|base_url|fallback_providers|api_key" /opt/data/config.yaml
```

A job with `model: null / provider: null` inherits the live chain — so a
primary blip can cascade to a fallback that was never actually exercised
before (the latent bomb). This bit the nightly sweep on 2026-07-24: primary
`zai-anthropic`/`glm-5.2` blipped → fell through to the `anthropic`/
`claude-opus-4-8` fallback → `ANTHROPIC_API_KEY` unset in cron env → 401.

### 4. Fix (pin preferred)

For scheduled jobs, **determinism beats resilience.** Pin the job to the
known-good provider+model so it never drifts to a keyless fallback:
```
cronjob action=update job_id=<id>   # set model + provider explicitly
# or: hermes cron edit <id>
```
Alternatives if you want the fallback genuinely available: set the missing
key env var in `.env`, or remove the broken `fallback_providers` entry so a
primary blip can't cascade into a hard 401. Avoid leaving a keyless fallback
in the chain "for later" — it only fires under load, when you're not watching.

### 5. Verify

Trigger an immediate run instead of waiting for the schedule:
```
cronjob action=run job_id=<id>      # or: hermes cron run <id>
```
Re-check `last_status` on the next tick. A successful run also writes a new
timestamped `.md` under `cron/output/<job_id>/` — its presence (and the
absence of a `## Error` footer) confirms recovery.

### What NOT to do
- Don't treat a one-off transient blip (5xx, 429) as a config bug — those
  are retried automatically. Only `non_retryable_client_error` repeats.
- Don't capture the specific dead key as a durable rule — keys change. The
  durable lesson is the *diagnostic pattern* and the *pin-preferred* fix.
