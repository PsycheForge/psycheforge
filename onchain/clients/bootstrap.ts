#!/usr/bin/env ts-node
/**
 * bootstrap — Idempotent setup for a demo run.
 *
 * Ensures the following on-chain state exists, in order:
 *   1. ProgramConfig PDA with `resolver` set to the resolver keypair's pubkey.
 *   2. AgentReputation PDA for the agent keypair.
 *   3. A fresh Proposal PDA for the given proposal_id.
 *
 * Steps 1 and 2 are idempotent — if the account already exists, the step
 * logs "(already exists)" and continues. Step 3 always attempts creation and
 * will fail if the proposal_id collides with an existing PDA; choose a fresh
 * id per run.
 *
 * Usage:
 *   ts-node clients/bootstrap.ts \
 *     --resolver-keypair ~/.config/solana/id.json \
 *     --agent-keypair ~/.config/solana/id.json \
 *     --proposal-id 01ee000000000000000000000000000000000000000000000000000000000000 \
 *     [--dao-id <hex>] \
 *     [--num-choices 2] \
 *     [--voting-closes-slots-ahead 10000] \
 *     [--rpc http://127.0.0.1:8899]
 */

import * as anchor from "@coral-xyz/anchor";
import { Program, AnchorProvider, Wallet } from "@coral-xyz/anchor";
import { Connection, Keypair, PublicKey } from "@solana/web3.js";
import * as fs from "fs";
import * as path from "path";

interface Args {
  resolverKeypair: string;
  agentKeypair: string;
  proposalId: string;
  daoId: string;
  numChoices: number;
  votingClosesSlotsAhead: number;
  rpc: string;
  programId: string;
  idl: string;
}

function parseArgs(argv: string[]): Args {
  const out: Record<string, string | number> = {
    rpc: "http://127.0.0.1:8899",
    programId: "85huMKVbSddkbZiSk4XUBUSxsZS39tbd3sLp17viJJqH",
    idl: path.resolve(__dirname, "..", "target", "idl", "reputation.json"),
    numChoices: 2,
    votingClosesSlotsAhead: 10000,
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--resolver-keypair") out.resolverKeypair = argv[++i];
    else if (a === "--agent-keypair") out.agentKeypair = argv[++i];
    else if (a === "--proposal-id") out.proposalId = argv[++i];
    else if (a === "--dao-id") out.daoId = argv[++i];
    else if (a === "--num-choices") out.numChoices = parseInt(argv[++i], 10);
    else if (a === "--voting-closes-slots-ahead") out.votingClosesSlotsAhead = parseInt(argv[++i], 10);
    else if (a === "--rpc") out.rpc = argv[++i];
    else if (a === "--program-id") out.programId = argv[++i];
    else if (a === "--idl") out.idl = argv[++i];
    else if (a === "--help" || a === "-h") {
      console.error("see file header for usage");
      process.exit(0);
    } else {
      console.error(`unknown argument: ${a}`);
      process.exit(2);
    }
  }
  for (const req of ["resolverKeypair", "agentKeypair", "proposalId"]) {
    if (!out[req]) {
      console.error(`missing required --${req.replace(/([A-Z])/g, "-$1").toLowerCase()}`);
      process.exit(2);
    }
  }
  if (!out.daoId) out.daoId = out.proposalId; // default: reuse same bytes; demo-grade
  return out as unknown as Args;
}

function loadKeypair(p: string): Keypair {
  const expanded = p.startsWith("~/") ? path.join(process.env.HOME || "", p.slice(2)) : p;
  const raw = JSON.parse(fs.readFileSync(expanded, "utf8"));
  return Keypair.fromSecretKey(Uint8Array.from(raw));
}

function hexToBytes(hex: string): Uint8Array {
  const clean = hex.replace(/^0x/, "");
  if (clean.length !== 64) {
    throw new Error(`id must be 64 hex chars (got ${clean.length})`);
  }
  const bytes = new Uint8Array(32);
  for (let i = 0; i < 32; i++) bytes[i] = parseInt(clean.slice(i * 2, i * 2 + 2), 16);
  return bytes;
}

