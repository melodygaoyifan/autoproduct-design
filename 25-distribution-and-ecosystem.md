# 25 — Distribution, DX & Ecosystem: How the Platform Reaches People Without Lying to Them

Parts 73–76. Doc 24 defined who the three doors are for; this document defines how anyone walks through one — packaging, time-to-first-value, the public benchmark, telemetry ethics, community mechanics, and positioning that survives the repo's own claim linter. The last part closes the loop that docs 20–23 opened: **the platform's own launch runs through its own P0–P5**, and its README claims are checked by its own tools. Numbering: ADR-U28+, invariants 14.23+, FMEA F-25.x.

---

## Part 73 — Developer experience & packaging

### 73.1 The time-to-first-value ladder

Adoption dies in the gap between "interesting README" and "first real output." The ladder makes each rung cheap and each next rung visible:

| Rung | Command | Time | Requires | Proves |
|---|---|---|---|---|
| R0 read | README + one real-run transcript | 3 min | nothing | the shape of the thing |
| R1 replay | `uvx autoproduct replay --demo` | 2 min | Python 3.12; **no API key** | gate records, verdicts, and the audit trail are real — replays a vendored product-bench run offline |
| R2 bench | `autoproduct bench` | ~10 min | one API key | the seeded-defect catch rates in §74 reproduce on *your* machine |
| R3 build | `autoproduct create demo --profile web` on the group-buy FDR | under an hour | API key | FDR → plan → code → tests → review, end to end |
| R4 yours | `autoproduct init --edition <e>` on a real workspace | Day 0 (§day-0-calibration) | your repo | the multiplier, measured, before commitments |

R1 is the load-bearing rung and the only new engineering in this part: a vendored, redacted run bundle plus offline replay path, so the audit-trail claim is verifiable by someone who has not yet decided to trust us with a key. Everything else on the ladder already exists in the CLI (`RUNBOOK.md`).

### 73.2 Packaging decisions

PyPI as `autoproduct` (uv-first; `uvx` for R1); GitHub releases with attested artifacts; **no Homebrew/npm wrappers at v1** (each is a supply-chain surface and a version-skew source — revisit on demand, record the demand). Templates are not a separate artifact: **product-bench workspaces double as starter templates** (`autoproduct init --from bench/01-groupbuy-api`), which keeps templates honest — they are the same fixtures the benchmark runs, so a template that rots fails CI, not a user.

### 73.3 Docs topology (three doors, §68.2, made literal)

`editions/{enterprise,solo,engineer}/START-HERE.md` — each ≤2 pages, each ending at the same Day-0 calibration. The nineteen design docs stay the canon; the START-HERE files are *routes into* them, not summaries that can drift (each links to sections, never restates rules — restated rules fork).

---

## Part 74 — product-bench as the public trust artifact

### 74.1 What gets published, and the reporting rules

The four workspaces (group-buy API, shortener API, group-buy auto, direction workbench) plus their seeded-defect manifests and pinned expected findings become the **published benchmark**. Reporting rules are claim-lint semantics applied to ourselves:

- Every published number carries model ID, date, harness version, and run count; single-run numbers are labeled `n=1` and never headline.
- Catch-rate claims come only from seeded-defect manifests (`autoproduct toolchain --manifest`); lanes without calibrated manifests publish **PROVISIONAL** and say so in the same font size.
- Regressions publish too: `eval-gate` baselines are in-repo, so a version that drops recall shows in the diff. **A benchmark you can only pass is marketing; one you can fail in public is evidence.**
- No cross-framework comparison tables. Comparing our recall to another framework's would require running *their* harness at equal effort, which we have not done; the honest form is "here is ours, runnable" (§76.2). This also keeps us out of the `unmeasured_superlative` bucket by construction.

### 74.2 Versioning & compatibility policy

SemVer over the **contract surface**, which is enumerated, not vibes: FDR schema · `.mas/*` schemas (specs, substrate, edition, data-checks, cab-preflight) · CLI commands and exit codes · gate names and record schemas · skill frontmatter. Breaking any of these bumps major; a migration note per break is a release gate. Deprecations live one minor version minimum with a loud runtime warning. The design docs themselves are versioned artifacts: docs-only corrections land as errata (doc 15 §8 pattern) rather than silent edits, because the docs are part of what people adopt.

### 74.3 Invariant

| Invariant | Statement | Enforced by |
|---|---|---|
| 14.23 | No published performance number without an in-repo manifest + pinned baseline that reproduces it | release checklist runs `bench` + `eval-gate`; PUBLISHING.md gains the checkbox |

---

## Part 75 — Telemetry, community, and governance

### 75.1 ADR-U28 — Telemetry is opt-in, aggregate-only, and inspectable

