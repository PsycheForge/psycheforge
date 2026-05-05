# eval/ — Governance Triage Evaluation Harness

Runs the `governance-triage` skill against canonical fixtures via the Hermes Agent framework and validates output against its JSON Schema.

## Layout

```
eval/
├── fixtures/
│   ├── jupiter_grant.md            # vague KPI grant (tests vague_kpi + outflow)
│   ├── marinade_param.md           # clean parameter change (tests no-false-positive)
│   ├── adversarial_permission.md   # buried upgrade authority (canary)
│   └── live_*.md                   # real proposals (e.g. live_mip15_marinade_labs_grant.md)
├── outputs/                        # generated artifacts (demo markdowns, batch manifests)
├── setup_hermes_local.sh           # one-time project-local Hermes install
├── test_governance_triage.py       # single-fixture triage runner
├── test_prediction_writer.py       # two-step chain runner (triage → prediction)
├── batch_runner.py                 # N-fixture chain runner + optional devnet submit
├── batch_resolver.py               # close out pending predictions using outcomes.json
└── README.md                       # this file
```

The skill itself lives at `skills/governance-triage/` with its SKILL.md and `references/output-schema.json`.

## Setup

### 1. Install Hermes Agent + register the skill (project-local, one-time)

```bash
./eval/setup_hermes_local.sh
# or, if not yet executable:
bash eval/setup_hermes_local.sh
```

The script does five things:

1. Clones `NousResearch/hermes-agent` into `.hermes-agent/` at the repo root.
2. Creates a dedicated Python venv at `.hermes-agent/venv/`.
3. Installs `hermes-agent` (editable) into that venv.
4. Installs the eval-harness deps from `requirements.txt` into the same venv.
5. Symlinks `skills/governance-triage/` → `~/.hermes/skills/research/governance-triage/` so Hermes can discover it as `research/governance-triage`.

No system PATH changes, no `.zshrc` / `.bashrc` edits, no global packages. Re-running the script is safe.

To remove everything: `rm -rf .hermes-agent/ ~/.hermes/skills/research/governance-triage`.

### 2. Configure a backend model + API key (required, one-time)

Without a configured provider, `hermes chat` errors with "No inference provider configured." Pick one path:

**Option A — Interactive:**

```bash
source .hermes-agent/venv/bin/activate
hermes model      # provider + model picker
deactivate
```

**Option B — API key in `~/.hermes/.env` (faster for scripts):**

```bash
echo 'OPENROUTER_API_KEY=sk-or-...' >> ~/.hermes/.env
# or OPENAI_API_KEY / ANTHROPIC_API_KEY / NOUS_API_KEY / etc.
```

Hermes also picks up `hermes config` defaults — see `hermes config` to inspect.

## Running

The runner **auto-reexecs** under `.hermes-agent/venv/bin/python` when that venv exists, so you do NOT need to activate the venv before each run. Your shell's Python can be anything.

```bash
# All fixtures
python eval/test_governance_triage.py

# Single fixture
python eval/test_governance_triage.py adversarial_permission.md

# Dry run (render prompts, no agent call — works even without the venv)
python eval/test_governance_triage.py --dry-run

# Verbose (print full JSON output per fixture)
python eval/test_governance_triage.py --verbose

# Point at a different skill (same harness works for any skill with a
# references/output-schema.json). Default is skills/governance-triage.
python eval/test_governance_triage.py --skill-path skills/some-other-skill

# Override the Hermes identifier (default: research/<skill-dir-name>).
# Useful if you symlinked the skill under a different category.
python eval/test_governance_triage.py --hermes-id domain/governance-triage
```

Flags combine freely: `--dry-run --verbose`, `--skill-path ... <fixture>`, etc.

Exit code is `0` only when every fixture parsed as JSON and validated against the schema. Non-zero on any schema or runner failure.

**Opt out of auto-reexec** (e.g. debugging with system Python):

```bash
HERMES_NO_REEXEC=1 python eval/test_governance_triage.py --dry-run
```

## What the runner does

For each `eval/fixtures/*.md`:

1. Parses YAML frontmatter (`source_url`, `dao_context`, `expected_behaviors`) and the Markdown body.
2. Builds a user prompt: DAO context + source URL + full proposal body + instruction to use the `governance-triage` skill and return JSON only.
3. Invokes Hermes via the project-local CLI: `hermes chat -q <prompt> -s <identifier> -Q`. The `-Q` flag suppresses banner/spinner so stdout is just the agent's final response.
4. Strips code fences and parses the response as JSON (models sometimes wrap JSON in ```json ... ``` blocks).
5. Validates the JSON against `skills/governance-triage/references/output-schema.json` using `jsonschema` (Draft 2020-12).
6. Prints per-fixture: schema result, top-line output fields, expected behaviors for manual review.

## Expected behaviors — manual review

The `expected_behaviors` block in each fixture's frontmatter is printed next to the model output but is **not** auto-asserted. Deliberate choice: this is a PoC-stage harness, not a CI gate. Human eval catches things a regex check would miss, and keeping the gate lightweight fits the "no product scaffolding before Risk A closes" discipline in `docs/open-risks.md`.

Auto-assertion becomes fair once (a) we have real customer-discovery signal and (b) we're running the skill at volume.

## Adding a fixture

