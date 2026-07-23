# Day 0 — Calibration Experiments (Tracks A & B)

**Purpose.** Convert the plan-time estimates into empirically grounded numbers *before* committing to a build week. Track A calibrates the downstream (review-side) build pace; Track B calibrates the upstream (generative-side) pace. Each track's output is either (a) confirmation the plan budget is realistic, or (b) scope cuts made before Week 1 / Week U1 instead of mid-build.

Track A is unchanged from the prior edition (full text in `archive/day-0-calibration-v1.md`); its condensed protocol is retained below for self-containment. Track B is new and gates the doc-14 upstream track.

---

## Track A — Downstream (condensed; run before Week 1 of doc 10)

**Budget: 2–5 h.** 🟢 < 2 h · 🟡 2–3.5 h · 🔴 > 3.5 h · hard stop at 5 h.

1. **Minimal scaffold (30–45 min):** venv + `anthropic pyyaml`; stub LLM client (`complete()` only), one-method Voter shim, verbatim Correctness skill, `read_file` stub.
2. **One fixture (15–20 min):** a small synthetic diff with an unambiguous correctness bug + `expected_finding_pattern`.
3. **Wire-up + first run (45–60 min):** script loads skill+fixture → model call → parse YAML findings → stdout; expected: pattern matched.
4. **Record** per-step actuals and friction causes (SDK versions, YAML-not-returned, env issues).

**Date completed: ______ Hours: ______ Zone: 🟢/🟡/🔴**

---

## Track B — Upstream (run before Week U1 of doc 14)

**Budget: 2–4 h.** 🟢 < 1.5 h · 🟡 1.5–3 h · 🔴 > 3 h · hard stop at 4 h. Track B assumes Track A's scaffold exists (reuse the venv, LLM client, and voter shim — we are measuring *upstream-specific* build pace: a deterministic linter, an artifact writer, and an artifact-input voter).

### Pre-flight (5 min)

- [ ] Track A scaffold runs (its Step 3 script still works)
- [ ] One real feature idea from your actual backlog, one paragraph, pasted into `day0/feature-idea.md`. NOT a toy.
- [ ] 2–4 uninterrupted hours

The feature idea you picked: __________________________________________

### Step 1 — `ears_lint` v0 (30–45 min target)

The single highest-value upstream tool, and it's pure Python. Implement the five-pattern check + three violation types (no-pattern-match, multi-SHALL, missing-id). ~60 lines. Write 6 inline test cases (one valid per pattern that should pass, plus these three violations).

```python
# day0/ears_lint.py — minimal
import re
PATTERNS = [
    r"^AC-\d+.*?: THE SYSTEM SHALL .+",
    r"^AC-\d+.*?: WHEN .+ THE SYSTEM SHALL .+",
    r"^AC-\d+.*?: WHILE .+ THE SYSTEM SHALL .+",
    r"^AC-\d+.*?: IF .+ THEN THE SYSTEM SHALL .+",
    r"^AC-\d+.*?: WHERE .+ THE SYSTEM SHALL .+",
]
def lint(lines):  # -> list[(line_no, violation)]
    ...
```

**Stopwatch.** ears_lint time: ____ min. If > 60 min, note why (regex fights and pattern-edge debates are the usual causes — both are real friction doc 14 Week U1 Day 1 must absorb): ______________________

### Step 2 — SpecWriter shim, one real generation (45–60 min target)

Reuse the Track A voter shim shape as a writer: prompt = SpecWriter skill excerpt (Role + EARS rules + banned-vague-words list) + your real feature idea → ask for 5–8 EARS ACs with ids and FR tags. Pipe the output through your `ears_lint`.

- [ ] First generation: lint violations count: ____
- [ ] One revision pass (fresh call: artifact + violation list only — the §13.25.4 protocol in miniature): violations after: ____

**Stopwatch.** Writer wire-up + two runs: ____ min. Model returned non-parseable structure? Y/N — if Y, that's the friction the artifact schemas exist to catch; count the debug time.

### Step 3 — Ambiguity voter on the generated ACs (30–45 min target)

Voter shim with the Ambiguity skill excerpt (§13.28.4) + a 10-term banned list; input = your Step-2 ACs. Then hand-label: for each voter finding, is it right?

- [ ] Findings emitted: ____  · You agree with: ____  · Obvious misses (vague AC it didn't flag): ____

This 10-minute hand-label is your first fixture seed AND your first calibration datum for the 80-threshold discussion — keep the file.

**Stopwatch.** Voter + labeling: ____ min.

### Step 4 — Read the signal (10 min)

| Observation | Implication for doc 14 |
|---|---|
| Total 🟢 | 12-week budget credible; proceed as planned |
| Total 🟡 | Proceed, but pre-decide the U11 benchmark set size down (10 → 6) and hold Preflight out of scope until v1.3.0 decision point |
| Total 🔴 | Cut before starting: drop Discovery to v1.4.0+ (Spec+Coding+Plan still deliver the core loop), and/or drop deep-mode reverse interrogation to a fixed 5 questions |
| Step-2 revision converged (violations → 0-1) | The fresh-context revision protocol works at your prompt quality; 3-cycle bound is safe |
| Step-2 revision did NOT converge | Budget extra U2 days for SpecWriter skill iteration before touching voters |
| Step-3 agreement < 50% | Ambiguity skill needs your project's vocabulary — write the banned-term list from your real docs first (U1 Day 3) |

**Date completed: ______ Hours: ______ Zone: 🟢/🟡/🔴 Scope decisions taken: ______________________**

---

## Shared stop rule

Either track blowing its hard stop is itself the calibration result. Do not push through — write down where the time went, apply the corresponding scope cut, and start the week plan with honest numbers. The plan serves the pace; the pace does not serve the plan.
