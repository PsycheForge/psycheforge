#!/usr/bin/env python3
"""Format a governance-triage JSON output into a human-readable markdown summary.

Lite tier: triage only.
Premium tier: triage + prediction (pass --with-prediction).

Usage:
    # Lite tier output
    python eval/format_triage.py \
        --triage eval/outputs/.../live_mip15_triage.json \
        --source-url https://forum.marinade.finance/t/... \
        --output eval/outputs/lite_mip15.md

    # Premium tier output (adds outcome prediction section)
    python eval/format_triage.py \
        --triage path/to/triage.json \
        --with-prediction path/to/prediction.json \
        --source-url https://...

If --output is omitted, writes to stdout.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def short_title(summary: str, max_len: int = 80) -> str:
    """Pull a short, title-y phrase from the summary's first sentence."""
    if not summary:
        return "Proposal Triage"
    first = summary.split(".")[0].split("—")[0].strip()
    if len(first) > max_len:
        first = first[:max_len].rsplit(" ", 1)[0] + "…"
    return first


def render_header(triage: dict[str, Any], source_url: str | None) -> str:
    summary = triage.get("summary", "")
    title = short_title(summary)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out = [f"# {title}", ""]
    if source_url:
        out.append(f"**Source:** {source_url}")
    out.append(f"**Generated:** {today}")
    out.append(f"**Analyzed by:** PsycheForge `governance-triage` skill")
    out.append("")
    out.append("> **This is analysis, not voting advice.** The skill is hard-ruled to never recommend a vote. Every claim below is grounded in a verbatim citation from the proposal text — verify the citations yourself.")
    out.append("")
    return "\n".join(out)


def render_tldr(triage: dict[str, Any]) -> str:
    summary = triage.get("summary", "*no summary produced*")
    return f"## TL;DR\n\n{summary}\n"


def render_treasury(triage: dict[str, Any]) -> str:
    ti = triage.get("treasury_impact") or {}
    direction = ti.get("direction", "unknown")
    amount = ti.get("amount_usd")
    confidence = ti.get("confidence", "unknown")
    citation = ti.get("citation", "")
    amount_str = f"${amount:,}" if isinstance(amount, (int, float)) else "*not specified in USD*"
    out = ["## Treasury Impact", ""]
    out.append(f"- **Direction:** `{direction}`")
    out.append(f"- **Amount:** {amount_str}")
    out.append(f"- **Confidence:** `{confidence}`")
    out.append("")
    if citation:
        out.append(f"> *{citation}*")
        out.append("")
    return "\n".join(out)


def render_red_flags(triage: dict[str, Any]) -> str:
    flags = triage.get("red_flags") or []
    if not flags:
        return "## Red Flags\n\nNone. The skill evaluated all categories and found nothing flag-worthy.\n\n"

    # Sort by severity (high → medium → low) for skim-readability
    sev_order = {"high": 0, "medium": 1, "low": 2}
    flags = sorted(flags, key=lambda f: sev_order.get(f.get("severity", "low"), 3))

    out = [f"## Red Flags ({len(flags)})", ""]
    for i, rf in enumerate(flags, 1):
        cat = rf.get("category", "?")
        sev = rf.get("severity", "?")
        detail = rf.get("detail", "")
        cit = rf.get("citation", "")
        out.append(f"### {i}. `{cat}` — severity **{sev}**")
        out.append("")
        out.append(detail)
        out.append("")
        if cit:
            out.append(f"> *{cit}*")
            out.append("")
    return "\n".join(out)


def render_stakeholders(triage: dict[str, Any]) -> str:
    stake = triage.get("stakeholders") or []
    if not stake:
        return ""
    out = ["## Stakeholders", ""]
    for s in stake:
        name = s.get("name", "?")
        role = s.get("role", "?")
        cit = s.get("citation", "")
        cit_short = cit if len(cit) <= 100 else cit[:100] + "…"
        out.append(f"- **{name}** — `{role}` · *\"{cit_short}\"*")
    out.append("")
    return "\n".join(out)


