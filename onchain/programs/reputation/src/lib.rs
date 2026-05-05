//! Reputation program (v0.1.0)
//!
//! See `docs/reputation-program-design.md` for the full design.
//! All seven v0.1 instructions implemented: `initialize_config`,
//! `register_agent`, `create_proposal`, `submit_prediction`,
//! `resolve_proposal`, `finalize_prediction`, `transfer_resolver`.
//! Red-team scenario tests live in `tests/red_team.ts`.

use anchor_lang::prelude::*;

declare_id!("85huMKVbSddkbZiSk4XUBUSxsZS39tbd3sLp17viJJqH");

#[program]
pub mod reputation {
    use super::*;

    /// One-time program setup. Sets the resolver authority on the
    /// `ProgramConfig` PDA. Should be called in the same transaction / script
    /// as `anchor deploy` to prevent a front-running attacker from claiming
    /// the resolver seat (known v0.1 hole — see design doc §2).
    pub fn initialize_config(ctx: Context<InitializeConfig>, resolver: Pubkey) -> Result<()> {
        let config = &mut ctx.accounts.config;
        config.resolver = resolver;
        config._reserved = [0u8; 64];
        Ok(())
    }

    /// Registers a new agent. Creates the `AgentReputation` PDA and zeroes
    /// all counters. Idempotent at the caller — the second call fails at
    /// account creation because the PDA already exists.
    pub fn register_agent(ctx: Context<RegisterAgent>) -> Result<()> {
        let reputation = &mut ctx.accounts.reputation;
        reputation.agent_pubkey = ctx.accounts.agent.key();
        reputation.total_predictions = 0;
        reputation.total_resolved = 0;
        reputation.weighted_correct_numerator = 0;
        reputation.weighted_difficulty_denominator = 0;
        reputation.eligible_proposals_seen = 0;
        reputation._reserved = [0u8; 64];
        Ok(())
    }

    /// Creates a new proposal entry. Only callable by the resolver recorded
    /// in `ProgramConfig`. Validates num_choices and timing before creating
    /// the `Proposal` PDA. Outcome and difficulty fields stay zero until
    /// `resolve_proposal` is called.
    pub fn create_proposal(
        ctx: Context<CreateProposal>,
        proposal_id: [u8; 32],
        dao_id: [u8; 32],
        voting_closes_at_slot: u64,
        num_choices: u8,
    ) -> Result<()> {
        require!(
            (2..=8).contains(&num_choices),
            ReputationError::InvalidNumChoices
        );
        let now = Clock::get()?.slot;
        require!(
            voting_closes_at_slot > now,
            ReputationError::VotingAlreadyClosed
        );

        let proposal = &mut ctx.accounts.proposal;
        proposal.proposal_id = proposal_id;
        proposal.dao_id = dao_id;
        proposal.voting_closes_at_slot = voting_closes_at_slot;
        proposal.num_choices = num_choices;
        proposal.resolved = false;
        proposal.final_outcome = 0;
        proposal.vote_distribution_bps = [0u16; 8];
        proposal.difficulty_bps = 0;
        proposal.resolver = ctx.accounts.resolver.key();
        proposal.resolved_at_slot = 0;
        proposal._reserved = [0u8; 32];
        Ok(())
    }

    /// Agent commits a prediction for a proposal. One prediction per
    /// (agent, proposal) — the PDA uniqueness guarantees this. Must be
    /// submitted before `voting_closes_at_slot`.
    pub fn submit_prediction(
        ctx: Context<SubmitPrediction>,
        _proposal_id: [u8; 32],
        predicted_outcome: u8,
    ) -> Result<()> {
        let now = Clock::get()?.slot;
        let proposal = &ctx.accounts.proposal;

        require!(
            now < proposal.voting_closes_at_slot,
            ReputationError::VotingAlreadyClosed
        );
        require!(
            predicted_outcome < proposal.num_choices,
            ReputationError::InvalidPredictedOutcome
        );

        let prediction = &mut ctx.accounts.prediction;
        prediction.agent = ctx.accounts.agent.key();
        prediction.proposal_id = proposal.proposal_id;
        prediction.predicted_outcome = predicted_outcome;
        prediction.submitted_at_slot = now;
        prediction.resolved = false;
        prediction.correctness_bps = 0;
        prediction.score_contribution = 0;
        prediction._reserved = [0u8; 32];

        let reputation = &mut ctx.accounts.reputation;
        reputation.total_predictions = reputation
            .total_predictions
            .checked_add(1)
            .ok_or(ReputationError::MathOverflow)?;

        Ok(())
    }

