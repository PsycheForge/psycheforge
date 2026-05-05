# Outreach One-Pager — Post-N=7 Devnet Batch

Purpose: convert the [N=7 report](batch_n7_devnet_report.md) into assets you can actually send. Pick what fits the channel; don't send all of them at once to the same person.

Three artifacts here:
1. **Loom video script** (~90–120 seconds)
2. **X thread** (5 tweets)
3. **DM / forum-post templates** — Marinade · Jupiter · Realms / governance figures

The single ask across all: **20 minutes on a call to validate or disprove the approach.** Not selling, not pitching, not asking for delegation. You're testing a hypothesis.

---

## 1. Loom video script (~90 seconds)

Screen-share the [batch_n7_devnet_report.md](batch_n7_devnet_report.md) throughout. Speak while scrolling.

**[0:00 — 0:12] Hook**

> I built an AI agent that triages Solana DAO proposals. Instead of claiming some accuracy number on a slide, I commit each prediction on-chain before the vote closes and score it — difficulty-weighted — after. Today I'm showing the first seven real live proposals the agent ran against. The track record is on devnet, and anyone can audit it.

**[0:12 — 0:35] The number** *(scroll to "Current accuracy")*

> Here's the current agent accuracy: 51.05%. That's weighted by vote difficulty — contested votes count more, unanimous ones contribute effectively zero. Naive "how many did you get right" would be four out of seven, about 57%. I'm showing the lower weighted number because the whole point of this tool is to make accuracy verifiable, not marketable. If I showed you 57%, I could be gaming that by only predicting obvious calls. The math prevents that.

**[0:35 — 0:60] Show the table** *(scroll to per-proposal breakdown)*

> Here's every prediction. Seven proposals across Marinade, Jupiter, Jito. The hardest one in the batch — the Jupiter net-zero emissions vote, which was 75/25 contested — we predicted approve, and the community approved it. That one call alone is 77% of the total weight. The three wrong calls were all reject predictions on proposals with technical red flags that the community passed anyway. That's a v0.1 prompt bias I can fix.

**[0:60 — 0:80] Verify** *(scroll to "Audit — don't trust")*

> Don't trust any of this. Click the Reputation PDA link. Inspect the raw account data on Solana Explorer. Every prediction transaction has its own link. The on-chain numbers are the scoreboard — this document just explains them.

**[0:80 — 0:120] Ask**

> I'm looking for 20 minutes with Solana DAO delegates — any DAO, any size. Not selling anything. I want to know: is this kind of verifiable agent accuracy something you'd use? What would break the trust? What kinds of proposals would you most want triaged? If you'd be willing to talk, DM me. I'll send you a calendar link, no pitch deck, just questions.

---

## 2. X thread (5 tweets)

**1/ Hook**

I built an AI agent that triages Solana DAO proposals.

Instead of claiming "90% accuracy" on a slide, I commit each prediction on-chain *before* the vote closes and score it — difficulty-weighted — after.

Here's the first 7 live proposals. [link]

**2/ The number**

Current accuracy: 51.05% (difficulty-weighted, N=7).

Naive 4/7 = 57%. Weighted is lower because contested votes count more than unanimous ones.

If I showed you the naive number I could be gaming it. The math prevents that.

**3/ What it got right**

Hardest call in the batch: Jupiter net-zero emissions (75/25 contested, entropy 0.81). Difficulty weight 8064.

Skill predicted approve. Community approved. That one correct call is 77% of the total weighted-correct signal.

[link to Explorer: prediction PDA]

**4/ What it got wrong (honestly)**

3 wrong predictions: MIP-18 Marinade, MIP-21 Marinade, JIP-28 Jito. All 3 were `reject` calls; community approved each by wide margins (84/16, 99/1, 95/5).

Pattern: skill over-weighted technical red flags when treasury wasn't directly at risk. That's a v0.1 prompt bias I can fix. Fix is documented. Next batch will test it.

**5/ Ask**

Looking for 20 min with Solana DAO delegates. Any DAO, any stake size. Not selling. Just want to know if verifiable agent accuracy matters to you.

Auditable record: [explorer link]
Full report: [markdown link]

Reply or DM.

---

## 3. DM / forum-post templates