def render_questions(triage: dict[str, Any]) -> str:
    qs = triage.get("questions_to_ask") or []
    if not qs:
        return ""
    out = [f"## Questions to ask before voting", ""]
    for i, q in enumerate(qs, 1):
        out.append(f"{i}. {q}")
    out.append("")
    return "\n".join(out)


def render_confidence(triage: dict[str, Any]) -> str:
    conf = triage.get("confidence") or {}
    overall = conf.get("overall", "unknown")
    unreadable = conf.get("unreadable_sections") or []
    out = ["## What this analysis could NOT read", ""]
    out.append(f"**Overall confidence:** `{overall}`")
    out.append("")
    if unreadable:
        out.append("The skill flagged these sections as unreadable from the proposal text alone (external references, linked specs, addresses not included, etc.):")
        out.append("")
        for u in unreadable:
            out.append(f"- {u}")
        out.append("")
    else:
        out.append("The skill analyzed every section of the proposal text. No external references or unreadable gaps.")
        out.append("")
    return "\n".join(out)


def render_premium_prediction(prediction: dict[str, Any]) -> str:
    out = ["---", "", "## Outcome prediction — Premium tier", ""]
    pred_outcome = prediction.get("predicted_outcome")
    conf_bps = prediction.get("confidence_bps", 0)
    reason = prediction.get("reasoning_citation", "")
    signals = prediction.get("key_triage_signals") or []

    label = {0: "approve / yes / pass", 1: "reject / no / fail"}.get(pred_outcome, f"option {pred_outcome}")
    out.append(f"- **Predicted outcome:** `{pred_outcome}` ({label})")
    out.append(f"- **Confidence:** {conf_bps} bps ({conf_bps / 100:.1f}%)")
    out.append("")
    out.append("**Reasoning:**")
    out.append("")
    out.append(f"> {reason}")
    out.append("")
    if signals:
        out.append("**Key triage signals that drove the prediction:**")
        out.append("")
        for s in signals:
            out.append(f"- `{s}`")
        out.append("")
    out.append("This prediction is **falsifiable**. After the vote closes, it is scored on-chain (difficulty-weighted) against the actual outcome. The agent's [Reputation PDA on Solana devnet](https://explorer.solana.com/address/3PDUJBj2LswT4fnUmGMMZrP3vriapUPRWUFJ66FRkoVS?cluster=devnet) accumulates the public, auditable accuracy history.")
    out.append("")
    return "\n".join(out)


def render_footer(tier: str) -> str:
    return f"""---

_Generated by **PsycheForge** ({tier} tier). This is analysis, not voting advice. The skill is hard-ruled to never recommend how to vote — it surfaces what's worth questioning. Every claim above carries a verbatim citation; if any cite doesn't match the proposal, the analysis is invalid. Source code: pending public release (MIT)._
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--triage", required=True, type=Path, help="Path to triage JSON")
    parser.add_argument("--with-prediction", type=Path, help="Path to prediction JSON (Premium tier)")
    parser.add_argument("--source-url", default=None, help="Source URL of the proposal (optional, included in header)")
    parser.add_argument("--output", type=Path, help="Write to file (default: stdout)")
    args = parser.parse_args()

    if not args.triage.exists():
        print(f"[x] triage file not found: {args.triage}", file=sys.stderr)
        return 2

    triage = json.loads(args.triage.read_text())
    is_premium = bool(args.with_prediction)
    tier = "Premium" if is_premium else "Lite"

    parts = [
        render_header(triage, args.source_url),
        render_tldr(triage),
        render_treasury(triage),
        render_red_flags(triage),
        render_stakeholders(triage),
        render_questions(triage),
        render_confidence(triage),
    ]

    if is_premium:
        if not args.with_prediction.exists():
            print(f"[x] prediction file not found: {args.with_prediction}", file=sys.stderr)
            return 2
        prediction = json.loads(args.with_prediction.read_text())
        parts.append(render_premium_prediction(prediction))

    parts.append(render_footer(tier))
    md = "\n".join(parts)

    if args.output:
        args.output.write_text(md)
        print(f"wrote {args.output} ({tier} tier)", file=sys.stderr)
    else:
        sys.stdout.write(md)

    return 0


if __name__ == "__main__":
    sys.exit(main())
