---
name: litigation-disclosure-bids
description: "Use when preparing litigation disclosure responses for municipal/public-agency bids (OCTA, Riverside, etc.). Covers the critical legal distinction between contract litigation and co-defendant tort suits, the adversarial review process, and the workflow for researching agency ties from public records."
version: 1.0.0
author: Muni Bot
metadata:
  hermes:
    tags: [litigation, bid-disclosure, municipal-bids, octa, adversarial-review, great-scott-tree-care]
    related_skills: [trim-it-muni-queries]
---

# Litigation Disclosure for Municipal Bids

## When to Use

- Brent asks for help with a litigation disclosure form for a municipal or public-agency bid (OCTA, Riverside, CalTrans, cities, etc.)
- A bid document asks GSTS to disclose contracts where the company has been involved in litigation with the contracting authority
- Brent sends an attorney-prepared litigation list and asks for agency-tie identification

## ⚠️ THE #1 LESSON: Qualification Turns on the Exact Bid Language

**This is the most important takeaway from the OCTA disclosure (July 2026).** The adversarial agent's critique revealed that the entire approach was initially wrong — and the fix was all about reading the bid question literally.

### Typical bid disclosure language (OCTA example):

> "Offeror/Bidder shall list the status of past and present contracts where the firm has either provided services as a prime vendor or a subcontractor during the past five (5) years in which **the contract has been the subject of or may be involved in litigation with the contracting authority**."

### This question has FOUR gating elements — ALL must be met:

1. A specific **contract** existed between GSTS and a public agency
2. GSTS **provided services** as prime vendor or subcontractor on that contract
3. **That contract** was the subject of or involved in litigation
4. The litigation was **with the contracting authority** (i.e., GSTS vs. the agency, adverse parties)

### Critical distinction that the adversarial agent caught:

**Being a CO-DEFENDANT with a city in a tort suit is NOT "litigation with the contracting authority."**

In the OCTA case, two Long Beach lawsuits (Robinson v. Long Beach, Varley v. Long Beach) initially appeared to qualify because the City of Long Beach was a named party. But in both cases:
- GSTS and the City were **on the SAME SIDE** (co-defendants)
- A third-party plaintiff sued the City, and GSTS was impleaded as a Doe defendant
- The GSTS–Long Beach tree maintenance **contract was never the subject** of the litigation
- Therefore: **NOT responsive** to the disclosure question

**The result: GSTS had ZERO qualifying contracts, not two.** This was the difference between a clean disclosure and an over-disclosed one that would have made GSTS look litigation-exposed.

### How to apply this:

1. **Start from the CONTRACT side, not the litigation side.** Begin with GSTS's municipal contract roster (TRIM IT, `ProjectGroupDefID = 11`). Ask: "Was any of these contracts in litigation with the agency?"
2. **Do NOT start from the litigation list and retrofit agency labels.** That's the wrong direction and leads to over-disclosure.
3. **Test each case against all four gating elements.** If any element fails, the case is non-responsive.
4. **When in doubt, the answer leans toward "non-responsive."** Employment disputes, vehicular accidents, PAGA claims, and infraction citations are almost never contract-performance litigation.

## Common Case Categories and Their Typical (Non-)Qualification

| Case Type | Typically Responsive? | Why |
|-----------|----------------------|-----|
| Contract performance dispute with a city | ✅ YES | Contract + agency + litigation = all four elements |
| Premises liability / personal injury (GSTS as co-defendant with city) | ❌ NO | GSTS and city are co-defendants, not adverse parties; contract not at issue |
| Employment / wrongful termination | ❌ NO | Internal employer-employee dispute; no contracting authority involved |
| PAGA / labor code claims | ❌ NO | Administrative labor proceeding; no contracting authority involved |
| Vehicular accident / auto PI | ❌ NO | Insurance-managed tort; no contracting authority involved |
| Small claims | ❌ NO | Localized dispute; almost never contract-related |
| Vehicle equipment infractions | ❌ NO | Not litigation; administrative citation |