function isAlreadyInUse(err: unknown): boolean {
  return String(err).includes("already in use") || String(err).includes("custom program error: 0x0");
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv);
  const resolver = loadKeypair(args.resolverKeypair);
  const agent = loadKeypair(args.agentKeypair);
  const proposalIdBytes = hexToBytes(args.proposalId);
  const daoIdBytes = hexToBytes(args.daoId);
  const programId = new PublicKey(args.programId);

  const connection = new Connection(args.rpc, "confirmed");
  // Resolver provider for init_config + create_proposal. We use a second
  // provider for register_agent because that signer is the agent.
  const resolverProvider = new AnchorProvider(connection, new Wallet(resolver), { commitment: "confirmed" });
  const agentProvider = new AnchorProvider(connection, new Wallet(agent), { commitment: "confirmed" });

  const idl = JSON.parse(fs.readFileSync(args.idl, "utf8"));
  const programAsResolver = new Program(idl, resolverProvider) as any;
  const programAsAgent = new Program(idl, agentProvider) as any;

  const [configPda] = PublicKey.findProgramAddressSync([Buffer.from("config")], programId);
  const [reputationPda] = PublicKey.findProgramAddressSync(
    [Buffer.from("reputation"), agent.publicKey.toBuffer()],
    programId
  );
  const [proposalPda] = PublicKey.findProgramAddressSync(
    [Buffer.from("proposal"), Buffer.from(proposalIdBytes)],
    programId
  );

  console.error(`rpc:           ${args.rpc}`);
  console.error(`program:       ${programId.toBase58()}`);
  console.error(`resolver:      ${resolver.publicKey.toBase58()}`);
  console.error(`agent:         ${agent.publicKey.toBase58()}`);
  console.error(`proposal_id:   ${args.proposalId}`);
  console.error(`configPda:     ${configPda.toBase58()}`);
  console.error(`reputationPda: ${reputationPda.toBase58()}`);
  console.error(`proposalPda:   ${proposalPda.toBase58()}`);
  console.error("");

  // ── Step 1: initialize_config (idempotent) ─────────────────────────
  console.error("[1/3] initialize_config");
  try {
    const sig = await programAsResolver.methods
      .initializeConfig(resolver.publicKey)
      .accounts({
        payer: resolver.publicKey,
        config: configPda,
      })
      .rpc();
    console.error(`      ok: ${sig}`);
  } catch (e) {
    if (isAlreadyInUse(e)) {
      console.error("      (already exists, skipping)");
    } else {
      console.error(`      failed: ${e}`);
      throw e;
    }
  }

  // ── Step 2: register_agent (idempotent) ────────────────────────────
  console.error("[2/3] register_agent");
  try {
    const sig = await programAsAgent.methods
      .registerAgent()
      .accounts({
        agent: agent.publicKey,
        reputation: reputationPda,
      })
      .rpc();
    console.error(`      ok: ${sig}`);
  } catch (e) {
    if (isAlreadyInUse(e)) {
      console.error("      (already exists, skipping)");
    } else {
      console.error(`      failed: ${e}`);
      throw e;
    }
  }

  // ── Step 3: create_proposal (NOT idempotent — caller supplies fresh id) ─
  console.error("[3/3] create_proposal");
  const currentSlot = await connection.getSlot();
  const closesAt = new anchor.BN(currentSlot + args.votingClosesSlotsAhead);
  try {
    const sig = await programAsResolver.methods
      .createProposal(
        Array.from(proposalIdBytes),
        Array.from(daoIdBytes),
        closesAt,
        args.numChoices
      )
      .accounts({
        resolver: resolver.publicKey,
        proposal: proposalPda,
      })
      .rpc();
    console.error(`      ok: ${sig}`);
    console.error(`      voting_closes_at_slot: ${closesAt.toString()}`);
  } catch (e) {
    if (isAlreadyInUse(e)) {
      console.error(`      (proposal PDA already exists for id ${args.proposalId} — pick a fresh id)`);
      process.exit(1);
    }
    console.error(`      failed: ${e}`);
    throw e;
  }

  // Structured result on stdout for machine consumption.
  process.stdout.write(JSON.stringify({
    config_pda: configPda.toBase58(),
    reputation_pda: reputationPda.toBase58(),
    proposal_pda: proposalPda.toBase58(),
    proposal_id: args.proposalId,
    voting_closes_at_slot: closesAt.toString(),
  }) + "\n");
}

main().catch((err) => {
  console.error(`fatal: ${err}`);
  process.exit(1);
});