    /// Resolver writes the final outcome, full vote distribution, and
    /// difficulty weight onto the `Proposal` PDA. Difficulty is computed
    /// off-chain (see design doc §5). This is a one-shot per proposal —
    /// second calls are rejected.
    pub fn resolve_proposal(
        ctx: Context<ResolveProposal>,
        _proposal_id: [u8; 32],
        vote_distribution_bps: [u16; 8],
        final_outcome: u8,
        difficulty_bps: u16,
    ) -> Result<()> {
        let proposal = &mut ctx.accounts.proposal;
        require!(!proposal.resolved, ReputationError::AlreadyResolved);
        require!(
            final_outcome < proposal.num_choices,
            ReputationError::InvalidFinalOutcome
        );
        require!(
            difficulty_bps <= 10_000,
            ReputationError::InvalidDifficulty
        );
        let sum: u32 = vote_distribution_bps.iter().map(|v| *v as u32).sum();
        require!(sum == 10_000, ReputationError::InvalidVoteDistribution);

        proposal.resolved = true;
        proposal.final_outcome = final_outcome;
        proposal.vote_distribution_bps = vote_distribution_bps;
        proposal.difficulty_bps = difficulty_bps;
        proposal.resolved_at_slot = Clock::get()?.slot;

        Ok(())
    }

    /// Scores a single prediction against a resolved proposal and rolls the
    /// result into the agent's running numerator / denominator. Permissionless
    /// — anyone can crank. Idempotent per (proposal, agent): second call fails
    /// on `AlreadyFinalized`.
    ///
    /// Scoring math (fixed-point, no floats):
    ///   correctness_bps        = 10_000 if predicted == final else 0
    ///   score_contribution     = correctness_bps * difficulty_bps / 10_000    (per-prediction)
    ///   numerator += correctness_bps * difficulty_bps                         (u128, no divide)
    ///   denominator += difficulty_bps                                         (u128)
    ///   agent accuracy_bps     = numerator / denominator                      (read-side)
    ///
    /// Gaming-by-easy: if difficulty_bps == 0, both delta-numerator and
    /// delta-denominator are 0 — the prediction is score-neutral. See
    /// design doc §5 + §6.
    pub fn finalize_prediction(
        ctx: Context<FinalizePrediction>,
        _proposal_id: [u8; 32],
        _agent_pubkey: Pubkey,
    ) -> Result<()> {
        let proposal = &ctx.accounts.proposal;
        require!(proposal.resolved, ReputationError::ProposalNotResolved);

        let prediction = &mut ctx.accounts.prediction;
        require!(!prediction.resolved, ReputationError::AlreadyFinalized);

        let correctness_bps: u16 = if prediction.predicted_outcome == proposal.final_outcome {
            10_000
        } else {
            0
        };

        let score_contribution: u64 = (correctness_bps as u64)
            .checked_mul(proposal.difficulty_bps as u64)
            .and_then(|v| v.checked_div(10_000))
            .ok_or(ReputationError::MathOverflow)?;

        prediction.correctness_bps = correctness_bps;
        prediction.score_contribution = score_contribution;
        prediction.resolved = true;

        let reputation = &mut ctx.accounts.reputation;
        let product: u128 = (correctness_bps as u128)
            .checked_mul(proposal.difficulty_bps as u128)
            .ok_or(ReputationError::MathOverflow)?;
        reputation.weighted_correct_numerator = reputation
            .weighted_correct_numerator
            .checked_add(product)
            .ok_or(ReputationError::MathOverflow)?;
        reputation.weighted_difficulty_denominator = reputation
            .weighted_difficulty_denominator
            .checked_add(proposal.difficulty_bps as u128)
            .ok_or(ReputationError::MathOverflow)?;
        reputation.total_resolved = reputation
            .total_resolved
            .checked_add(1)
            .ok_or(ReputationError::MathOverflow)?;

        Ok(())
    }

    /// Rotates the resolver in `ProgramConfig`. Callable only by the current
    /// resolver. Path to multisig: set `new_resolver` to a Squads vault PDA
    /// or a multisig account — no program change needed.
    pub fn transfer_resolver(
        ctx: Context<TransferResolver>,
        new_resolver: Pubkey,
    ) -> Result<()> {
        let config = &mut ctx.accounts.config;
        config.resolver = new_resolver;
        Ok(())
    }
}

// ─── Accounts contexts ───────────────────────────────────────────────────────

#[derive(Accounts)]
pub struct InitializeConfig<'info> {
    #[account(mut)]
    pub payer: Signer<'info>,

    #[account(
        init,
        payer = payer,
        space = 8 + ProgramConfig::INIT_SPACE,
        seeds = [b"config"],
        bump,
    )]
    pub config: Account<'info, ProgramConfig>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct RegisterAgent<'info> {
    #[account(mut)]
    pub agent: Signer<'info>,

    #[account(
        init,
        payer = agent,
        space = 8 + AgentReputation::INIT_SPACE,
        seeds = [b"reputation", agent.key().as_ref()],
        bump,
    )]
    pub reputation: Account<'info, AgentReputation>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(proposal_id: [u8; 32])]
