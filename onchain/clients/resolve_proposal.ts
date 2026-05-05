#!/usr/bin/env ts-node
/**
 * resolve_proposal — Resolver writes the final outcome, distribution, and
 * difficulty onto a `Proposal` PDA. One-shot: a second call fails with
 * `AlreadyResolved`.
 *
 * Usage:
 *   ts-node clients/resolve_proposal.ts \
 *     --resolver-keypair ~/.config/solana/id.json \
 *     --proposal-id 01ee...00 \
 *     --outcome 1 \
 *     --distribution 4500,5500 \
 *     --difficulty-bps 8000 \
 *     [--rpc http://127.0.0.1:8899]
 *
 * `distribution` is a comma-separated list of up to 8 u16 values in basis
 * points that must sum to exactly 10000. Zero-padded on the program side.
 * `difficulty-bps` is 0-10000 (0 = unanimous, 10000 = max entropy).
 */

import * as anchor from "@coral-xyz/anchor";
import { Program, AnchorProvider, Wallet } from "@coral-xyz/anchor";
import { Connection, Keypair, PublicKey } from "@solana/web3.js";
import * as fs from "fs";
import * as path from "path";

interface Args {
  resolverKeypair: string;
  proposalId: string;
  outcome: number;
  distribution: string;
  difficultyBps: number;
  rpc: string;
  programId: string;
  idl: string;
}

function parseArgs(argv: string[]): Args {
  const out: Record<string, string | number> = {
    rpc: "http://127.0.0.1:8899",
    programId: "85huMKVbSddkbZiSk4XUBUSxsZS39tbd3sLp17viJJqH",
    idl: path.resolve(__dirname, "..", "target", "idl", "reputation.json"),
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--resolver-keypair") out.resolverKeypair = argv[++i];
    else if (a === "--proposal-id") out.proposalId = argv[++i];
    else if (a === "--outcome") out.outcome = parseInt(argv[++i], 10);
    else if (a === "--distribution") out.distribution = argv[++i];
    else if (a === "--difficulty-bps") out.difficultyBps = parseInt(argv[++i], 10);
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
  for (const req of ["resolverKeypair", "proposalId", "outcome", "distribution", "difficultyBps"]) {
    if (out[req] === undefined) {
      console.error(`missing required --${req.replace(/([A-Z])/g, "-$1").toLowerCase()}`);
      process.exit(2);
    }
  }
  return out as unknown as Args;
}

function loadKeypair(p: string): Keypair {
  const expanded = p.startsWith("~/") ? path.join(process.env.HOME || "", p.slice(2)) : p;
  return Keypair.fromSecretKey(Uint8Array.from(JSON.parse(fs.readFileSync(expanded, "utf8"))));
}

function hexToBytes(hex: string): Uint8Array {
  const clean = hex.replace(/^0x/, "");
  if (clean.length !== 64) throw new Error(`proposal-id must be 64 hex chars (got ${clean.length})`);
  const b = new Uint8Array(32);
  for (let i = 0; i < 32; i++) b[i] = parseInt(clean.slice(i * 2, i * 2 + 2), 16);
  return b;
}

function parseDistribution(spec: string): number[] {
  const values = spec.split(",").map((s) => parseInt(s.trim(), 10));
  if (values.some((v) => Number.isNaN(v) || v < 0 || v > 10000)) {
    throw new Error(`each distribution entry must be 0-10000 (got: ${spec})`);
  }
  if (values.length > 8) throw new Error(`distribution supports at most 8 entries (got ${values.length})`);
  const sum = values.reduce((a, b) => a + b, 0);
  if (sum !== 10000) throw new Error(`distribution must sum to 10000 (got ${sum})`);
  const padded = new Array(8).fill(0);
  for (let i = 0; i < values.length; i++) padded[i] = values[i];
  return padded;
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv);
  const resolver = loadKeypair(args.resolverKeypair);
  const proposalIdBytes = hexToBytes(args.proposalId);
  const distribution = parseDistribution(args.distribution);
  const programId = new PublicKey(args.programId);

  const connection = new Connection(args.rpc, "confirmed");
  const provider = new AnchorProvider(connection, new Wallet(resolver), { commitment: "confirmed" });
  anchor.setProvider(provider);
  const idl = JSON.parse(fs.readFileSync(args.idl, "utf8"));
  const program = new Program(idl, provider) as any;

  const [proposalPda] = PublicKey.findProgramAddressSync(
    [Buffer.from("proposal"), Buffer.from(proposalIdBytes)],
    programId
  );

  console.error(`rpc:            ${args.rpc}`);
  console.error(`resolver:       ${resolver.publicKey.toBase58()}`);
  console.error(`proposal_id:    ${args.proposalId}`);
  console.error(`proposalPda:    ${proposalPda.toBase58()}`);
  console.error(`outcome:        ${args.outcome}`);
  console.error(`distribution:   [${distribution.join(", ")}]`);
  console.error(`difficulty_bps: ${args.difficultyBps}`);
  console.error("");

  try {
    const sig = await program.methods
      .resolveProposal(Array.from(proposalIdBytes), distribution, args.outcome, args.difficultyBps)
      .accounts({ resolver: resolver.publicKey, proposal: proposalPda })
      .rpc();
    console.error(`[ok] resolve confirmed: ${sig}`);
  } catch (e) {
    console.error(`[x] resolve failed: ${e}`);
    process.exit(1);
  }

  const p = await program.account.proposal.fetch(proposalPda);
  console.error(`\non-chain Proposal (post-resolve):`);
  console.error(`  resolved:           ${p.resolved}`);
  console.error(`  final_outcome:      ${p.finalOutcome}`);
  console.error(`  difficulty_bps:     ${p.difficultyBps}`);
  console.error(`  resolved_at_slot:   ${p.resolvedAtSlot.toString()}`);

  process.stdout.write(JSON.stringify({
    proposal_pda: proposalPda.toBase58(),
    final_outcome: p.finalOutcome,
    difficulty_bps: p.difficultyBps,
    resolved_at_slot: p.resolvedAtSlot.toString(),
  }) + "\n");
}

main().catch((err) => { console.error(`fatal: ${err}`); process.exit(1); });
