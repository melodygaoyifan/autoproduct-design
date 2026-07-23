# Day 0 — Calibration Experiment

**Purpose.** Convert the §10 honest-time-estimate (24-30 weeks, 84-140 hours) from a reasoned-from-external-benchmarks number into an *empirically grounded* plan grounded in Melody's actual pace on the AgentHire codebase. The output of Day 0 is either (a) confirmation that the plan budget is realistic, or (b) early scope-cut decisions made BEFORE Week 1 instead of mid-build.

**Budget for Day 0 itself: 2-5 hours.** The 🟢 zone is < 2 hours (strictly); 🟡 is 2-3.5 hours (typical first-time outcome); 🔴 is > 3.5 hours. If you blow past 5 hours total, stop — the calibration signal is clear and continuing past 5 hours just wastes API budget.

**Date completed: ____________  Hours actually spent: ____________**

---

## Pre-flight (5 min)

- [ ] You have an Anthropic API key with at least $10 budget headroom
- [ ] You have a recent AgentHire PR (last 30 days) checked out locally — small but real, ~50-150 lines diff. NOT a docs-only PR.
- [ ] You're on the M1 Max MacBook (`yifangao` user). Python 3.11+ available.
- [ ] You have ~3-5 uninterrupted hours. Day 0 in fragments doesn't measure the right thing.

The PR you pick: __________________________________________________

---

## Step 1 — Minimal scaffold (30-45 min target)