pub struct SubmitPrediction<'info> {
    #[account(mut)]
    pub agent: Signer<'info>,

    #[account(
        mut,
        seeds = [b"reputation", agent.key().as_ref()],
        bump,
    )]
    pub reputation: Account<'info, AgentReputation>,

    #[account(
        seeds = [b"proposal", proposal_id.as_ref()],
        bump,
    )]
    pub proposal: Account<'info, Proposal>,

    #[account(
        init,
        payer = agent,
        space = 8 + Prediction::INIT_SPACE,
        seeds = [b"prediction", proposal_id.as_ref(), agent.key().as_ref()],
        bump,
    )]
    pub prediction: Account<'info, Prediction>,

    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct TransferResolver<'info> {
    pub current_resolver: Signer<'info>,

    #[account(
        mut,
        seeds = [b"config"],
        bump,
        constraint = config.resolver == current_resolver.key() @ ReputationError::UnauthorizedResolver,
    )]
    pub config: Account<'info, ProgramConfig>,
}

#[derive(Accounts)]
#[instruction(proposal_id: [u8; 32])]
pub struct ResolveProposal<'info> {
    pub resolver: Signer<'info>,

    #[account(
        seeds = [b"config"],
        bump,
        has_one = resolver @ ReputationError::UnauthorizedResolver,
    )]
    pub config: Account<'info, ProgramConfig>,

    #[account(
        mut,
        seeds = [b"proposal", proposal_id.as_ref()],
        bump,
    )]
    pub proposal: Account<'info, Proposal>,
}

#[derive(Accounts)]
#[instruction(proposal_id: [u8; 32], agent_pubkey: Pubkey)]
pub struct FinalizePrediction<'info> {
    /// Permissionless cranker. Just pays the tx fee; no access control.
    #[account(mut)]
    pub cranker: Signer<'info>,

    #[account(
        mut,
        seeds = [b"reputation", agent_pubkey.as_ref()],
        bump,
    )]
    pub reputation: Account<'info, AgentReputation>,

    #[account(
        seeds = [b"proposal", proposal_id.as_ref()],
        bump,
    )]
    pub proposal: Account<'info, Proposal>,

    #[account(
        mut,
        seeds = [b"prediction", proposal_id.as_ref(), agent_pubkey.as_ref()],
        bump,
    )]
    pub prediction: Account<'info, Prediction>,
}

#[derive(Accounts)]
#[instruction(proposal_id: [u8; 32])]
pub struct CreateProposal<'info> {
    #[account(mut)]
    pub resolver: Signer<'info>,

    #[account(
        seeds = [b"config"],
        bump,
        has_one = resolver @ ReputationError::UnauthorizedResolver,
    )]
    pub config: Account<'info, ProgramConfig>,

    #[account(
        init,
        payer = resolver,
        space = 8 + Proposal::INIT_SPACE,
        seeds = [b"proposal", proposal_id.as_ref()],
        bump,
    )]
    pub proposal: Account<'info, Proposal>,

    pub system_program: Program<'info, System>,
}

// ─── Account structs ─────────────────────────────────────────────────────────

#[account]
#[derive(InitSpace)]
pub struct ProgramConfig {
    pub resolver: Pubkey,
    pub _reserved: [u8; 64],
}

#[account]
#[derive(InitSpace)]
pub struct AgentReputation {
    pub agent_pubkey: Pubkey,
    pub total_predictions: u64,
    pub total_resolved: u64,
    pub weighted_correct_numerator: u128,
    pub weighted_difficulty_denominator: u128,
    pub eligible_proposals_seen: u64,
    pub _reserved: [u8; 64],
}

#[account]
#[derive(InitSpace)]
pub struct Proposal {
    pub proposal_id: [u8; 32],
    pub dao_id: [u8; 32],
    pub voting_closes_at_slot: u64,
    pub num_choices: u8,
    pub resolved: bool,
    pub final_outcome: u8,
    pub vote_distribution_bps: [u16; 8],
    pub difficulty_bps: u16,
    pub resolver: Pubkey,
    pub resolved_at_slot: u64,
    pub _reserved: [u8; 32],
}

#[account]
#[derive(InitSpace)]
pub struct Prediction {
    pub agent: Pubkey,
    pub proposal_id: [u8; 32],
    pub predicted_outcome: u8,
    pub submitted_at_slot: u64,
    pub resolved: bool,
    pub correctness_bps: u16,
    pub score_contribution: u64,
    pub _reserved: [u8; 32],
}

// ─── Errors ──────────────────────────────────────────────────────────────────

#[error_code]
pub enum ReputationError {
    #[msg("num_choices must be in the range [2, 8]")]
    InvalidNumChoices,
    #[msg("voting_closes_at_slot must be in the future")]
    VotingAlreadyClosed,
    #[msg("signer is not the configured resolver")]
    UnauthorizedResolver,
    #[msg("predicted_outcome must be less than num_choices")]
    InvalidPredictedOutcome,
    #[msg("arithmetic overflow")]
    MathOverflow,
    #[msg("proposal is already resolved")]
    AlreadyResolved,
    #[msg("final_outcome must be less than num_choices")]
    InvalidFinalOutcome,
    #[msg("difficulty_bps must be <= 10_000")]
    InvalidDifficulty,
    #[msg("vote_distribution_bps entries must sum to 10_000")]
    InvalidVoteDistribution,
    #[msg("proposal has not been resolved yet")]
    ProposalNotResolved,
    #[msg("prediction has already been finalized")]
    AlreadyFinalized,
}
