import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { Reputation } from "../target/types/reputation";
import { expect } from "chai";

describe("reputation", () => {
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);
  const program = anchor.workspace.Reputation as Program<Reputation>;

  const [configPda] = anchor.web3.PublicKey.findProgramAddressSync(
    [Buffer.from("config")],
    program.programId
  );

  const resolverKey = anchor.web3.Keypair.generate();

  async function airdrop(pubkey: anchor.web3.PublicKey, lamports = 2_000_000_000) {
    const sig = await provider.connection.requestAirdrop(pubkey, lamports);
    await provider.connection.confirmTransaction(sig, "confirmed");
  }

  function proposalPda(id: Uint8Array) {
    return anchor.web3.PublicKey.findProgramAddressSync(
      [Buffer.from("proposal"), Buffer.from(id)],
      program.programId
    )[0];
  }

  function fixedId(seed: number): Uint8Array {
    const arr = new Uint8Array(32);
    arr[0] = seed;
    return arr;
  }

  before("initialize program config (once)", async () => {
    await airdrop(resolverKey.publicKey);
    try {
      await program.methods
        .initializeConfig(resolverKey.publicKey)
        .accounts({
          payer: provider.wallet.publicKey,
          config: configPda,
        })
        .rpc();
    } catch (e) {
      // Tolerate re-runs on the same localnet ledger.
      if (!String(e).includes("already in use")) throw e;
    }
  });

  describe("initialize_config + register_agent", () => {
    it("writes the resolver into ProgramConfig", async () => {
      const config = await program.account.programConfig.fetch(configPda);
      expect(config.resolver.toBase58()).to.equal(resolverKey.publicKey.toBase58());
    });

    it("registers an agent with zeroed counters", async () => {
      const agent = anchor.web3.Keypair.generate();
      await airdrop(agent.publicKey);

      const [reputationPda] = anchor.web3.PublicKey.findProgramAddressSync(
        [Buffer.from("reputation"), agent.publicKey.toBuffer()],
        program.programId
      );

      await program.methods
        .registerAgent()
        .accounts({
          agent: agent.publicKey,
          reputation: reputationPda,
        })
        .signers([agent])
        .rpc();

      const rep = await program.account.agentReputation.fetch(reputationPda);
      expect(rep.agentPubkey.toBase58()).to.equal(agent.publicKey.toBase58());
      expect(rep.totalPredictions.toNumber()).to.equal(0);
      expect(rep.totalResolved.toNumber()).to.equal(0);
      expect(rep.eligibleProposalsSeen.toNumber()).to.equal(0);
      expect(rep.weightedCorrectNumerator.toString()).to.equal("0");
      expect(rep.weightedDifficultyDenominator.toString()).to.equal("0");
    });

    it("rejects a second register_agent for the same agent", async () => {
      const agent = anchor.web3.Keypair.generate();
      await airdrop(agent.publicKey);

      const [reputationPda] = anchor.web3.PublicKey.findProgramAddressSync(
        [Buffer.from("reputation"), agent.publicKey.toBuffer()],
        program.programId
      );

      await program.methods
        .registerAgent()
        .accounts({ agent: agent.publicKey, reputation: reputationPda })
        .signers([agent])
        .rpc();

      let threw = false;
      try {
        await program.methods
          .registerAgent()
          .accounts({ agent: agent.publicKey, reputation: reputationPda })
          .signers([agent])
          .rpc();
      } catch {
        threw = true;
      }
      expect(threw, "second register_agent must fail").to.equal(true);
    });
  });

  describe("create_proposal", () => {
    const daoId = fixedId(42);

    it("creates a proposal with valid inputs (yes/no vote)", async () => {
      const id = fixedId(1);
      const currentSlot = await provider.connection.getSlot();
      const closesAt = new anchor.BN(currentSlot + 10_000);

      await program.methods
        .createProposal(Array.from(id), Array.from(daoId), closesAt, 2)
        .accounts({
          resolver: resolverKey.publicKey,
          proposal: proposalPda(id),
        })
        .signers([resolverKey])
        .rpc();

      const p = await program.account.proposal.fetch(proposalPda(id));
      expect(p.resolved).to.equal(false);
      expect(p.numChoices).to.equal(2);
      expect(p.votingClosesAtSlot.toString()).to.equal(closesAt.toString());
      expect(p.difficultyBps).to.equal(0);
      expect(p.resolver.toBase58()).to.equal(resolverKey.publicKey.toBase58());
    });

    it("rejects num_choices = 1 (InvalidNumChoices)", async () => {
      const id = fixedId(2);
      const closesAt = new anchor.BN((await provider.connection.getSlot()) + 10_000);

      let err = "";
      try {
        await program.methods
          .createProposal(Array.from(id), Array.from(daoId), closesAt, 1)
          .accounts({ resolver: resolverKey.publicKey, proposal: proposalPda(id) })
          .signers([resolverKey])
          .rpc();
      } catch (e) {
        err = String(e);
      }
      expect(err).to.include("InvalidNumChoices");
    });

    it("rejects num_choices = 9 (InvalidNumChoices)", async () => {
      const id = fixedId(3);
      const closesAt = new anchor.BN((await provider.connection.getSlot()) + 10_000);

      let err = "";
      try {
        await program.methods
          .createProposal(Array.from(id), Array.from(daoId), closesAt, 9)
          .accounts({ resolver: resolverKey.publicKey, proposal: proposalPda(id) })
          .signers([resolverKey])
          .rpc();
      } catch (e) {
        err = String(e);
      }
      expect(err).to.include("InvalidNumChoices");
    });

    it("rejects a voting_closes_at_slot in the past (VotingAlreadyClosed)", async () => {
      const id = fixedId(4);
      // Always-in-the-past: slot 1 is long gone by the time we run.
      const closesAt = new anchor.BN(1);

      let err = "";
      try {
        await program.methods
          .createProposal(Array.from(id), Array.from(daoId), closesAt, 2)
          .accounts({ resolver: resolverKey.publicKey, proposal: proposalPda(id) })
          .signers([resolverKey])
          .rpc();
      } catch (e) {
        err = String(e);
      }
      expect(err).to.include("VotingAlreadyClosed");
    });

    it("rejects create_proposal from a non-resolver signer (UnauthorizedResolver)", async () => {
      const imposter = anchor.web3.Keypair.generate();
      await airdrop(imposter.publicKey);

      const id = fixedId(5);
      const closesAt = new anchor.BN((await provider.connection.getSlot()) + 10_000);

      let err = "";
      try {
        await program.methods
          .createProposal(Array.from(id), Array.from(daoId), closesAt, 2)
          .accounts({ resolver: imposter.publicKey, proposal: proposalPda(id) })
          .signers([imposter])
          .rpc();
      } catch (e) {
        err = String(e);
      }
      expect(err).to.include("UnauthorizedResolver");
    });
  });

  describe("submit_prediction", () => {
    const daoId = fixedId(42);

    function reputationPdaFor(agentPk: anchor.web3.PublicKey) {
      return anchor.web3.PublicKey.findProgramAddressSync(
        [Buffer.from("reputation"), agentPk.toBuffer()],
        program.programId
      )[0];
    }

    function predictionPda(proposalId: Uint8Array, agentPk: anchor.web3.PublicKey) {
      return anchor.web3.PublicKey.findProgramAddressSync(
        [Buffer.from("prediction"), Buffer.from(proposalId), agentPk.toBuffer()],
        program.programId
      )[0];
    }

    async function registerAndFund(): Promise<anchor.web3.Keypair> {
      const agent = anchor.web3.Keypair.generate();
      await airdrop(agent.publicKey);
      await program.methods
        .registerAgent()
        .accounts({ agent: agent.publicKey, reputation: reputationPdaFor(agent.publicKey) })
        .signers([agent])
        .rpc();
      return agent;
    }

    async function createProposalFresh(id: Uint8Array, numChoices = 2) {
      const closesAt = new anchor.BN((await provider.connection.getSlot()) + 10_000);
      await program.methods
        .createProposal(Array.from(id), Array.from(daoId), closesAt, numChoices)
        .accounts({ resolver: resolverKey.publicKey, proposal: proposalPda(id) })
        .signers([resolverKey])
        .rpc();
    }

    it("records a prediction and increments total_predictions", async () => {
      const agent = await registerAndFund();
      const id = fixedId(10);
      await createProposalFresh(id);

      await program.methods
        .submitPrediction(Array.from(id), 1)
        .accounts({
          agent: agent.publicKey,
          reputation: reputationPdaFor(agent.publicKey),
          proposal: proposalPda(id),
          prediction: predictionPda(id, agent.publicKey),
        })
        .signers([agent])
        .rpc();

      const pred = await program.account.prediction.fetch(predictionPda(id, agent.publicKey));
      expect(pred.agent.toBase58()).to.equal(agent.publicKey.toBase58());
      expect(pred.predictedOutcome).to.equal(1);
      expect(pred.resolved).to.equal(false);
      expect(pred.correctnessBps).to.equal(0);

      const rep = await program.account.agentReputation.fetch(reputationPdaFor(agent.publicKey));
      expect(rep.totalPredictions.toNumber()).to.equal(1);
    });

    it("rejects predicted_outcome >= num_choices", async () => {
      const agent = await registerAndFund();
      const id = fixedId(11);
      await createProposalFresh(id, 2); // binary vote → outcomes 0 or 1 only

      let err = "";
      try {
        await program.methods
          .submitPrediction(Array.from(id), 2)
          .accounts({
            agent: agent.publicKey,
            reputation: reputationPdaFor(agent.publicKey),
            proposal: proposalPda(id),
            prediction: predictionPda(id, agent.publicKey),
          })
          .signers([agent])
          .rpc();
      } catch (e) {
        err = String(e);
      }
      expect(err).to.include("InvalidPredictedOutcome");
    });

    it("rejects a second prediction from the same agent on the same proposal", async () => {
      const agent = await registerAndFund();
      const id = fixedId(12);
      await createProposalFresh(id);

      await program.methods
        .submitPrediction(Array.from(id), 0)
        .accounts({
          agent: agent.publicKey,
          reputation: reputationPdaFor(agent.publicKey),
          proposal: proposalPda(id),
          prediction: predictionPda(id, agent.publicKey),
        })
        .signers([agent])
        .rpc();

      let threw = false;
      try {
        await program.methods
          .submitPrediction(Array.from(id), 1)
          .accounts({
            agent: agent.publicKey,
            reputation: reputationPdaFor(agent.publicKey),
            proposal: proposalPda(id),
            prediction: predictionPda(id, agent.publicKey),
          })
          .signers([agent])
          .rpc();
      } catch {
        threw = true;
      }
      expect(threw, "duplicate prediction must fail").to.equal(true);
    });

    it("allows two different agents to predict on the same proposal", async () => {
      const alice = await registerAndFund();
      const bob = await registerAndFund();
      const id = fixedId(13);
      await createProposalFresh(id);

      await program.methods
        .submitPrediction(Array.from(id), 0)
        .accounts({
          agent: alice.publicKey,
          reputation: reputationPdaFor(alice.publicKey),
          proposal: proposalPda(id),
          prediction: predictionPda(id, alice.publicKey),
        })
        .signers([alice])
        .rpc();

      await program.methods
        .submitPrediction(Array.from(id), 1)
        .accounts({
          agent: bob.publicKey,
          reputation: reputationPdaFor(bob.publicKey),
          proposal: proposalPda(id),
          prediction: predictionPda(id, bob.publicKey),
        })
        .signers([bob])
        .rpc();

      const pAlice = await program.account.prediction.fetch(predictionPda(id, alice.publicKey));
      const pBob = await program.account.prediction.fetch(predictionPda(id, bob.publicKey));
      expect(pAlice.predictedOutcome).to.equal(0);
      expect(pBob.predictedOutcome).to.equal(1);
    });
  });

  describe("resolve_proposal", () => {
    const daoId = fixedId(42);

    // Distribution helper: returns [u16; 8] with supplied values in front,
    // zero-padded to length 8. Sum must equal 10_000 for a valid call.
    function dist(...values: number[]): number[] {
      const arr = new Array(8).fill(0);
      for (let i = 0; i < values.length; i++) arr[i] = values[i];
      return arr;
    }

    async function freshProposal(id: Uint8Array, numChoices = 2) {
      const closesAt = new anchor.BN((await provider.connection.getSlot()) + 10_000);
      await program.methods
        .createProposal(Array.from(id), Array.from(daoId), closesAt, numChoices)
        .accounts({ resolver: resolverKey.publicKey, proposal: proposalPda(id) })
        .signers([resolverKey])
        .rpc();
    }

    it("writes outcome, distribution, and difficulty on a valid call", async () => {
      const id = fixedId(20);
      await freshProposal(id);

      await program.methods
        .resolveProposal(Array.from(id), dist(6000, 4000), 0, 5500)
        .accounts({ resolver: resolverKey.publicKey, proposal: proposalPda(id) })
        .signers([resolverKey])
        .rpc();

      const p = await program.account.proposal.fetch(proposalPda(id));
      expect(p.resolved).to.equal(true);
      expect(p.finalOutcome).to.equal(0);
      expect(p.voteDistributionBps[0]).to.equal(6000);
      expect(p.voteDistributionBps[1]).to.equal(4000);
      expect(p.difficultyBps).to.equal(5500);
      expect(p.resolvedAtSlot.toNumber()).to.be.greaterThan(0);
    });

    it("rejects a second resolve on the same proposal (AlreadyResolved)", async () => {
      const id = fixedId(21);
      await freshProposal(id);
      await program.methods
        .resolveProposal(Array.from(id), dist(9000, 1000), 0, 2000)
        .accounts({ resolver: resolverKey.publicKey, proposal: proposalPda(id) })
        .signers([resolverKey])
        .rpc();

      let err = "";
      try {
        await program.methods
          .resolveProposal(Array.from(id), dist(9000, 1000), 0, 2000)
          .accounts({ resolver: resolverKey.publicKey, proposal: proposalPda(id) })
          .signers([resolverKey])
          .rpc();
      } catch (e) {
        err = String(e);
      }
      expect(err).to.include("AlreadyResolved");
    });

    it("rejects a distribution that does not sum to 10_000", async () => {
      const id = fixedId(22);
      await freshProposal(id);

      let err = "";
      try {
        await program.methods
          .resolveProposal(Array.from(id), dist(5000, 4000), 0, 5000)
          .accounts({ resolver: resolverKey.publicKey, proposal: proposalPda(id) })
          .signers([resolverKey])
          .rpc();
      } catch (e) {
        err = String(e);
      }
      expect(err).to.include("InvalidVoteDistribution");
    });

    it("rejects final_outcome >= num_choices", async () => {
      const id = fixedId(23);
      await freshProposal(id, 2);

      let err = "";
      try {
        await program.methods
          .resolveProposal(Array.from(id), dist(5000, 5000), 2, 10_000)
          .accounts({ resolver: resolverKey.publicKey, proposal: proposalPda(id) })
          .signers([resolverKey])
          .rpc();
      } catch (e) {
        err = String(e);
      }
      expect(err).to.include("InvalidFinalOutcome");
    });

    it("rejects difficulty_bps > 10_000", async () => {
      const id = fixedId(24);
      await freshProposal(id);

      let err = "";
      try {
        await program.methods
          .resolveProposal(Array.from(id), dist(5000, 5000), 0, 20_000)
          .accounts({ resolver: resolverKey.publicKey, proposal: proposalPda(id) })
          .signers([resolverKey])
          .rpc();
      } catch (e) {
        err = String(e);
      }
      expect(err).to.include("InvalidDifficulty");
    });

    it("rejects non-resolver signer (UnauthorizedResolver)", async () => {
      const imposter = anchor.web3.Keypair.generate();
      await airdrop(imposter.publicKey);
      const id = fixedId(25);
      await freshProposal(id);

      let err = "";
      try {
        await program.methods
          .resolveProposal(Array.from(id), dist(5000, 5000), 0, 10_000)
          .accounts({ resolver: imposter.publicKey, proposal: proposalPda(id) })
          .signers([imposter])
          .rpc();
      } catch (e) {
        err = String(e);
      }
      expect(err).to.include("UnauthorizedResolver");
    });
  });

  describe("finalize_prediction + scoring math", () => {
    const daoId = fixedId(42);

    function dist(...values: number[]): number[] {
      const arr = new Array(8).fill(0);
      for (let i = 0; i < values.length; i++) arr[i] = values[i];
      return arr;
    }

    async function registerAndFund(): Promise<anchor.web3.Keypair> {
      const agent = anchor.web3.Keypair.generate();
      await airdrop(agent.publicKey);
      await program.methods
        .registerAgent()
        .accounts({ agent: agent.publicKey, reputation: reputationPdaFor(agent.publicKey) })
        .signers([agent])
        .rpc();
      return agent;
    }

    function reputationPdaFor(agentPk: anchor.web3.PublicKey) {
      return anchor.web3.PublicKey.findProgramAddressSync(
        [Buffer.from("reputation"), agentPk.toBuffer()],
        program.programId
      )[0];
    }

    function predictionPda(proposalId: Uint8Array, agentPk: anchor.web3.PublicKey) {
      return anchor.web3.PublicKey.findProgramAddressSync(
        [Buffer.from("prediction"), Buffer.from(proposalId), agentPk.toBuffer()],
        program.programId
      )[0];
    }

    async function setupPredicted({
      id,
      outcome,
      numChoices = 2,
    }: {
      id: Uint8Array;
      outcome: number;
      numChoices?: number;
    }): Promise<anchor.web3.Keypair> {
      const agent = await registerAndFund();
      const closesAt = new anchor.BN((await provider.connection.getSlot()) + 10_000);
      await program.methods
        .createProposal(Array.from(id), Array.from(daoId), closesAt, numChoices)
        .accounts({ resolver: resolverKey.publicKey, proposal: proposalPda(id) })
        .signers([resolverKey])
        .rpc();
      await program.methods
        .submitPrediction(Array.from(id), outcome)
        .accounts({
          agent: agent.publicKey,
          reputation: reputationPdaFor(agent.publicKey),
          proposal: proposalPda(id),
          prediction: predictionPda(id, agent.publicKey),
        })
        .signers([agent])
        .rpc();
      return agent;
    }

    it("scores a correct prediction on a 50/50 proposal (difficulty=10000)", async () => {
      const id = fixedId(30);
      const agent = await setupPredicted({ id, outcome: 1 });
      await program.methods
        .resolveProposal(Array.from(id), dist(5000, 5000), 1, 10_000)
        .accounts({ resolver: resolverKey.publicKey, proposal: proposalPda(id) })
        .signers([resolverKey])
        .rpc();

      await program.methods
        .finalizePrediction(Array.from(id), agent.publicKey)
        .accounts({
          cranker: provider.wallet.publicKey,
          reputation: reputationPdaFor(agent.publicKey),
          proposal: proposalPda(id),
          prediction: predictionPda(id, agent.publicKey),
        })
        .rpc();

      const pred = await program.account.prediction.fetch(predictionPda(id, agent.publicKey));
      expect(pred.resolved).to.equal(true);
      expect(pred.correctnessBps).to.equal(10_000);
      // score_contribution = 10000 * 10000 / 10000 = 10000
      expect(pred.scoreContribution.toNumber()).to.equal(10_000);

      const rep = await program.account.agentReputation.fetch(reputationPdaFor(agent.publicKey));
      // numerator = 10000 * 10000 = 100_000_000
      expect(rep.weightedCorrectNumerator.toString()).to.equal("100000000");
      expect(rep.weightedDifficultyDenominator.toString()).to.equal("10000");
      expect(rep.totalResolved.toNumber()).to.equal(1);
    });

    it("scores a wrong prediction as zero on a contested proposal", async () => {
      const id = fixedId(31);
      const agent = await setupPredicted({ id, outcome: 1 }); // agent predicts 1
      // Real outcome = 0, 60/40 split → difficulty ~9710 bps (entropy of 0.6/0.4)
      await program.methods
        .resolveProposal(Array.from(id), dist(6000, 4000), 0, 9710)
        .accounts({ resolver: resolverKey.publicKey, proposal: proposalPda(id) })
        .signers([resolverKey])
        .rpc();

      await program.methods
        .finalizePrediction(Array.from(id), agent.publicKey)
        .accounts({
          cranker: provider.wallet.publicKey,
          reputation: reputationPdaFor(agent.publicKey),
          proposal: proposalPda(id),
          prediction: predictionPda(id, agent.publicKey),
        })
        .rpc();

      const pred = await program.account.prediction.fetch(predictionPda(id, agent.publicKey));
      expect(pred.correctnessBps).to.equal(0);
      expect(pred.scoreContribution.toNumber()).to.equal(0);

      const rep = await program.account.agentReputation.fetch(reputationPdaFor(agent.publicKey));
      // numerator += 0, denominator += 9710
      expect(rep.weightedCorrectNumerator.toString()).to.equal("0");
      expect(rep.weightedDifficultyDenominator.toString()).to.equal("9710");
      expect(rep.totalResolved.toNumber()).to.equal(1);
    });

    it("rejects finalize before the proposal is resolved (ProposalNotResolved)", async () => {
      const id = fixedId(32);
      const agent = await setupPredicted({ id, outcome: 0 });

      let err = "";
      try {
        await program.methods
          .finalizePrediction(Array.from(id), agent.publicKey)
          .accounts({
            cranker: provider.wallet.publicKey,
            reputation: reputationPdaFor(agent.publicKey),
            proposal: proposalPda(id),
            prediction: predictionPda(id, agent.publicKey),
          })
          .rpc();
      } catch (e) {
        err = String(e);
      }
      expect(err).to.include("ProposalNotResolved");
    });

    it("rejects a second finalize on the same prediction (AlreadyFinalized)", async () => {
      const id = fixedId(33);
      const agent = await setupPredicted({ id, outcome: 0 });
      await program.methods
        .resolveProposal(Array.from(id), dist(5000, 5000), 0, 10_000)
        .accounts({ resolver: resolverKey.publicKey, proposal: proposalPda(id) })
        .signers([resolverKey])
        .rpc();

      await program.methods
        .finalizePrediction(Array.from(id), agent.publicKey)
        .accounts({
          cranker: provider.wallet.publicKey,
          reputation: reputationPdaFor(agent.publicKey),
          proposal: proposalPda(id),
          prediction: predictionPda(id, agent.publicKey),
        })
        .rpc();

      let err = "";
      try {
        await program.methods
          .finalizePrediction(Array.from(id), agent.publicKey)
          .accounts({
            cranker: provider.wallet.publicKey,
            reputation: reputationPdaFor(agent.publicKey),
            proposal: proposalPda(id),
            prediction: predictionPda(id, agent.publicKey),
          })
          .rpc();
      } catch (e) {
        err = String(e);
      }
      expect(err).to.include("AlreadyFinalized");
    });

    it("aggregates correctly across multiple predictions (end-to-end math)", async () => {
      // Scenario: agent predicts 3 proposals. All predictions correct.
      // Difficulties: 10000, 5000, 2000. Total denominator = 17000.
      // Numerator = 10000*10000 + 10000*5000 + 10000*2000 = 170_000_000.
      // Expected accuracy_bps = 170_000_000 / 17000 = 10_000 (perfect, since all correct).
      const agent = await registerAndFund();
      const ids = [fixedId(40), fixedId(41), fixedId(42)];
      const difficulties = [10_000, 5_000, 2_000];
      const outcomes = [0, 1, 0];

      for (let i = 0; i < ids.length; i++) {
        const closesAt = new anchor.BN((await provider.connection.getSlot()) + 10_000);
        await program.methods
          .createProposal(Array.from(ids[i]), Array.from(daoId), closesAt, 2)
          .accounts({ resolver: resolverKey.publicKey, proposal: proposalPda(ids[i]) })
          .signers([resolverKey])
          .rpc();
        await program.methods
          .submitPrediction(Array.from(ids[i]), outcomes[i])
          .accounts({
            agent: agent.publicKey,
            reputation: reputationPdaFor(agent.publicKey),
            proposal: proposalPda(ids[i]),
            prediction: predictionPda(ids[i], agent.publicKey),
          })
          .signers([agent])
          .rpc();
        await program.methods
          .resolveProposal(Array.from(ids[i]), dist(5000, 5000), outcomes[i], difficulties[i])
          .accounts({ resolver: resolverKey.publicKey, proposal: proposalPda(ids[i]) })
          .signers([resolverKey])
          .rpc();
        await program.methods
          .finalizePrediction(Array.from(ids[i]), agent.publicKey)
          .accounts({
            cranker: provider.wallet.publicKey,
            reputation: reputationPdaFor(agent.publicKey),
            proposal: proposalPda(ids[i]),
            prediction: predictionPda(ids[i], agent.publicKey),
          })
          .rpc();
      }

      const rep = await program.account.agentReputation.fetch(reputationPdaFor(agent.publicKey));
      expect(rep.totalPredictions.toNumber()).to.equal(3);
      expect(rep.totalResolved.toNumber()).to.equal(3);
      expect(rep.weightedCorrectNumerator.toString()).to.equal("170000000");
      expect(rep.weightedDifficultyDenominator.toString()).to.equal("17000");

      // Accuracy derived off-chain: numerator / denominator
      const numerator = BigInt(rep.weightedCorrectNumerator.toString());
      const denominator = BigInt(rep.weightedDifficultyDenominator.toString());
      const accuracyBps = Number(numerator / denominator);
      expect(accuracyBps).to.equal(10_000);
    });
  });

  // ─── red-team scenarios (Risk B proof) ─────────────────────────────────
  // Numeric proof that the scoring metric cannot be gamed. Each scenario
  // builds a fresh agent, runs a specific prediction pattern, then asserts
  // the resulting (weighted_correct_numerator, weighted_difficulty_denominator)
  // on-chain. Off-chain, accuracy_bps = numerator / denominator (undefined
  // when denominator == 0).
  describe("red-team scenarios", () => {
    const DAO_ID = new Uint8Array(32).fill(7);

    function dist(...values: number[]): number[] {
      const arr = new Array(8).fill(0);
      for (let i = 0; i < values.length; i++) arr[i] = values[i];
      return arr;
    }

    function reputationPdaFor(agentPk: anchor.web3.PublicKey) {
      return anchor.web3.PublicKey.findProgramAddressSync(
        [Buffer.from("reputation"), agentPk.toBuffer()],
        program.programId
      )[0];
    }

    function predictionPda(proposalId: Uint8Array, agentPk: anchor.web3.PublicKey) {
      return anchor.web3.PublicKey.findProgramAddressSync(
        [Buffer.from("prediction"), Buffer.from(proposalId), agentPk.toBuffer()],
        program.programId
      )[0];
    }

    let seq = 100;
    function nextId(): Uint8Array {
      seq += 1;
      const arr = new Uint8Array(32);
      arr[0] = seq & 0xff;
      arr[1] = (seq >> 8) & 0xff;
      arr[2] = 0xee; // tag red-team so ids don't collide with main-suite proposals
      return arr;
    }

    async function newAgent(): Promise<anchor.web3.Keypair> {
      const agent = anchor.web3.Keypair.generate();
      await airdrop(agent.publicKey, 3_000_000_000);
      await program.methods
        .registerAgent()
        .accounts({
          agent: agent.publicKey,
          reputation: reputationPdaFor(agent.publicKey),
        })
        .signers([agent])
        .rpc();
      return agent;
    }

    async function runPrediction(
      agent: anchor.web3.Keypair,
      opts: {
        predicted: number;
        finalOutcome: number;
        difficulty: number;
        distribution: number[];
      }
    ) {
      const id = nextId();
      const closesAt = new anchor.BN((await provider.connection.getSlot()) + 10_000);

      await program.methods
        .createProposal(Array.from(id), Array.from(DAO_ID), closesAt, 2)
        .accounts({ resolver: resolverKey.publicKey, proposal: proposalPda(id) })
        .signers([resolverKey])
        .rpc();

      await program.methods
        .submitPrediction(Array.from(id), opts.predicted)
        .accounts({
          agent: agent.publicKey,
          reputation: reputationPdaFor(agent.publicKey),
          proposal: proposalPda(id),
          prediction: predictionPda(id, agent.publicKey),
        })
        .signers([agent])
        .rpc();

      await program.methods
        .resolveProposal(
          Array.from(id),
          opts.distribution,
          opts.finalOutcome,
          opts.difficulty
        )
        .accounts({ resolver: resolverKey.publicKey, proposal: proposalPda(id) })
        .signers([resolverKey])
        .rpc();

      await program.methods
        .finalizePrediction(Array.from(id), agent.publicKey)
        .accounts({
          cranker: provider.wallet.publicKey,
          reputation: reputationPdaFor(agent.publicKey),
          proposal: proposalPda(id),
          prediction: predictionPda(id, agent.publicKey),
        })
        .rpc();
    }

    async function getNumDen(agent: anchor.web3.Keypair) {
      const rep = await program.account.agentReputation.fetch(
        reputationPdaFor(agent.publicKey)
      );
      return {
        num: BigInt(rep.weightedCorrectNumerator.toString()),
        den: BigInt(rep.weightedDifficultyDenominator.toString()),
      };
    }

    it("Scenario 1: perfect predictor — 3/3 correct on mixed difficulties → 10000", async () => {
      const agent = await newAgent();
      await runPrediction(agent, { predicted: 0, finalOutcome: 0, difficulty: 10000, distribution: dist(5000, 5000) });
      await runPrediction(agent, { predicted: 1, finalOutcome: 1, difficulty: 5000,  distribution: dist(2000, 8000) });
      await runPrediction(agent, { predicted: 0, finalOutcome: 0, difficulty: 2000,  distribution: dist(9500, 500) });

      const { num, den } = await getNumDen(agent);
      // numerator = 10000*10000 + 10000*5000 + 10000*2000 = 170_000_000
      // denominator = 17000
      expect(num.toString()).to.equal("170000000");
      expect(den.toString()).to.equal("17000");
      expect(Number(num / den)).to.equal(10_000);
    });

    it("Scenario 2: always wrong — 0/3 correct → accuracy = 0", async () => {
      const agent = await newAgent();
      await runPrediction(agent, { predicted: 1, finalOutcome: 0, difficulty: 10000, distribution: dist(5000, 5000) });
      await runPrediction(agent, { predicted: 0, finalOutcome: 1, difficulty: 5000,  distribution: dist(3000, 7000) });
      await runPrediction(agent, { predicted: 1, finalOutcome: 0, difficulty: 2000,  distribution: dist(9000, 1000) });

      const { num, den } = await getNumDen(agent);
      expect(num.toString()).to.equal("0");
      expect(den.toString()).to.equal("17000");
      expect(Number(num / den)).to.equal(0);
    });

    it("Scenario 3: unanimous-only (difficulty=0) all correct → 0/0 undefined", async () => {
      const agent = await newAgent();
      await runPrediction(agent, { predicted: 0, finalOutcome: 0, difficulty: 0, distribution: dist(10000, 0) });
      await runPrediction(agent, { predicted: 1, finalOutcome: 1, difficulty: 0, distribution: dist(0, 10000) });
      await runPrediction(agent, { predicted: 0, finalOutcome: 0, difficulty: 0, distribution: dist(10000, 0) });

      const { num, den } = await getNumDen(agent);
      // Core gaming-resistance proof: predicting only easy proposals yields
      // zero mass. Off-chain reader sees 0/0 and shows "insufficient data".
      expect(num.toString()).to.equal("0");
      expect(den.toString()).to.equal("0");
    });

    it("Scenario 4: two unanimous + one contested, all correct → weighted only by contested", async () => {
      const agent = await newAgent();
      await runPrediction(agent, { predicted: 0, finalOutcome: 0, difficulty: 0,     distribution: dist(10000, 0) });
      await runPrediction(agent, { predicted: 1, finalOutcome: 1, difficulty: 0,     distribution: dist(0, 10000) });
      await runPrediction(agent, { predicted: 0, finalOutcome: 0, difficulty: 10000, distribution: dist(5000, 5000) });

      const { num, den } = await getNumDen(agent);
      expect(num.toString()).to.equal("100000000");
      expect(den.toString()).to.equal("10000");
      expect(Number(num / den)).to.equal(10_000);
      // Coverage would flag this — agent barely participates on hard votes.
    });

    it("Scenario 5: contested-right + unanimous-wrong → ~10000 (positive weighting)", async () => {
      const agent = await newAgent();
      await runPrediction(agent, { predicted: 0, finalOutcome: 0, difficulty: 10000, distribution: dist(5000, 5000) });
      await runPrediction(agent, { predicted: 1, finalOutcome: 0, difficulty: 0,     distribution: dist(10000, 0) });
      await runPrediction(agent, { predicted: 1, finalOutcome: 0, difficulty: 0,     distribution: dist(10000, 0) });

      const { num, den } = await getNumDen(agent);
      expect(num.toString()).to.equal("100000000");
      expect(den.toString()).to.equal("10000");
      expect(Number(num / den)).to.equal(10_000);
    });

    it("Scenario 6: contested-wrong + unanimous-right → ~0 (gaming fails)", async () => {
      const agent = await newAgent();
      await runPrediction(agent, { predicted: 1, finalOutcome: 0, difficulty: 10000, distribution: dist(5000, 5000) });
      await runPrediction(agent, { predicted: 0, finalOutcome: 0, difficulty: 0,     distribution: dist(10000, 0) });
      await runPrediction(agent, { predicted: 0, finalOutcome: 0, difficulty: 0,     distribution: dist(10000, 0) });

      const { num, den } = await getNumDen(agent);
      expect(num.toString()).to.equal("0");
      expect(den.toString()).to.equal("10000");
      expect(Number(num / den)).to.equal(0);
    });
  });

  // ─── transfer_resolver ──────────────────────────────────────────────────
  // Mutates the singleton ProgramConfig. Place this suite LAST so it doesn't
  // break earlier tests that rely on `resolverKey` being the active resolver.
  // Each test also restores the original resolver at the end for idempotency.
  describe("transfer_resolver", () => {
    it("rotates the resolver key when called by the current resolver", async () => {
      const newResolver = anchor.web3.Keypair.generate();
      await airdrop(newResolver.publicKey);

      await program.methods
        .transferResolver(newResolver.publicKey)
        .accounts({
          currentResolver: resolverKey.publicKey,
          config: configPda,
        })
        .signers([resolverKey])
        .rpc();

      let config = await program.account.programConfig.fetch(configPda);
      expect(config.resolver.toBase58()).to.equal(newResolver.publicKey.toBase58());

      // Restore original resolver so the test suite remains idempotent
      // against the existing localnet ledger.
      await program.methods
        .transferResolver(resolverKey.publicKey)
        .accounts({
          currentResolver: newResolver.publicKey,
          config: configPda,
        })
        .signers([newResolver])
        .rpc();

      config = await program.account.programConfig.fetch(configPda);
      expect(config.resolver.toBase58()).to.equal(resolverKey.publicKey.toBase58());
    });

    it("rejects transfer_resolver from a non-resolver signer (UnauthorizedResolver)", async () => {
      const imposter = anchor.web3.Keypair.generate();
      await airdrop(imposter.publicKey);
      const target = anchor.web3.Keypair.generate();

      let err = "";
      try {
        await program.methods
          .transferResolver(target.publicKey)
          .accounts({
            currentResolver: imposter.publicKey,
            config: configPda,
          })
          .signers([imposter])
          .rpc();
      } catch (e) {
        err = String(e);
      }
      expect(err).to.include("UnauthorizedResolver");

      // Verify state unchanged.
      const config = await program.account.programConfig.fetch(configPda);
      expect(config.resolver.toBase58()).to.equal(resolverKey.publicKey.toBase58());
    });
  });
});
