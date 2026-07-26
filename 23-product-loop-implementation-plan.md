# 23 — Product-Loop Implementation Plan

Part 67 + Appendices M–P. Implements docs 20–22: the evidence substrate, P0–P2 (opportunity, market, PRD), P3 (launch & growth with its deterministic backstops and experiment machinery), P4–P5 (evidence, attribution, prioritization, kill). Same conventions as docs 10/14/19: day-level granularity while the ground is new, week-level once patterns repeat; every week ends with checkable success criteria; the change-control protocol and the 20% week-buffer policy of §10 Part 11 apply verbatim. Time budget: **16 weeks**, calibrated by the Phase-0 rerun in P1 before anything after P4 is trusted.

**Prerequisite:** v1.4.0 minimum — the inner loop must be live end-to-end, because the outer loop's entire value is choosing what enters it. Building P0–P5 against an inner loop that cannot yet ship is a category error, and this plan should not start early.

**Build order rationale, and it is not the obvious one.** The obvious order is P0→P5, following the loop. The correct order is **substrate → the two most dangerous stages → the rest**:

1. **The claim substrate first (P1–P2 weeks).** Everything else is unsafe without it. `claim_lint` is the outer loop's `ears_lint`; a P0 shipped before it is a fabrication generator with a nice roster.
2. **P3's deterministic backstops second (P3–P5 weeks), before any P3 agent exists.** The checks that prevent irreversible external harm must exist before the machinery that could cause it. This inverts the usual generate-then-check build order deliberately, for the same reason F-21.1/F-21.2 have no rollback.
3. **P4 third.** Measurement before more generation. A team that builds P0/P1 before P4 will produce opportunities it cannot evaluate — and will feel productive doing it.
4. **P0/P1/P2 fourth**, on a substrate that can already catch them.
5. **P5 last**, because it consumes everything else's output.

A team that only ever completes steps 1–3 has a real improvement: honest claims, safe publishing, honest measurement. That is the intended kill-switch shape — every phase boundary is a legitimate stopping point.

---

## Milestones

| Version | Weeks | Contains | Release gate |
|---|---|---|---|
| **v2.1.0** substrate | P1–P2 | claim schema + `claim_lint` + evidence snapshotting + `synthetic_persona_scan` + `source_standing_check` + taint classes; ADR-U19/U22/U23 recorded | `claim_lint` catches 8/8 seeded fabrication fixtures; one real artifact (a retro market memo, hand-written) passes only after real corrections |
| **v2.2.0** safe-publish | P3–P5 | `marketing_server` MCP + the seven backstops (§21.58) + channel profiles + Gate PL3 approval surface; ADR-U20/U21 | every backstop fixture-gated at ≥87.5%; one real artifact published through the gate by a human; `forbidden_autonomous` additions loader-enforced and startup-tested |
| **v2.3.0** evidence | P6–P8 | P4 MAS + metric vocabulary + `analytics_server` with query-layer privacy enforcement + `attribution_typer`; ADR-U25 | one real cohort read end-to-end; person-level query returns an error, tested; one causal claim correctly rejected for lacking a holdout |
| **v2.4.0** upstream | P9–P13 | P0 + P1 + P2 MASes, gates, handoff contract | one opportunity travels P0→P1→P2→Stage 1 with the handoff machine-checked at Discovery's DoR gate |
| **v2.5.0** experiments | P12–P14 | Experiment MAS, pre-registration lock, two-stage FDR design, holdout tooling | one pre-registered two-stage experiment completed; one post-hoc edit correctly blocked by the hash pin |
| **v3.0.0** closed loop | P14–P16 | P5 + kill registry + hypothesis reconciliation + the five metrics | one full loop P0→…→P5 with a **recorded kill or pivot decision**; attention-cost baseline published |

The v3.0.0 gate is deliberately harsh: a full loop that ends in "continue" does not release. Until the machinery has actually stopped something, F-22.3 is unproven and the loop is a ratchet with extra steps.

---

## Week P1 — Phase 0 recalibration + the claim schema

