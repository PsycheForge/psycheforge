# PsycheForge Triage — 5 Delegate Validation Test

**Status:** Test packet for B-validation interviews (post-2026-05-05 pivot to triage-only).
**Goal:** Determine whether structured triage output, by itself, materially helps a delegate make a governance decision.
**Decision tree:** ≥4/5 yes → ship triage-only product · ≤2/5 yes → defer to A pivot (context aggregator).

---

## How to use this packet

1. Identify a candidate delegate (active in Solana DAO governance, ideally one of your 5 anonymous interviewees who said "I'd try the beta").
2. Send them the **outreach DM** ([template below](#outreach-dm-template)).
3. When they accept, share the **triage output** ([test_pack_mip21_triage.md](test_pack_mip21_triage.md)) — a real PsycheForge triage of a real recent Marinade DAO proposal (MIP-21).
4. Run the **interview script** ([4 questions below](#interview-script)). 10–15 min total.
5. Capture answers verbatim where possible. **Do not lead** — let them complain about gaps before naming them.
6. After they answer, **debrief**: tell them the actual vote outcome was 99.6/0.4 approve, and ask if that changes their reaction.

---

## Why MIP-21 specifically

The triage flagged **two HIGH-severity red flags** on this proposal:

- `backdoor_permission` HIGH — fee redirect to Council wallet has no on-chain sunset
- `centralization` HIGH — monthly transfer mechanic relies on manual Council execution, no enforcement

The community then approved the proposal **99.6/0.4** — nearly unanimous despite the flags.

This is the perfect test material because it forces the delegate to react to a tension:

- *"Did the AI see something the community missed?"* (skill-positive interpretation)
- *"Or is the AI over-flagging stuff that doesn't actually matter to this DAO?"* (skill-skeptic interpretation)

Either reaction is informative. The key signal is whether the structure (citations + categorized flags + open questions) helped them THINK about the proposal more sharply, regardless of whether they agreed with the flags.

---

## Outreach DM template

Personalize `{handle}` and any DAO context. Don't paste literally — the template should not be visible in the DM itself.

> Hey {handle} — earlier you said you'd be open to trying a governance triage tool I've been building. I have a 10-minute version of that ready: I'd send you the structured analysis output for one real Marinade proposal (MIP-21, recent), and ask 4 short questions about whether the format actually helped you reason about the proposal.
>
> Not a pitch, not a demo call — just a direct read on whether structured triage is a real tool or noise. If you can spare 10–15 minutes async (DM or voice, your pick), I'll send the packet. Outcome of MIP-21 is already known so this isn't a forecasting test — it's about whether the *analysis structure* helps a delegate.
>
> Worth your time?

---

## Interview script

Send the triage output ([test_pack_mip21_triage.md](test_pack_mip21_triage.md)). Give them ~5 minutes to read it. Then:

### Q1. Did this output help you think about the proposal more clearly?

*Listen for:* concrete pieces they latched onto vs ignored. **Not** "was the AI right" — that's Q3. Q1 is about decision-support quality.

If they say "yes": Why specifically? Which section?
If they say "no": What was missing or distracting?

Capture the verbatim phrase if they describe value. Especially important:
- "I would have missed [X]" — direct value signal
- "I already knew that" — saturation / no value
- "I don't trust this" — trust blocker, ask why

### Q2. Which part was most useful — and which part felt like noise?

*Listen for:* differential signal across sections. We expect different delegates to weight differently:

- TL;DR vs detailed red flags vs questions list vs stakeholders
- "Citations are essential" vs "I just want the bullet"

Don't lead. Let them rank in their own words.

### Q3. Would you have voted differently if you'd seen this before voting?

(After they answer: tell them the vote was 99.6/0.4 approve.) Did that change your reaction? Are you surprised the community approved? Are you now more or less skeptical of the AI's flags?

*Listen for:*
- "The flags were valid but irrelevant for this DAO" → calibration fit
- "The flags should have changed the outcome" → AI sees real risks the community ignores (PsycheForge-positive)
- "The flags were just noise" → over-flag problem

### Q4. Would you use this for every proposal you face? How many proposals per week?

*Listen for:*
- Frequency baseline
- Conditions: "only for proposals over $X treasury impact" / "only for ones I'm not deeply familiar with" / etc.
- Pricing tolerance: implicit ("I'd pay" / "if it's free") — don't ask price directly here, save for closing

### Closing

> Thanks. Two last questions:
>
> If a tool produced this kind of output for any Solana proposal you cared about, on demand, what would make you actually subscribe vs just try once?
>
> Anyone else you'd recommend I show this to?

---

## Scoring rubric

For each delegate, capture:

- **Q1 score:** 1 (no value) / 2 (slight) / 3 (real value) / 4 (changed how I think) / 5 (I want this on every proposal)
- **Q2 ranking:** ordered list of sections (citations, red flags, questions, TL;DR, stakeholders) by stated usefulness
- **Q3 reaction:** flags-valid-but-irrelevant / flags-should-have-mattered / flags-noise / mixed
- **Q4 frequency:** proposals-per-week + conditions
- **Subscription intent:** subscribe-now / would-with-X-feature / try-but-not-pay / no-interest

Aggregate decision after all 5:

- **≥4 with Q1 ≥ 3:** ship the triage-only product. Risk A genuinely closing.
- **3 with Q1 ≥ 3:** soft signal, do 5 more interviews before committing.
- **≤2:** triage alone insufficient. Pivot to A (context aggregator) more urgently.

---

## What this test does NOT do

- Does not test prediction quality — that's deferred to N=50+ calibration
- Does not test against contested live proposals — easier to capture reactions on closed votes
- Does not measure pricing tolerance directly — implicit signal only, deeper pricing test comes in cohort 2

These are deliberate scope cuts. We're answering one question: **is structured triage, by itself, valuable to a delegate?**
