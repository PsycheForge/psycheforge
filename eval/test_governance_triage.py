#!/usr/bin/env python3
"""Run all governance-triage fixtures through Hermes Agent and validate output.

Usage:
    python eval/test_governance_triage.py                        # run all fixtures
    python eval/test_governance_triage.py adversarial_permission.md   # run one
    python eval/test_governance_triage.py --dry-run              # render prompts only

Invocation path (confirmed against hermes-agent v0.10.0)
---------------------------------------------------------
Uses the Hermes CLI:
  hermes chat -q "<prompt>" -s <category>/<name> -Q

The `-Q` (quiet) flag strips the banner/spinner/tool previews and returns just
the final response. Hermes expects skill identifiers as `category/name` — for
this project the identifier is `research/governance-triage`, matching the
symlink setup_hermes_local.sh creates at ~/.hermes/skills/research/.

The hermes_agent distribution does not expose a top-level Python SDK (its
code is spread across `agent/`, `run_agent.py`, `batch_runner.py`, etc.), so
this runner commits to the CLI path.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Auto-reexec under the project-local Hermes venv if it exists.
# This lets `python eval/test_governance_triage.py` work without manually
# activating .hermes-agent/venv first. Set HERMES_NO_REEXEC=1 to skip
# (useful for debugging with the system Python).
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
from dataclasses import dataclass, field
from typing import Any

import yaml
from jsonschema import Draft202012Validator

DEFAULT_SKILL_DIR = REPO_ROOT / "skills" / "governance-triage"
FIXTURES_DIR = REPO_ROOT / "eval" / "fixtures"


@dataclass
class FixtureResult:
    name: str
    passed: bool
    output: dict | None = None
    schema_errors: list[str] = field(default_factory=list)
    runner_error: str | None = None
    expected_behaviors: list[str] = field(default_factory=list)
    raw_response: str | None = None


def parse_fixture(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text()
    if not text.startswith("---\n"):
        return {}, text.strip()
    _, fm_raw, body = text.split("---\n", 2)
    return yaml.safe_load(fm_raw) or {}, body.strip()


def build_prompt(proposal_text: str, frontmatter: dict[str, Any]) -> str:
    source_url = frontmatter.get("source_url") or "(none provided)"
    dao_context = frontmatter.get("dao_context") or "(none provided)"
    return (
        "Analyze this Solana DAO proposal using the governance-triage skill. "
        "Return ONLY a single JSON object matching the skill's output schema.\n"
        "\n"
        f"DAO context: {dao_context}\n"
        f"Source URL: {source_url}\n"
        "\n"
        "PROPOSAL TEXT:\n"
        f"{proposal_text}\n"
    )


class HermesRunner:
    """Invokes Hermes Agent's CLI to run the target skill.

    Invocation: `hermes chat -q <prompt> -s <identifier> -Q`
    Identifier format: `<category>/<name>` (e.g. `research/governance-triage`)
    matching the symlink layout under ~/.hermes/skills/ produced by the
    setup_hermes_local.sh script.
    """

    def __init__(self, skill_dir: Path, hermes_identifier: str, model: str | None = None):
        self.skill_dir = skill_dir
        self.hermes_identifier = hermes_identifier
        self.model = model

    def invoke(self, user_prompt: str) -> str:
        venv_hermes = REPO_ROOT / ".hermes-agent" / "venv" / "bin" / "hermes"
        exe = str(venv_hermes) if venv_hermes.exists() else "hermes"
        cmd = [exe, "chat", "-q", user_prompt, "-s", self.hermes_identifier, "-Q"]
        if self.model:
            cmd.extend(["-m", self.model])
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300,
            )
        except FileNotFoundError as e:
            raise RuntimeError(
                "`hermes` CLI not found. Run ./eval/setup_hermes_local.sh first."
            ) from e
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"hermes chat exited {e.returncode}.\n"
                f"stderr: {e.stderr[:800]}\n"
                f"stdout: {e.stdout[:200]}"
            ) from e
        return result.stdout


_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)


def extract_json(response: str) -> dict[str, Any]:
    """Extract a JSON object from the agent's response.

    Handles three common shapes:
      1. Pure JSON — single object, no prose.
      2. Fenced JSON — ```json ... ``` optionally preceded/followed by prose.
      3. Prose-embedded JSON — object starts at some offset, possibly with
         trailing session-info text. Uses raw_decode to tolerate trailing junk.
    """
    text = response.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced = _FENCE_RE.search(text)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    start = text.find("{")
    if start == -1:
        raise json.JSONDecodeError("No JSON object found in response", text, 0)
    obj, _ = json.JSONDecoder().raw_decode(text[start:])
    if not isinstance(obj, dict):
        raise json.JSONDecodeError("Top-level JSON value is not an object", text, start)
    return obj


def validate(output: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema)
    errors = []
    for err in validator.iter_errors(output):
        path = ".".join(str(p) for p in err.absolute_path) or "<root>"
        errors.append(f"{path}: {err.message}")
    return errors


def run_fixture(
    fixture_path: Path, runner: HermesRunner, schema: dict[str, Any], dry_run: bool
) -> FixtureResult:
    frontmatter, body = parse_fixture(fixture_path)
    expected = frontmatter.get("expected_behaviors") or []
    prompt = build_prompt(body, frontmatter)

    if dry_run:
        print(f"\n--- PROMPT for {fixture_path.name} ---")
        print(prompt)
        return FixtureResult(
            name=fixture_path.name,
            passed=True,
            expected_behaviors=expected,
        )

    try:
        raw = runner.invoke(prompt)
    except Exception as e:
        return FixtureResult(
            name=fixture_path.name,
            passed=False,
            runner_error=f"{type(e).__name__}: {e}",
            expected_behaviors=expected,
        )

    try:
        output = extract_json(raw)
    except json.JSONDecodeError as e:
        return FixtureResult(
            name=fixture_path.name,
            passed=False,
            schema_errors=[f"Non-JSON response: {e}. First 500 chars: {raw[:500]!r}"],
            expected_behaviors=expected,
            raw_response=raw,
        )

    errors = validate(output, schema)
    return FixtureResult(
        name=fixture_path.name,
        passed=not errors,
        output=output,
        schema_errors=errors,
        expected_behaviors=expected,
        raw_response=raw,
    )


def print_result(r: FixtureResult, verbose: bool) -> None:
    mark = "[ok]" if r.passed else "[x] "
    status = "PASS" if r.passed else "FAIL"
    print(f"\n{mark} {r.name} — {status}")
    print("-" * 60)

    if r.runner_error:
        print(f"  runner error:\n    {r.runner_error}")
        return

    if r.schema_errors:
        print(f"  schema errors ({len(r.schema_errors)}):")
        for e in r.schema_errors:
            print(f"    - {e}")
    else:
        print("  schema: valid")

    if r.output:
        direction = (r.output.get("treasury_impact") or {}).get("direction")
        rf_count = len(r.output.get("red_flags") or [])
        summary = r.output.get("summary", "<no summary>")
        rf_cats = [rf.get("category") for rf in (r.output.get("red_flags") or [])]
        print(f"  treasury_impact.direction: {direction}")
        print(f"  red_flags: {rf_count} ({', '.join(rf_cats) if rf_cats else '-'})")
        print(f"  summary: {summary}")

    if r.expected_behaviors:
        print("  expected behaviors (manual review):")
        for b in r.expected_behaviors:
            print(f"    - {b}")

    if verbose and r.output is not None:
        print("\n  full output:")
        print(json.dumps(r.output, indent=2, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("fixture", nargs="?", help="Single fixture filename (e.g. jupiter_grant.md)")
    parser.add_argument(
        "--skill-path",
        type=Path,
        default=DEFAULT_SKILL_DIR,
        help=f"Path to the skill directory (default: skills/{DEFAULT_SKILL_DIR.name})",
    )
    parser.add_argument(
        "--hermes-id",
        default=None,
        help="Hermes skill identifier in 'category/name' form (default: research/<skill-dir-name>)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Override the configured Hermes model for this run (e.g. anthropic/claude-sonnet-4.5). Passed through as `-m MODEL`.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Render prompts only; do not invoke agent")
    parser.add_argument("--verbose", action="store_true", help="Print full JSON output per fixture")
    args = parser.parse_args()

    skill_dir = args.skill_path.resolve()
    schema_path = skill_dir / "references" / "output-schema.json"
    hermes_identifier = args.hermes_id or f"research/{skill_dir.name}"

    if not skill_dir.exists():
        print(f"[x] Skill directory not found at {skill_dir}")
        return 2
    if not schema_path.exists():
        print(f"[x] Schema not found at {schema_path}")
        return 2
    if not FIXTURES_DIR.exists():
        print(f"[x] Fixtures dir not found at {FIXTURES_DIR}")
        return 2

    schema = json.loads(schema_path.read_text())
    runner = HermesRunner(skill_dir, hermes_identifier, args.model)

    if args.fixture:
        single = FIXTURES_DIR / args.fixture
        if not single.exists():
            print(f"[x] Fixture not found: {single}")
            return 2
        fixtures = [single]
    else:
        fixtures = sorted(FIXTURES_DIR.glob("*.md"))

    if not fixtures:
        print(f"[x] No fixtures in {FIXTURES_DIR}")
        return 2

    print(f"skill:    {skill_dir}")
    print(f"hermes:   {hermes_identifier}")
    print(f"schema:   {schema_path.name}")
    print(f"fixtures: {len(fixtures)}")
    if args.dry_run:
        print("mode:     dry-run (no agent invocation)")
    print("=" * 60)

    results = [run_fixture(f, runner, schema, args.dry_run) for f in fixtures]

    for r in results:
        print_result(r, args.verbose)

    passed = sum(1 for r in results if r.passed)
    print("\n" + "=" * 60)
    print(f"Summary: {passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