**Day 1.** Phase-0 rerun, outer-loop flavor: hand-write one market memo and one PRD for a real candidate, timing yourself. This is the §10 Day-0 discipline applied to a new domain — every week estimate after P4 is calibrated against these two numbers, and they will not match the inner-loop numbers.
**Day 2.** ADR-U19, U22, U23 written and accepted before code (the framework's own rule: decisions precede implementation).
**Day 3–4.** `claims/*.claim.yaml` schema; JSON-Schema validation; `.mas/product-policy.yaml` with the inference ratio ceilings; the ledger→hypothesis-class mapping (§20.53.6) wired both directions.
**Day 5.** Seeded fabrication fixture set — 8 artifacts, each carrying exactly one planted failure: invented TAM, causal-without-holdout, proportion without n, expired evidence, synthetic testimonial, unsourced superlative, inference over ceiling, missing falsifier.

**Success:** schema validates; the 8 fixtures exist and are each hand-labeled with the rule that should fire.

## Week P2 — `claim_lint`, snapshots, taint

**Day 1–2.** `claim_lint.py` per §20.53.3, run standalone. All 8 fixtures caught, zero false positives on a clean control artifact.
**Day 3.** Evidence snapshotting: `.mas/evidence/<sha256>`, content-addressed; `snapshot_differ` for rot detection; `expires` handling.
**Day 4.** `synthetic_persona_scan` and `source_standing_check`; `.mas/signal-sources.yaml` with the standing field; loader fails closed on a source with no standing.
**Day 5.** `user_data_taint` class added to `.mas/taint-classes.yaml` alongside `research_taint`; loader tests that neither can be weakened by config.

**Success:** 8/8 fixtures caught; clean control passes; a config attempting to widen a taint rule fails startup with a named error. **Release v2.1.0.**

## Week P3 — `marketing_server` skeleton + substantiation

**Day 1.** MCP server scaffold under the existing tool registry, T1 subprocess sandbox, per-tool RBAC (§11.17) — no new transport, no exceptions to ADR-U08.
**Day 2–3.** `claim_substantiation_check` (§21.58.1) including `unmeasured_superlative` and `number_drift`; `claims_available` register schema; `release_to_p3.yaml` contract.
**Day 4–5.** `disclosure_lint` + `.mas/compliance-profile.yaml` with `verified_on` and review cadence. Ship with a **conservative default ruleset** and a prominent note that jurisdiction specifics are the operator's to confirm — the check is the deliverable, not the legal advice.

**Success:** a draft asserting an unregistered capability fails; a draft with a drifted number fails with both values quoted; a first-person testimonial fails on two independent rules.

## Week P4 — Deliverability, spam policy, brand safety

**Day 1–2.** `deliverability_preflight` (§21.58.3). Thresholds from config with a `verified_on` date; **consent and suppression checks are hard-coded as non-overridable** while placement thresholds are tunable — the distinction is tested.
**Day 3–4.** `spam_policy_check` (§21.58.4): publish-rate ceiling, shingling + embedding near-duplication, original-contribution floor (reads the claim ledger — the check that is nearly free here and hard everywhere else), query-variant fan-out, editorial attestation.
**Day 5.** `brand_and_safety_scan`: banned phrases, competitor mentions → review flag, unresolved template variables, PII scan, link check.

**Success:** a 10-page batch of near-duplicate drafts fails on similarity; a page with no `primary_measured` claim fails the contribution floor; an email with no consent record fails with no override path available.

## Week P5 — GEO checks, UTM lint, channel profiles, Gate PL3

**Day 1.** `geo_extractability_check` (§21.58.6): crawler-permission verification (including the CDN default-deny trap), structured data validity, passage extractability, inline-source requirement, author identity.
**Day 2.** `utm_and_instrumentation_lint`; no-PII-in-URL rule shared with the taint class.
**Day 3.** `.mas/channel-profile.yaml` + loader; the five profiles of §21.59; structural test that a profile cannot weaken a core check, mirroring the domain-profile test.
**Day 4–5.** Gate PL3 approval surface: artifact-exact preview, sentence→claim→evidence substantiation map, disclosure block, preflight summary, diff-vs-last-approved. **Scoped approvals only** — the data model has no representation for an unscoped approval, which is the strongest available form of the §21.61.5 rule.

**Success:** publish one real artifact through the gate, approved by a human, with the substantiation map reviewed. `forbidden_autonomous` additions enforced; a startup test proves a config cannot grant `publish_external`. **Release v2.2.0.**

## Week P6 — `analytics_server` and the privacy boundary

**Day 1–2.** Read-only analytics MCP server; **query-layer refusal of person-level rows**; k-anonymity floor applied server-side; free text through `pii_scan` before return.
**Day 3.** `feedback_server`: tickets, reviews, survey text — same egress rules, with locators that resolve into stored artifacts so `user_reported` claims can be verified.
**Day 4–5.** Metric vocabulary + `metrics/*.md` definition files; `metric_definition_check`; the `changed_at` baseline-reset mechanic.

**Success:** an agent request for individual rows returns an error (tested, not documented); a cohort under the floor returns a refusal; a metric cited without a definition file fails.

## Week P7 — P4 MAS

**Day 1–2.** EvidenceWriter + `cohort_calc` + `sample_sufficiency_check`.
**Day 3–4.** Five voter skills with disjoint lenses (§22.62.2); 8 fixtures each (4 positive, 2 negative, 2 boundary) per the standing fixture-gate contract; ≥87.5% to register.
**Day 5.** Verify pass + Leader + Gate PL4; `signal_router.py` splitting P4 from Stage 8 with conservative escalation.

**Success:** one real cohort read end-to-end; the Selection-Bias voter catches a planted vocal-minority reading; an ambiguous signal escalates rather than routing.

## Week P8 — Attribution

**Day 1–2.** `attribution_typer` (§22.63.2) at the tool boundary, so typing happens where data enters rather than where prose is written.
**Day 3.** `causal_without_experiment` end-to-end against real analytics output.
**Day 4–5.** Holdout tooling: assignment, exposure logging, geo/random splits, the analysis path shared with §21.61.

**Success:** a claim that a channel "drove" signups is rejected; the same observation restated as two typed facts passes; one real holdout designed (running it comes at P12). **Release v2.3.0.**

## Weeks P9–P10 — P0 Opportunity Sensing

`signal_server` with per-source standing and API-only access; dedupe + clustering (deterministic near-dup before embedding, per ADR-U05 ordering); OpportunityWriter; five voters with fixtures; Gate PL0. Kill-registry read path built now even though P5 does not write it until P14 — Novelty depends on it, and building the reader first surfaces the schema early.

**Success:** a week of real owned signals produces ≥3 candidates, each with ≥1 non-inference claim and a named cheapest test; a candidate matching a (hand-seeded) killed idea is surfaced with its history.

## Weeks P11–P12 — P1 Market & Viability

`competitor_probe` (public/API-permitted only, snapshotting, standing-checked); `sizing_calc` with mandatory sensitivity sweep and range output; the six voters including **Disconfirmation**; `injection_scan` over snapshots plus the source-concentration finding; Gate PL1 with its five-question rubric.

**Injection fixture set (P12, day 4–5):** planted instruction-shaped content in a snapshot; a single source supporting five claims; a snapshot whose hash changed since retrieval. Each must produce its finding.

**Success:** one real market assessment reaching Gate PL1 with a bottom-up range, a divergence from the top-down cross-check recorded rather than reconciled by prose, and Disconfirmation findings answered with evidence.

## Week P13 — P2 PRD

PRD schema + `prd_lint` (EARS/module leakage, non-goals ≥2, kill criteria present, every outcome measurable with instrumentation existing or task-generated); three voters; Gate PL2; the `p2_to_stage1.yaml` handoff **validated at Discovery's DoR gate**, so a malformed handoff fails there rather than being interpreted.

**Success:** one PRD passes; an `instrumentation.exists: false` outcome correctly generates a Planning task; a PRD naming modules fails the lint. **Release v2.4.0.**

## Week P14 — Experiment MAS

`power_calc`; `fdr_plan_check` (Benjamini-Hochberg for the screening stage); `preregistration_lock` (hash pinned pre-exposure, compared at analysis); sequential monitoring with a pre-specified spending function; two-stage screening→validation; the Ethics voter with hard veto; the inconclusive-enters-nothing rule wired into the compounding-loop boundary.

**Success:** one pre-registered two-stage experiment run to completion; a post-hoc edit to the registered design is blocked by hash mismatch; an underpowered design returns `BLOCKED(INSUFFICIENT_POWER)` with the required n stated. **Release v2.5.0.**

## Weeks P15–P16 — P5, the kill machinery, and the metrics

`evaluate_kill_criteria`; the append-only kill registry with `reusable_learning` and `revisit_if`; hypothesis reconciliation extended to market and PRD hypotheses with claim-ID propagation of invalidations; Gate PL5 with routing constraints (never directly to the inner loop); the five metrics instrumented, including **attention cost per resolved hypothesis** — the metric by which this whole track is falsifiable.

**Success and the v3.0.0 gate:** one complete loop with a recorded kill-or-pivot decision at Gate PL5; the fired criterion demonstrably could not be closed without it; attention-cost baseline published. **Release v3.0.0.**

---

## Appendix M — File tree delta (extends §14 Appendix E, §19 Appendix I)

```
autoproduct/
├── tools/product/{claim_lint,synthetic_persona_scan,source_standing_check,
│                  sizing_calc,prd_lint,snapshot_differ,signal_router}.py
├── tools/marketing/{claim_substantiation,disclosure_lint,deliverability_preflight,
│                    spam_policy_check,brand_safety_scan,geo_extractability,utm_lint}.py
├── tools/experiment/{power_calc,fdr_plan_check,preregistration_lock,holdout_assign}.py
├── tools/evidence/{cohort_calc,attribution_typer,sample_sufficiency,metric_definition_check}.py
├── servers/{signal_server,marketing_server,analytics_server,feedback_server}/   # MCP, T1/T2
├── harness/taint.py                      # research_taint + user_data_taint enforcement
skills/product/{opportunity,market,prd,evidence,prioritization}/*.md     # 24 voter skills
skills/marketing/{extractability,original_contribution,norm_fit,voice,consent_basis,
│                 relevance,validity,metric_integrity,ethics,sample_feasibility}.md
tests/integration/voters/fixtures/product/{voter}/*.yaml                 # 8 each
tests/fixtures/fabrication/*.yaml         # the 8 seeded claim-lint fixtures
tests/fixtures/injection/*.yaml           # planted-instruction snapshots
.mas/{product-policy.yaml,signal-sources.yaml,channel-profile.yaml,compliance-profile.yaml,
      strategy.yaml,kill-registry.yaml,taint-classes.yaml}
metrics/*.md                              # one definition file per metric, human-owned
claims/ product/ market/ experiments/ handoff/    # artifact directories
```

## Appendix N — Dependencies delta (extends §14 Appendix F, §19 Appendix J)

Deliberately thin. New Python deps: a statistics library for power/sequential boundaries and BH correction (`statsmodels`-class, pinned), a shingling/near-duplicate library or ~80 lines of local minhash, an HTML-to-text extractor for snapshotting, and a structured-data validator. Analytics and feedback sources are **wrapped, never vendored** — the operator's existing product analytics and support tooling are the runtime, same posture as the data profile's dbt/GE wrapping in §19 Appendix J. Search/AI-visibility vendor APIs are optional adapters behind the tool registry; none is required, and any vendor score enters as `third_party_report`. **No ad-platform SDK is a dependency, now or later** (ADR-U20).

## Appendix O — Risk register delta (extends §14 Appendix G, §19 Appendix K; F-20.x/F-21.x/F-22.x are the design-level FMEA, §22.66.3)

| ID | Risk | L×I | Mitigation |
|---|---|---|---|
| R-P1 | `claim_lint` is so strict that writers route around it with untyped prose | H×M | Lint runs on artifacts, not just ledgers: an artifact whose quantitative sentences lack ledger entries fails `no_claim_for_number`. Tune the ratio ceilings, never the requirement |
| R-P2 | Gate PL3 approval queue eats the human-attention budget (F-22.5) | **H×H** | Cadence ceilings default low; batch scoping rules; attention metric watched from P5 onward. The expected correct response is publishing less — say so in the README, not just here |
| R-P3 | Traffic too small to power any experiment, making P3's machinery dead weight | H×M | `BLOCKED(INSUFFICIENT_POWER)` is a *supported* outcome with a qualitative fallback path; the experiment MAS is optional in the profile. A 200-visit/week product should use P4's cohort reads and skip P3 experiments entirely |
| R-P4 | Compliance ruleset goes stale and the check certifies the wrong thing | M×H | `verified_on` + review cadence in the profile; the check fails closed on an expired ruleset rather than passing on old rules — same posture as `expires` on claims |
| R-P5 | The outer loop becomes a ratchet: nothing is ever killed | M×H | Kill criteria required at P2; loop budget; mandatory review; kill rate as a published metric; **the v3.0.0 release gate requires a real kill or pivot** |
| R-P6 | Platform policies shift under the channel profiles | H×M | Every platform limit is config with a `verified_on` date (the §17.43 discipline); rejections and enforcement actions become preflight fixtures via ADR-U14's loop |
| R-P7 | Operator uses the framework to industrialize low-value content anyway | M×H | Structural: no publish-rate reward exists, ceilings only; original-contribution floor; `spam_policy_check`. Not solvable beyond this — a determined operator can always disable checks, and that is true of every gate in the system |
| R-P8 | Two loops, one team: the outer loop starves the inner one of attention | M×H | Shared WIP and attention budgets (§16.38), outer-loop WIP default 1–2, `attention_spent` reported in the P4→P5 contract every cycle |

## Appendix P — Glossary delta (extends §14 Appendix H, §19 Appendix L)

**Outer loop / product loop (P0–P5)** the weeks-to-months loop around the eight-stage inner loop (§20.52.2, ADR-U19) · **Claim ledger** the typed, per-artifact record of every quantitative or comparative assertion (§20.53.2) · **`source_type`** the five-value provenance enum; `primary_measured` is the only type that may ground a causal claim · **Falsifier** the disconfirming observation every claim must state · **Evidence snapshot** the content-addressed capture of an external source at retrieval time · **`user_data_taint`** the privacy taint class; person-level data never leaves the analytics boundary (§22.64) · **`claims_available`** the substantiation register emitted at release; marketing may not assert beyond it (§21.57.4) · **Channel profile** a launch-channel delta on the P3 stage, same mechanism as domain profiles (ADR-U12) · **Cadence ceiling** the per-channel publish maximum; there is never a minimum (§21.59.5) · **GEO** generative engine optimization; admissible in its verifiability-increasing form only (ADR-U21) · **Two-stage experiment** screening with FDR control, then validation of the leader on a fresh sample (ADR-U24) · **Pre-registration lock** the hash pin that makes post-hoc design edits a gate failure · **Holdout** the withheld control group that makes a causal claim legal (ADR-U25) · **Kill criteria** the PRD-time conditions that force a Gate PL5 decision · **Kill registry** the append-only record of killed/pivoted work with reusable learning and revisit conditions · **Loop budget** `max_loops` per PRD; exhaustion forces review · **Attention cost per resolved hypothesis** the metric by which the product loop is falsifiable (§22.66.4) · **P1–P16** the product-loop track weeks (this doc); not to be confused with **P0–P5**, the outer-loop stages, or **Gate PL0–PL5**, their gates · **Why the `PL` prefix** `Gate P1` was already taken by the external-platform-review gate class (§17.41.3, ADR-U14), which is unchanged and unrelated.
