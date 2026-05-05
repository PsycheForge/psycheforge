#!/usr/bin/env python3
"""Batch resolver — read a manifest from batch_runner and close out each
prediction by calling resolve_proposal + (optionally) finalize_prediction
on-chain.

Usage:
    python eval/batch_resolver.py \\
        --manifest eval/outputs/batch_<ts>.json \\
        --outcomes outcomes.json \\
        --resolver-keypair ~/.config/solana/id.json \\
        --agent-pubkey 6Fxmg... \\
        [--finalize] \\
        [--rpc https://api.devnet.solana.com]

outcomes.json schema — one entry per proposal_id_hex that has closed:

    {
      "<proposal_id_hex>": {
        "final_outcome": 0,
        "distribution": [6000, 4000],
        "difficulty_bps": 9710
      },
      ...
    }

Entries not in outcomes.json are skipped (still open, not yet known).
Entries already marked resolved in the manifest are skipped.
Manifest is updated in place with resolve/finalize tx signatures + correctness.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_VENV_PY = REPO_ROOT / ".hermes-agent" / "venv" / "bin" / "python"
if (
    _VENV_PY.exists()
    and Path(sys.executable).resolve() != _VENV_PY.resolve()
    and not os.environ.get("HERMES_NO_REEXEC")
):
    os.execv(str(_VENV_PY), [str(_VENV_PY), *sys.argv])

import argparse
import json
import re
import subprocess
from typing import Any

ONCHAIN_DIR = REPO_ROOT / "onchain"
RESOLVE_TS = ONCHAIN_DIR / "clients" / "resolve_proposal.ts"
FINALIZE_TS = ONCHAIN_DIR / "clients" / "finalize_prediction.ts"
TS_NODE = ONCHAIN_DIR / "node_modules" / ".bin" / "ts-node"


def run_ts(script: Path, args: list[str], timeout: int = 120) -> tuple[str, str, int]:
    cmd = [str(TS_NODE), str(script)] + args
    result = subprocess.run(
        cmd, cwd=str(ONCHAIN_DIR), capture_output=True, text=True, timeout=timeout
    )
    return result.stdout, result.stderr, result.returncode


def validate_outcome(o: dict[str, Any]) -> None:
    required = {"final_outcome", "distribution", "difficulty_bps"}
    missing = required - set(o.keys())
    if missing:
        raise ValueError(f"outcome missing fields: {missing}")
    dist = o["distribution"]
    if not isinstance(dist, list) or len(dist) > 8 or sum(dist) != 10_000:
        raise ValueError(f"distribution must be a list of ≤8 ints summing to 10000 (got {dist})")
    if not (0 <= o["difficulty_bps"] <= 10_000):
        raise ValueError(f"difficulty_bps must be 0..10000 (got {o['difficulty_bps']})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--outcomes", required=True)
    parser.add_argument("--resolver-keypair", required=True)
    parser.add_argument("--agent-pubkey", required=True, help="Required if --finalize is set")
    parser.add_argument("--finalize", action="store_true")
    parser.add_argument("--rpc", default="https://api.devnet.solana.com")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text())
    outcomes: dict[str, Any] = json.loads(Path(args.outcomes).read_text())

    # Validate all outcomes upfront — fail fast on bad input.
    for pid, o in outcomes.items():
        try:
            validate_outcome(o)
        except Exception as e:
            print(f"[x] outcomes.json invalid for {pid[:16]}...: {e}")
            return 2

    print(f"manifest: {manifest_path}")
    print(f"outcomes: {len(outcomes)} proposal(s)")
    print(f"rpc:      {args.rpc}")
    print(f"finalize: {'yes' if args.finalize else 'no (resolve only)'}")
    print("=" * 60)

    processed = 0
    skipped_already_resolved = 0
    skipped_no_outcome = 0
    failed = 0

    for entry in manifest.get("entries", []):
        pid = entry.get("proposal_id_hex")
        slug = entry.get("slug", "<?>")

        if entry.get("resolved"):
            skipped_already_resolved += 1
            continue
        if not pid or pid not in outcomes:
            skipped_no_outcome += 1
            continue

        o = outcomes[pid]
        print(f"\n[{slug}] resolving")
        print(f"   proposal_id: {pid[:16]}...")
        print(f"   outcome:     {o['final_outcome']}")
        print(f"   distribution: {o['distribution']}")
        print(f"   difficulty:  {o['difficulty_bps']}")

        # Resolve
        _, rstderr, rrc = run_ts(RESOLVE_TS, [
            "--resolver-keypair", args.resolver_keypair,
            "--proposal-id", pid,
            "--outcome", str(o["final_outcome"]),
            "--distribution", ",".join(str(x) for x in o["distribution"]),
            "--difficulty-bps", str(o["difficulty_bps"]),
            "--rpc", args.rpc,
        ])
        if rrc != 0:
            entry["resolve_error"] = rstderr[:500]
            print(f"   [x] resolve failed: {rstderr[:300]}")
            failed += 1
            manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
            continue
        sig_match = re.search(r"\[ok\] resolve confirmed: (\S+)", rstderr)
        if sig_match:
            entry["resolve_tx_sig"] = sig_match.group(1)
        entry["final_outcome"] = o["final_outcome"]
        print(f"   [ok] resolve sig: {entry.get('resolve_tx_sig', '?')}")

        # Finalize (optional)
        if args.finalize:
            fstdout, fstderr, frc = run_ts(FINALIZE_TS, [
                "--cranker-keypair", args.resolver_keypair,
                "--proposal-id", pid,
                "--agent-pubkey", args.agent_pubkey,
                "--rpc", args.rpc,
            ])
            if frc != 0:
                entry["finalize_error"] = fstderr[:500]
                print(f"   [x] finalize failed: {fstderr[:300]}")
                failed += 1
            else:
                fsig_match = re.search(r"\[ok\] finalize confirmed: (\S+)", fstderr)
                if fsig_match:
                    entry["finalize_tx_sig"] = fsig_match.group(1)
                correctness_match = re.search(r"correctness_bps:\s*(\d+)", fstderr)
                if correctness_match:
                    entry["correctness_bps"] = int(correctness_match.group(1))
                json_lines = [l for l in fstdout.strip().splitlines() if l.strip().startswith("{")]
                if json_lines:
                    try:
                        data = json.loads(json_lines[-1])
                        entry["correctness_bps"] = data.get("correctness_bps", entry.get("correctness_bps"))
                    except json.JSONDecodeError:
                        pass
                entry["resolved"] = True
                print(f"   [ok] finalize sig: {entry.get('finalize_tx_sig', '?')}")
                print(f"   correctness_bps: {entry.get('correctness_bps')}")

        processed += 1
        # Persist after each entry
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print(f"  processed:                 {processed}")
    print(f"  skipped (already resolved): {skipped_already_resolved}")
    print(f"  skipped (no outcome yet):  {skipped_no_outcome}")
    print(f"  failed:                    {failed}")

    # Derive overall agent accuracy from resolved entries (if --finalize was used)
    resolved_with_scores = [
        e for e in manifest["entries"]
        if e.get("resolved") and e.get("correctness_bps") is not None
    ]
    if resolved_with_scores and args.finalize:
        # We don't have difficulty_bps stored on the entry — fetch from outcomes map for a local estimate.
        # Agent's authoritative numerator/denominator live on-chain.
        correct = sum(1 for e in resolved_with_scores if e["correctness_bps"] == 10_000)
        print(f"\n  resolved count: {len(resolved_with_scores)}")
        print(f"  correct calls:  {correct}/{len(resolved_with_scores)} (naive rate — on-chain is difficulty-weighted)")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