## Workflow

### Step 1: Read the Exact Bid Language
- Copy the disclosure requirement verbatim from the bid document
- Identify the gating elements (contract, services provided, litigation, with contracting authority)
- Note the lookback period (typically 5 years)
- Note the disclosure scope (does it also ask about claims, settlements, arbitrations, administrative proceedings, investigations?)

### Step 2: Start from Contracts, Not Litigation
- Query TRIM IT for GSTS's municipal contract roster (`ProjectGroupDefID = 11`)
- This is the universe of contracts that COULD potentially qualify
- Any litigation not involving an agency on this list is automatically non-responsive

### Step 3: Research Agency Ties for Each Litigation Case
- Search public records: DocketAlarm, DocketBird, UniCourt, court portals
- For LA County cases: DocketBird and DocketAlarm have good coverage
- For Orange County cases: OC court records (courtindex.occourts.org) are NOT web-indexed — attorney files are the primary source
- For Long Beach cases: LA County Superior Court system

### Step 4: Apply the Four-Element Test
- For each case, test against all four gating elements
- Label each case: "Responsive" or "Non-responsive" with reasoning
- If the answer is zero responsive cases, state that clearly as the lead finding

### Step 5: Spin Up Adversarial Agent
- Delegate to a subagent with the draft and the exact bid language
- Ask it to critique: accuracy, completeness, risk, language, and whether the draft answers the ACTUAL question
- The adversarial agent's most valuable contribution is catching over-disclosure and misclassification

### Step 6: Produce Draft Two
- Incorporate adversarial critique
- Lead with the direct answer to the bid question
- List non-responsive cases separately for transparency (if the form requires it)
- Strip all internal metadata (researcher names, AI attribution, process notes)

### Step 7: Flag Items for Attorney Review
- Any case with insufficient public data should be flagged for attorney confirmation
- The attorney has files that public records don't — use that as the primary source
- Produce a numbered checklist of specific items counsel should confirm

## Key Pitfalls

1. **Over-disclosure.** Listing all litigation when the answer is "zero qualifying contracts" makes GSTS look more litigation-exposed than the question requires. Scope to what's asked.
2. **Co-defendant ≠ adverse party.** Being sued alongside a city is NOT litigation "with" that city. This is the #1 misclassification risk.
3. **Starting from the wrong direction.** Starting from the litigation list and working toward contracts leads to over-disclosure. Start from contracts and work toward litigation.
4. **PAGA cases.** Pending PAGA actions are a red flag in bid contexts. Don't disclose them prominently if they're not responsive — they invite scrutiny of employment practices.
5. **Internal metadata leaking.** Never let "Researcher: Muni Bot," draft versioning, or process notes reach a public agency. Strip before submission.
6. **"Dismissed" is ambiguous.** Distinguish between judgment for GSTS, settlement ($X), voluntary dismissal, and dismissal after proof of correction.
7. **OC court records.** Orange County Superior Court civil cases are NOT searchable by case number through public web portals. Do not rely on web search alone for OC cases — use attorney files.
8. **Editorial language.** Remove "routine," "de minimis," "industry-wide" — state facts only in legal register.

## Email Rule

Per Brent's directive: only send email when explicitly asked. Only send to Brent (bbeller@gstsinc.com) or Jason. Drafts are for Brent's review before anything goes external.

## Sources Used (OCTA 2026 Disclosure)

- DocketAlarm: https://www.docketalarm.com (LA County Superior Court cases)
- DocketBird: https://www.docketbird.com (LA County civil case index)
- Long Beach Post: https://lbpost.com
- EIN Presswire: https://www.einpresswire.com
- OC Court Case Index: https://courtindex.occourts.org (not web-indexed for civil)
- TRIM IT database: Municipal contract verification (read-only)
- Attorney-prepared disclosure document: Primary source for case details