Personalize the placeholders `{handle}`, `{proposal/topic}`, `{why_them}` before sending. No one likes copy-paste outreach. The template is scaffolding, not the message.

### 3a. Marinade community — Cerba, helloiamvu, or any active MNDE delegate

**Channel:** Marinade Discord #governance, or direct DM if you have it. Fallback: forum reply on a current MIP thread.

> Hey {handle} — saw you on {MIP-NN} / {thread}. I've been building a proposal triage tool specifically for Solana DAOs. Unlike the existing chatbot-style tools, it commits its predictions on-chain *before* votes close and gets scored against actual outcomes — no marketing claims, you can audit the record.
>
> Just finished a first batch of 7 proposals including MIP-15, MIP-17, MIP-18, MIP-21. Full track record on devnet, verifiable in a browser. The skill predicted MIP-18 and MIP-21 as `reject` and got both wrong — community approved them by wide margins — so I have specific calibration data to work through.
>
> Would you be up for 20 min to compare notes? I'd love to understand how you read those two proposals, and whether an auditable agent would be useful (or noise) for delegates who follow multiple DAOs.
>
> Report: {paste batch_n7_devnet_report.md github/gist link}
> Agent on-chain: [explorer.solana.com/.../3PDUJBj2LswT...](https://explorer.solana.com/address/3PDUJBj2LswT4fnUmGMMZrP3vriapUPRWUFJ66FRkoVS?cluster=devnet)

### 3b. Jupiter community — Kash (net-zero proposer) or active JUP staker

**Channel:** Jupiter discuss.jup.ag DM, or X reply to a governance tweet. Fallback: post in Jupiter Discord #governance-discussion.

> Hey {handle} — I included the net-zero emissions proposal in a live-proposal batch I just ran through an on-chain-scored governance triage tool. The skill predicted Option 2 approve at 55% confidence and got it right; it was the hardest call in the batch (entropy 0.81) and carries most of the weight in the current accuracy score.
>
> I'd love 20 min on a call — two things I'd want your read on:
> 1. Whether the flags the skill surfaced (centralization via "Jupiter absorbs team sales", bundling three emission sources into one vote) matched your own concerns as a staker or proposer.
> 2. Whether a public, auditable track record of predictions would change how JUP delegates (or the DAO itself) interact with analysis tools.
>
> Not selling anything. Report + on-chain audit: [link]

### 3c. Realms / Solana Governance infra team

**Channel:** Realms Discord #governance or forum. Could also reach via Solana Foundation governance leads.

> Hi {handle} — different ask than the usual DM: not a DAO asking Realms for a feature, but a governance-adjacent builder sharing a tool that sits on top of SPL Governance and might be useful for Realms users.
>
> I've built a skill chain (governance-triage + prediction-writer, open-source, MIT) plus an on-chain reputation Anchor program that scores agent accuracy difficulty-weighted. Just closed a first N=7 batch on devnet covering Marinade, Jupiter, and Jito proposals — all publicly audited.
>
> Two reasons I'm reaching out:
> 1. Curious whether Realms would ever want to surface "predicted outcome + confidence + auditable accuracy history" as a UX element next to a proposal. Not asking for a commit, just a read on whether that's the direction you're thinking.
> 2. Risk C on our side is regulatory posture. Our skill is hard-ruled to produce predictions (falsifiable claims), never recommendations. I'd love a sanity check from the Realms team on whether that distinction holds up from your legal/UX perspective.
>
> 20 min, no slides. Report: [link]. On-chain: [explorer link].

---

## Before you send any of these

Sanity checks so the outreach doesn't blow up:

- **Personalize.** Remove every `{handle}` / `{MIP-NN}`. If it reads like a template, delete it.
- **Rate-limit.** 2–3 DMs per day per DAO, staggered across weekdays. Blasting governance channels earns mutes.
- **Respond within 4 hours.** If someone says "sure, send a link," be alive on the reply.
- **Track responses.** Keep a private list (name, DAO, date, state) — do not dox in any public channel.
- **No pitch deck.** The on-chain audit is the pitch. If they ask for slides, say "no slides — let me screen-share the Explorer tab."

When a call lands, use `docs/customer-discovery-template.md` (internal doc, not public) for interview structure. The outcome you're after: ≥3 of 5 interviewees say they'd try a beta, ≥1 written expression of interest. That closes Risk A.
