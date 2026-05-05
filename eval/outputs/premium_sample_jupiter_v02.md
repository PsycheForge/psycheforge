# Bundles Jupuary (700M JUP), team vesting, and Mercurial stakeholder emissions…

**Source:** https://discuss.jup.ag/t/proposal-net-zero-emissions/39948
**Generated:** 2026-05-04
**Analyzed by:** PsycheForge `governance-triage` skill

> **This is analysis, not voting advice.** The skill is hard-ruled to never recommend a vote. Every claim below is grounded in a verbatim citation from the proposal text — verify the citations yourself.

## TL;DR

Bundles Jupuary (700M JUP), team vesting, and Mercurial stakeholder emissions (~1.2B total) into two-option vote. Option 1 continues planned distributions. Option 2 postpones Jupuary, pauses team emissions with 'JUP credit' substitution, and accelerates Mercurial vesting with offset purchases by Jupiter entity.

## Treasury Impact

- **Direction:** `unknown`
- **Amount:** *not specified in USD*
- **Confidence:** `low`

> *Vote-dependent: Option 1 distributes 700M JUP ('Distribution commences ~2 weeks after, beginning with 200M $JUP'); Option 2 returns to treasury ('Return all 700 million tokens to Community Cold Multisig') but commits Jupiter entity to unquantified offset purchases ('Purchase equivalent tokens for Jupiter treasury when tracked wallets sell'). No USD valuation provided for any scenario.*

## Red Flags (6)

### 1. `token_dilution` — severity **high**

Modifies emission trajectory for approximately 1.2 billion JUP tokens (over 10% of circulating supply) through postponement, indefinite pause, and accelerated vesting with offsets. Skill mandates flagging any supply-trajectory change regardless of direction.

> ***Net Impact:** Reduces emissions from approximately 1.2 billion to effectively zero tokens.*

### 2. `unbounded_spend` — severity **high**

No dollar cap on Jupiter entity's commitment to purchase tokens offsetting Mercurial stakeholder sales. Obligation continues 'throughout the year' with price exposure determined by future market conditions and sale timing of ~300 wallets.

> *Purchase equivalent tokens for Jupiter treasury when tracked wallets sell or move tokens to exchanges. Continue offsetting throughout the year*

### 3. `vague_kpi` — severity **medium**

Jupuary postponement revisit trigger defined as 'when market conditions improve' with no quantified threshold (price target, volatility metric, or time-based review). Team emissions pause is 'indefinitely' with no success criteria or termination conditions.

> *Revisit when market conditions improve... Team Reserve emissions paused indefinitely*

### 4. `missing_milestone` — severity **medium**

Mercurial offset program lacks review checkpoints, spending caps, or performance evaluation milestones. JUP credits system has no described valuation, redemption rules, or audit mechanism.

> *Continue offsetting throughout the year... Provide 'JUP credits' against Jupiter balance sheet instead*

### 5. `technical_risk` — severity **medium**

Off-chain wallet tracking of ~300 addresses and CEX sale detection required for offset execution. No described methodology for identifying exchange deposits or preventing double-counting. Single point of failure if tracking system malfunctions.

> *Track approximately 300 wallets holding '99% of allocated $JUP'... Purchase equivalent tokens for Jupiter treasury when tracked wallets sell or move tokens to exchanges*

### 6. `centralization` — severity **medium**

Community Cold Multisig composition and signing threshold not specified. 700M JUP tokens (7% of implied supply) will be custodied by unidentified keyholders with no described operational security or governance structure.

> *Returned Jupuary Tokens: Secured in Community Cold Multisig, inaccessible without future DAO vote*

## Stakeholders

- **Kash** — `proposer` · *"**Author:** Kash"*
- **Jupuary recipients (users/stakers)** — `beneficiary` · *"**Jupuary** – Annual airdrop rewarding loyal users/stakers with governance power"*
- **Team members** — `beneficiary` · *"**Team Vesting** – Token deliveries to team members for ecosystem growth incentive alignment"*
- **Mercurial Stakeholders** — `beneficiary` · *"**Mercurial Stakeholders Vesting** – 5% of total supply distributed to Mercurial token holders and i…"*
- **Jupiter entity** — `counterparty` · *"Jupiter absorbs team member token sales directly"*
- **Community Cold Multisig** — `affected_group` · *"Return all 700 million tokens to Community Cold Multisig"*
- **ParaFi** — `affected_group` · *"**ParaFi Voting:** Locked $35M token allocation unavailable for governance"*

## Questions to ask before voting

1. What is the exact composition, signing threshold, and operational security setup for the Community Cold Multisig that will hold 700M returned Jupuary tokens?
2. How will Jupiter entity fund the Mercurial offset purchases - from DAO treasury, from protocol revenue, or from team/investor capital?
3. What specific metric (JUP price, market cap, 30-day volatility, treasury size) defines 'market conditions improve' for revisiting postponed Jupuary, and what threshold triggers a new DAO vote?
4. If a tracked Mercurial wallet sells 10M JUP during a price spike, is Jupiter committed to purchasing 10M JUP at that elevated price, and what is the maximum dollar exposure per transaction?
5. How are 'JUP credits' valued (locked rate, floating rate, discount to market), can team members redeem them on-demand, and who audits the balance sheet?
6. What happens if Jupiter entity cannot fulfill offset purchase obligations due to capital constraints or market liquidity issues - does the DAO backstop, or do Mercurial stakeholders receive uncompensated dilution?

## What this analysis could NOT read

**Overall confidence:** `medium`

The skill flagged these sections as unreadable from the proposal text alone (external references, linked specs, addresses not included, etc.):

- Community Cold Multisig composition and signing threshold
- Specific addresses for ~300 tracked Mercurial wallets
- Total JUP supply (implied 10B but not stated)
- Team vesting schedule amounts and timing
- JUP credits valuation and redemption mechanics
- Jupiter balance sheet details and capital allocation authority
- Mercurial offset tracking methodology and CEX detection system

---

## Outcome prediction — Premium tier

- **Predicted outcome:** `0` (approve / yes / pass)
- **Confidence:** 5500 bps (55.0%)

**Reasoning:**

> Core token economics proposal by Kash affecting 1.2B JUP (~10% supply). Two HIGH flags (token_dilution, unbounded_spend) plus four MEDIUM flags present. Calibration guidance indicates Solana communities tolerate process/implementation concerns on emission decisions when no backdoor_permission exists. Treasury_impact vote-dependent (unknown) not direct drain. Triage confidence=medium and multiple unreadable sections cap prediction confidence. Contested major-supply decision with genuine uncertainty.

**Key triage signals that drove the prediction:**

- `red_flag:token_dilution:high`
- `red_flag:unbounded_spend:high`
- `red_flags:6 total (2 high + 4 medium)`
- `treasury_impact:unknown`
- `stakeholders[0].name:Kash`
- `triage.confidence.overall:medium`

This prediction is **falsifiable**. After the vote closes, it is scored on-chain (difficulty-weighted) against the actual outcome. The agent's [Reputation PDA on Solana devnet](https://explorer.solana.com/address/3PDUJBj2LswT4fnUmGMMZrP3vriapUPRWUFJ66FRkoVS?cluster=devnet) accumulates the public, auditable accuracy history.

---

_Generated by **PsycheForge** (Premium tier). This is analysis, not voting advice. The skill is hard-ruled to never recommend how to vote — it surfaces what's worth questioning. Every claim above carries a verbatim citation; if any cite doesn't match the proposal, the analysis is invalid. Source code: pending public release (MIT)._