**Decision.** Default **off**. `autoproduct telemetry on` enables a schema-pinned payload: version, edition, substrate rung, stage-completion counts, gate-outcome counts, error classes. **Never**: FDR content, code, prompts, model outputs, repo names, claims-ledger content. `autoproduct telemetry show` prints the exact next payload before anything sends; the schema lives in-repo and is versioned under §74.2. *Rejected:* opt-out default (the enterprise edition's procurement pack would then need an exceptions story, and 48.8% of the EU non-adopters cited data protection — §69); "anonymous" free-text error reports (free text is where secrets leak). This is also self-interested honesty: §22.64's `user_data_taint` rules would be absurd to preach if our own telemetry didn't clear them.

### 75.2 Community mechanics — contribution is gated the way everything else is

- **Skills:** a contributed skill is a PR containing frontmatter + fixture + expected findings; FixtureGate runs in CI; no fixture, no merge. The SkillsBench finding (§71.1) is the rationale on the tin: the ecosystem's median public skill is mediocre *because nothing stops it from registering*; ours can't be, structurally.
- **Lanes and profiles:** a new language lane lands PROVISIONAL until its seeded-defect manifest is calibrated (§19 rule, unchanged, now applied to outsiders — same bar for the maintainer and a stranger).
- **Watch items ledger** (extends doc 16 §40.6): Agent Skills spec convergence; MCP Server Cards / statelessness (spec ~June 2026, adoption trailing); A2A revisit trigger (§71.2). Each has an owner, a review date, and a "what would change our mind" line — watch items without falsifiers are vibes.
- **Governance honesty:** single-maintainer project, stated plainly in CONTRIBUTING (bus factor = 1 is a fact, not a flaw to hide); decision rights = maintainer; the escalation path if that changes is an ADR, not a constitution written for a community that doesn't exist yet.

### 75.3 FMEA

| ID | Failure | S×L | Detection / mitigation |
|---|---|---|---|
| F-25.1 | Community skill passes its own fixture but is adversarial elsewhere (fixture-overfit) | M×M | fixtures are reviewed as code; bench regression run on merge; trust tiers apply to contributed skills exactly as to internal ones |
| F-25.2 | Benchmark numbers cited without PROVISIONAL/context labels by third parties | M×H | can't prevent quoting; can make the canonical page the top result (§76.2) and keep labels in the artifact filenames themselves |
| F-25.3 | Telemetry schema drifts into sensitive fields via well-meant PRs | H×L | schema change = major-version review + `telemetry show` diff in PR template |

---

## Part 76 — Honest positioning, and the loop closed

### 76.1 Positioning statement (the one allowed to appear anywhere)

*"An open, full-lifecycle multi-agent methodology and harness: one requirements document in the founder's own words → planned, built, tested, reviewed, maintained, and honestly marketed — every automated decision on the record. Deterministic gates first, LLM judgment second. Three editions, one spine."* Every clause maps to a shipped artifact or a numbered ADR; nothing in it is comparative.

### 76.2 What we say about the others

Orchestration SDKs (LangGraph, CrewAI, Agents SDKs, Microsoft Agent Framework) are **complements at a different layer**, and the docs say so with a straight face — an engineer can use their mental models and still adopt this repo's lifecycle, gates, and evidence discipline. The comparison page is one table: *layer, opinion held, opinion delegated* — no scores, no adjectives. Where a claim about the landscape is needed, it cites the survey, not our opinion of the survey.

### 76.3 ADR-U29 — The platform's own claims pass its own linter, in CI

**Decision.** `README.md` and the published benchmark page are parsed in CI; every quantitative or comparative sentence must resolve against `/.mas/claims/platform.yaml` — the platform's own claim ledger, typed per §20.53 (the ~190 hermetic tests: `primary_measured`, locator = CI run; the 88%-pilot figure: `third_party_report`, locator = source URL, expiry set). `product_loop_tools.py substantiation` is the checker; a README edit that asserts beyond the ledger **fails CI**. *Rejected:* manual review only (the 07-18 session's defensible-claims list was manual, and manual lists rot — this mechanizes the same discipline). This is the dogfooding closure: the tool built to keep P3 honest keeps the repo that ships it honest.

### 76.4 Launch runs through P0–P5, and produces the platform's own evidence

The GitHub release is executed as an outer-loop pass: PRD with kill criteria (*"if the framework's own weekly maintenance attention exceeds its budget for 4 consecutive weeks, scope is cut per Gate PL5"* — §22.66.4's metric pointed at ourselves), P3 restricted to `content_geo` + `product_surface` (E2 defaults; we are the solo persona), claims from `platform.yaml` only, launch-week experiment pre-registered with the §21.61 machinery. The kill registry's first entry may well be one of our own launch hypotheses, and that would be the strongest trust artifact this document could ask for.

**Implementation delta (extends doc 23's track):** weeks P17–P20 — P17 R1 offline replay bundle + `edition_lint`; P18 editions + START-HERE routes + procurement pack; P19 benchmark page + platform claim ledger + ADR-U29 CI; P20 launch pass through P0–P3. Same buffer policy; same change-control.

---
*Cross-references: §11 (FixtureGate, tiers), §16 (watch list), §18–19 (lanes, PROVISIONAL), §20–23 (claim ledger, backstops, experiment, kill), §24 (editions). New external figures land in doc 15 §6 with this revision.*