1. Create `eval/fixtures/<slug>.md` with YAML frontmatter:

   ```markdown
   ---
   name: short_slug
   source_url: https://forum.example-dao.org/t/...
   dao_context: "Jupiter DAO, JUP token, ~$45M treasury"
   expected_behaviors:
     - "At least one red_flag with category=vague_kpi"
     - "treasury_impact.direction=outflow"
   ---

   # Proposal title
   ...body here...
   ```

2. Add a short block in `skills/governance-triage/references/test-cases.md` documenting what the fixture tests and what failure means.

That's it — the runner auto-discovers everything in `eval/fixtures/*.md`.

## Adjusting the Hermes invocation

Confirmed against `hermes-agent v0.10.0` (April 2026):

- **Command:** `hermes chat -q "<prompt>" -s <category>/<name> -Q`
- **Identifier format:** `category/name`. Our skill registers as `research/governance-triage` (the setup script creates the symlink).
- **No Python SDK:** `hermes-agent` does not expose a top-level `hermes_agent` module; its internals live in `agent/`, `run_agent.py`, `batch_runner.py`, etc. The runner commits to CLI.
- **Skill is a symlink → outside trusted dir warning:** Hermes prints a security warning because the symlink target (`skills/governance-triage/`) is outside `~/.hermes/skills/`. The skill still loads (`success: True`). Replace the symlink with a copy if the warning ever blocks something; for now it is informational.

If Hermes releases a stable Python API in a later version, `HermesRunner.invoke` is the only method to update — fixture loading, JSON extraction, schema validation, and reporting are framework-independent.

## Output schema

See `skills/governance-triage/references/output-schema.json`. Required top-level fields: `reasoning_trace`, `summary`, `stakeholders`, `treasury_impact`, `red_flags`, `questions_to_ask`, `confidence`. Strict mode (`additionalProperties: false`) — extra fields cause schema failure.

## Batch runs — the validation loop

Single-fixture runners (`test_governance_triage.py`, `test_prediction_writer.py`) are for development iteration. For **validating accuracy over N proposals** — the Risk B closure path — use the batch runners:

### `batch_runner.py`

Runs the chain on every fixture matching a glob. Saves triage + prediction JSONs, optionally commits each prediction to devnet. Writes a manifest tracking every fixture's status.

```bash
# Skill chain only (dev / rehearsal)
python eval/batch_runner.py --fixtures 'eval/fixtures/live_*.md'

# Full: skill chain + devnet commit (agent/resolver keypairs required)
python eval/batch_runner.py --fixtures 'eval/fixtures/live_*.md' \
  --submit-devnet \
  --agent-keypair ~/.config/solana/id.json \
  --resolver-keypair ~/.config/solana/id.json
```

Outputs:

- `eval/outputs/batch_<utc_ts>.json` — manifest (one entry per fixture, status field tracks progress)
- `eval/outputs/batch_<utc_ts>_artifacts/<slug>_triage.json` — skill output, one per fixture
- `eval/outputs/batch_<utc_ts>_artifacts/<slug>_prediction.json` — ditto

The manifest writes after every fixture so a crash mid-batch keeps completed work. Each entry has a `status` (`triage+prediction_ok` / `submitted` / `<stage>_failed`) you can grep on.

**Proposal IDs are deterministic:** `sha256(source_url)`. Re-running with the same `source_url` targets the same on-chain proposal PDA (fails the second submit by design — the PDA already exists). To re-predict a proposal, use a different fixture or edit `source_url`.

### `batch_resolver.py`

Closes out pending predictions after real votes have concluded. You supply an `outcomes.json` mapping proposal_id_hex to `{final_outcome, distribution, difficulty_bps}`; the script walks the manifest, calls `resolve_proposal` + (optionally) `finalize_prediction` for each entry you have data for.

```bash
python eval/batch_resolver.py \
  --manifest eval/outputs/batch_<ts>.json \
  --outcomes outcomes.json \
  --resolver-keypair ~/.config/solana/id.json \
  --agent-pubkey 6FxmgP46a8SBfuZdfR9G8iAKfBsRR9Xeg9CuQjFc5xQ4 \
  --finalize
```

`outcomes.json` schema:

```json
{
  "<64-char hex proposal_id>": {
    "final_outcome": 0,
    "distribution": [6000, 4000],
    "difficulty_bps": 9710
  }
}
```

Entries you don't have outcomes for are skipped (still open on-chain, not yet known). Entries already marked resolved are skipped. Manifest is updated in place with tx signatures + correctness.

### Typical validation-loop cadence

1. Curate 5-20 live fixtures as they open for voting (`eval/fixtures/live_*.md`, YAML frontmatter with `source_url`).
2. `batch_runner.py --submit-devnet` — skills run, predictions commit on-chain before voting closes.
3. Wait for real-world votes to close (days-weeks).
4. Build `outcomes.json` from Realms / Explorer / governance forum — one entry per closed proposal.
5. `batch_resolver.py --finalize` — resolve + score every entry with a known outcome.
6. Inspect manifest; compute agent accuracy from on-chain numerator / denominator.
7. Update prompts if signal pushes a direction; rerun on future proposals.

This is the loop that moves Risk B from "partially resolved" to "resolved with public track record."

## What the harness does NOT do (yet)

- Auto-assertion of `expected_behaviors`
- Retries on transient backend errors
- Token / cost accounting
- Parallel fixture execution
- Per-fixture diff against a "golden" previous output
- Automatic outcome scraping from Realms / on-chain (you build `outcomes.json` manually)
- Proposal discovery (you curate fixtures manually)

All reasonable adds once Risk A closes and the skill starts getting real use.