Create only what's strictly needed for one voter to execute end-to-end. **No tests yet, no observability, no harness niceties.** This is deliberately stripped down — we're measuring voter-build time, not full-stack scaffolding time (that's Day 1).

```bash
mkdir autoproduct-day0 && cd autoproduct-day0
python3 -m venv .venv && source .venv/bin/activate
pip install anthropic pyyaml
mkdir -p src/autoproduct/{agents,llm,tools} skills tests/fixtures/correctness
touch src/autoproduct/__init__.py
```

Files to create (verbatim minimal — these are *Day 0 stubs*, not the full §09 implementations. The full Voter class per §09.4.2 takes `(config, llm, tools)` and `run(state)`. Day 0 deliberately collapses this to a one-method shim — we're measuring voter-build time, not framework-build time.):

- [ ] `src/autoproduct/llm/anthropic_client.py` — strip down §10 Day 4's `AnthropicClient` to just `complete()`, no retry, no token tracking. Take `api_key` in constructor (read from `os.environ["ANTHROPIC_API_KEY"]` in the run script). ~30 lines max.
- [ ] `src/autoproduct/agents/voter.py` — Day 0 stub class; one method `async def review(self, input_dict)` that builds the prompt from skill + diff and calls the LLM client. NOT the full §09.4.2 base class with config + tools + state. ~40 lines max.
- [ ] `skills/correctness.md` — verbatim copy from §09.4.4.1.
- [ ] `src/autoproduct/tools/read_file.py` — single function `read_file(path: str) -> str`. ~10 lines. (You won't actually call this in Day 0 — voter works from the diff in the fixture — but having it scaffolded confirms the import/path machinery works.)

Add `__init__.py` empty files to make src/autoproduct importable. Use `pip install -e .` OR set `PYTHONPATH=src` to make imports resolve.

**Stop watch.** Time spent on scaffold: ____ min.

If this took > 60 min, note why: ___________________________________
(Common causes: dep install issues, anthropic SDK version mismatch, M1-specific tooling — these reveal real friction your plan needs to absorb.)

---

## Step 2 — One fixture (15-20 min target)

Create one positive fixture for Correctness voter — a small synthetic diff with a clear correctness bug. Use the format from §09.11 fixture spec (simplified for Day 0 — we don't need the full envelope).

```yaml
# tests/fixtures/correctness/positive_001_unchecked_index.yaml
fixture_id: positive_001_unchecked_index
expected_finding_pattern: "(empty list|IndexError|unchecked|index out of range|empty.*skill)"
input:
  pr_description: "Add helper to extract candidate's top skill from resume"
  diff: |
    @@ -42,3 +42,8 @@ class ResumeParser:
        def parse(self, payload: dict) -> Resume:
            ...
    +
    +    def get_top_skill(self, skills: list[str]) -> str:
    +        """Returns the candidate's top skill (first in the list)."""
    +        return skills[0]
  changed_files: [agenthire/parsers/resume.py]
```

The bug: `get_top_skill` calls `skills[0]` with no empty-list check. On an empty list (which can happen if a candidate has no parsed skills), this raises `IndexError` at runtime — a clear correctness defect. Voter should flag this.

This fixture is unambiguous: the bug is purely defensive-coding, not a refactor or design choice that could be argued either way.

**Stop watch.** Time spent on fixture: ____ min.

---

## Step 3 — Wire it up + first run (45-60 min target)

Write a simple `run_correctness.py` script that:

1. Loads `correctness.md` skill
2. Reads the fixture YAML
3. Constructs the prompt: skill content + diff + PR description
4. Calls `claude-opus-4-7` (or `claude-sonnet-4-6` to save cost on Day 0; $0.30 vs $0.05 per call) via your `AnthropicClient`
5. Parses YAML output (`findings:` block)
6. Prints findings to stdout

```python
# run_correctness.py — minimal end-to-end
import asyncio, os, yaml, sys
from pathlib import Path
from src.autoproduct.llm.anthropic_client import AnthropicClient
from src.autoproduct.agents.voter import Voter

async def main():
    fixture = yaml.safe_load(Path(sys.argv[1]).read_text())
    skill = Path("skills/correctness.md").read_text()
    client = AnthropicClient(api_key=os.environ["ANTHROPIC_API_KEY"])
    voter = Voter(skill_content=skill, model="claude-sonnet-4-6", client=client)
    findings = await voter.review(fixture["input"])
    print(yaml.dump({"findings": findings}, sort_keys=False))

asyncio.run(main())
```

Run it:

```bash
python run_correctness.py tests/fixtures/correctness/positive_001_offbyone.yaml
```

Expected: voter outputs a finding mentioning "off-by-one" or "max_retries" (matches `expected_finding_pattern`).

**Stop watch.** Time spent on wire-up + first successful run: ____ min.

If the first run errors out, log what went wrong (count this debug time):
- [ ] API key issue
- [ ] YAML parsing of voter output (model returned text not YAML)
- [ ] anthropic SDK API change since §10 was written
- [ ] Other: __________________________________________________

Time on debug: ____ min.

---

## Step 4 — Calibrate against the fixture (20-30 min target)

Now check: did the voter actually catch the bug?

- [ ] Voter emitted at least one finding
- [ ] Finding text matches the `expected_finding_pattern` regex (case-insensitive) — should mention empty list, IndexError, or unchecked index access
- [ ] Finding's location references `get_top_skill` or `skills[0]` directly
- [ ] Severity is `medium` or higher (`low` is acceptable for first-iteration; `info` means the voter is not flagging it as a bug, which is wrong)

If all four boxes checked: voter calibrated against this fixture. ✅

If voter missed the bug or emitted noise instead:
- [ ] Re-read the skill prompt — is "missing null/empty checks" explicitly named in primary targets? (§09.4.4.1 lists "missing null checks" as a Correctness target — should be there.)
- [ ] Try the request once more (LLM nondeterminism — temperature 0.2 has small variance). If voter is truly inconsistent here, that's a calibration signal — note it.
- [ ] If still missing after 2 retries, edit the skill to add an explicit empty-collection-access example in the "Examples of good findings" section, then retry. Note the iteration count.

**Stop watch.** Time spent on calibration + skill iteration: ____ min.

---

## Step 5 — Run on the real AgentHire PR (30-45 min target)

Now run the same voter against your real AgentHire PR diff. This is the *real* signal — synthetic fixtures pass cleanly; real diffs are messier.

```bash
# Get the diff of your AgentHire PR
cd ~/path/to/agenthire
git diff main..feature/your-pr > /tmp/real_pr.diff

# Wrap it in fixture YAML
cat > /tmp/real_pr_fixture.yaml << EOF
fixture_id: real_pr_001
input:
  pr_description: "<paste PR description>"
  diff: |
$(sed 's/^/    /' /tmp/real_pr.diff)
  changed_files: [<paste changed files>]
EOF

cd ~/autoproduct-day0
python run_correctness.py /tmp/real_pr_fixture.yaml
```

Examine output:
- [ ] Voter ran without crashing
- [ ] Output is parseable YAML (not "let me think about this..." prose)
- [ ] At least one finding, OR `findings: []` with reasonable rationale

**Honestly assess the findings.** Are they:
- Real bugs you'd want to know about? Count: ____
- False positives (style nits, generic advice)? Count: ____
- Hallucinations (referencing code that's not in the diff)? Count: ____

The ratio is the calibration signal. **If real:fp:hallucination > 1:2:0**, the voter is roughly calibrated. If the ratio is worse, the skill needs more iteration than the §10 plan budget allows for.

**Stop watch.** Time spent on real PR run + assessment: ____ min.

---

## Step 6 — Compute the time multiplier (15 min)

Total Day 0 time: ____ hours (sum of all step stopwatches)

**Day 0 covers roughly 35% of full voter-build work.** What it covers: scaffold, one skill prompt setup, one fixture, basic calibration, smoke test on real input. What it does NOT cover: full 8-fixture set per voter, integration tests, voter envelope hardening, hooks integration, observability wiring, fresh-agent verification path, cost reconciliation. Those are the other ~65%.

So the projection formula is:

```
projected_full_voter_hours = day0_hours / 0.35
projected_voter_total_hours = projected_full_voter_hours × 8 voters × 1.15 difficulty_multiplier

# 0.35 — Day 0 fraction of full voter (rough; this is what Day 0 measures)
# 8 — number of new voters in Weeks 7-20 (4 Deploy + 4 Maintenance)
# 1.15 — Deploy/Maintenance domain depth (IaC, multi-source signals) is moderately
#         harder than Correctness, BUT the harness already exists from v0.1.0 (so
#         framework work is amortized). Net: ~15% harder per voter.
```

**Worked examples:**

| Day 0 hours | Implied full voter (hours) | 8 voters total (hours) | §10 Weeks 7-20 budget = 42-70 hr | Verdict |
|---|---|---|---|---|
| 2.0 | 5.7 | 53 | Voters consume entire budget; nothing left for harness/policy/dashboard | 🟡 |
| 3.0 | 8.6 | 79 | 9-37 hours OVER budget for voters alone | 🟡 |
| 4.0 | 11.4 | 105 | 35-63 hours over budget — voters alone are 1.5-2.5× the Weeks 7-20 budget | 🔴 |
| 5.0 | 14.3 | 131 | Way over | 🔴 |
| 1.5 | 4.3 | 39 | Just under budget for voters; ~3-31 hours left for everything else | 🟢 |

The realistic "🟢 on track" zone is **Day 0 < 2 hours** (strictly under). That's tight; most people won't hit it on first attempt. **🟡 in the 2-3.5 hour range is actually the expected outcome.** A 2.0 hour Day 0 sits at the border — count it as 🟡 (be conservative).

Read the matrix above honestly, not aspirationally. If your Day 0 is in the 🟡 or 🔴 zone, that's the data; the response is to adjust scope or timeline NOW, not to assume you'll be faster on Voter #2.

**Decision matrix:**

- 🟢 **Day 0 < 2 hr.** Plan budget is reasonable. Proceed to Day 1.

- 🟡 **Day 0 in 2-3.5 hr.** Budget is consumed; harness/policy/dashboard work needs to come from somewhere. **Action required: cut 1-2 lowest-priority items NOW.** Candidates from the design:
  - §11.14 Confidence threshold A/B testing framework (push to v1.1.0)
  - §9.9.4 Learned-skill registry browser dashboard view (push to v1.1.0)
  - §11.11.2 Vercel/Cloud Run/ECS sketches (already v1.1.0 backlog — confirm)
  - §12.14 Replay framework (push to v1.1.0)
  - Reduce 8 voters to 6: drop LearnedSkill (compound loop manages without it short-term) AND drop CanaryAnalysis voter (kept for v1.0.0 if K8s; cut if Railway-only as AgentHire is — Railway has no canary anyway)

- 🔴 **Day 0 > 3.5 hr.** Plan is too tight as stated. **Action required:**
  - EITHER reduce to 6 voters AND extend timeline to 30-36 weeks
  - OR keep 8 voters AND extend timeline to 36-44 weeks
  - DO NOT proceed at 24-30 weeks with 8 voters. The math doesn't close.

What you decided: ___________________________________________________

---

## Step 7 — Capture the data (10 min)

Even if you decide to proceed unchanged, capture Day 0's data for future you:

Create `autoproduct-day0/RETRO.md`:

```markdown
# Day 0 retrospective

**Date:** ____________
**Total hours:** ____
**PR used:** <link>
**Model used:** claude-sonnet-4-6 / claude-opus-4-7

## Time breakdown
- Scaffold: ____ min
- Fixture: ____ min
- Wire-up + first run: ____ min
- Debug (if any): ____ min
- Calibration: ____ min
- Real PR run: ____ min
- Compute multiplier: ____ min

## Findings on synthetic fixture
- [ ] Voter caught the off-by-one
- Skill iterations needed: ____

## Findings on real AgentHire PR
- Real bugs flagged: ____
- False positives: ____
- Hallucinations: ____

## Verdict
- 🟢 / 🟡 / 🔴 — what was decided

## Surprises
What surprised you? (most useful field — write 2-3 sentences)
___________________________________________________________________
___________________________________________________________________
___________________________________________________________________

## Action items for Day 1+
- ___________________________________________________________________
- ___________________________________________________________________
```

Commit `autoproduct-day0/` to a personal-notes repo (NOT the public autoproduct repo). The Day 0 scaffold is throwaway code; the data is not.

---

## Step 8 — Author module specs for 3 critical AgentHire modules (60-90 min)

Per `11-ultimate-architecture.md` Part 16 (Spec is a first-class artifact), every non-trivial module gets a `.mas/specs/{module}.spec.yaml` declaring invariants, error classes, forbidden patterns, and expected change patterns. Day 0 deliverable: bootstrap this for 3 critical AgentHire modules.

**Pick the 3 modules where bugs would hurt customers most.** For AgentHire, the natural choices:

1. **Workday parser** (`agenthire/parsers/workday.py`) — handles untrusted external data; null-handling, rate-limit issues
2. **Resume builder** (`agenthire/builders/resume.py`) — customer-facing output; PII handling
3. **Screening engine** (`agenthire/screening/engine.py`) — scoring/ranking customers see

For each module (~20-30 min):

```bash
mkdir -p ~/path/to/agenthire/.mas/specs/parsers
touch ~/path/to/agenthire/.mas/specs/parsers/workday.spec.yaml
```

Use this template (also in `11-ultimate-architecture.md` §16.3):

```yaml
spec_version: "1.0"
module: agenthire.parsers.workday
maintainer: melodygao
last_reviewed: 2026-04-29

purpose: |
  [What this module is responsible for in 2-3 sentences]

invariants:
  - id: <ALL_CAPS_SHORT_ID>
    description: |
      [What property must always hold]
    test_reference: tests/<path>::<test_name>  # OK to leave blank for Day 0

error_classes:
  - <ErrorClassName>  # Errors this module is allowed to raise

forbidden:
  - <forbidden side effect or pattern>

expected_change_patterns:
  - "<typical PR description that would touch this module>"

unexpected_change_patterns:
  - "<PR description that would smell wrong if it touched this module>"
```

**Checklist for a good Day 0 spec:**

- [ ] Spec is < 80 lines (more = over-specifying for Day 0; refine later)
- [ ] At least 2 invariants captured (not 0; not 10)
- [ ] At least 1 forbidden pattern (e.g., "logging response bodies")
- [ ] At least 1 expected change pattern (helps Code Review weight typical PRs less harshly)
- [ ] At least 1 unexpected change pattern (the high-signal entries)

**Time pressure escape hatch:** if Step 8 runs over 90 min, write 1 spec well rather than 3 specs poorly. Quality of one spec > quantity of three. The other two can be authored in Week 1.

This is the work that makes spec-driven prevention real. It's *not* time-pressure work — Step 8 going over budget is a sign you're authoring the specs honestly, which is the goal.

---

## What Day 0 explicitly does NOT include

- ✗ Full §5 ReviewState TypedDict (Day 1 work — too much for calibration)
- ✗ LangGraph orchestrator setup (Day 3 work)
- ✗ Webhook receiver (Week 9 work)
- ✗ Tests with pytest (Day 1 onwards; Day 0 we measure with stopwatch + manual eyeballing)
- ✗ Deterministic tools (Day 13+ tree-sitter, etc.)
- ✗ Cost tracking (Day 4+)

If you find yourself wanting any of these on Day 0, STOP and write them down for Day 1+. Day 0 is the smallest possible end-to-end loop. Adding to it defeats the calibration.

---

## Anti-pattern: doing Day 0 in fragments

Don't spread Day 0 across a week of 30-min sessions. Context-switch cost dominates at that fragment size; the time you measure won't reflect the time the real plan would take. Block 3-5 contiguous hours, ideally on a Saturday morning when you're fresh.

If you absolutely cannot do contiguous, the minimum unit is 90 min — enough for Steps 1-3 in one sitting and Steps 4-7 in another. Two 90-min blocks within a week.

---

## When Day 0 is "done"

Day 0 is done when ONE of these is true:

1. You completed all 8 steps and made an explicit 🟢/🟡/🔴 decision based on the Step 6 matrix, AND authored at least 1 module spec in Step 8
2. You hit a hard blocker (dep install fails, API rejected, M1 incompatibility) and have written down what the blocker is — the blocker becomes Day 1 first task
3. You've spent 7 hours total (Steps 1-7 budget = 5 hr; Step 8 budget = 60-90 min; with buffer = 7 hr) and aren't done — STOP. The pace signal is "your effective build pace is materially slower than the 🟢 zone". Revise plan to 36-44 weeks before proceeding, OR cut to 6 voters with original timeline.

Whatever the outcome, the Day 0 RETRO.md captures it. Day 1 reads RETRO.md as input.
