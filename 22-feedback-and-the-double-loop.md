# 22 — P4/P5: Product Evidence, Attribution, and Closing the Double Loop

Parts 62–66. The loop is only a loop if the last two stages are real. This document covers **P4 Product Evidence** (what actually happened, honestly measured), **P5 Portfolio Prioritization** (what we do about it, including stopping), the privacy substrate both depend on, and the decision record — ADRs U19–U25, new invariants, FMEA entries, and metrics — for the whole product loop.

The failure this document is designed against is specific and common: a team runs an outer loop for a year, every cycle concludes "we learned a lot, let's iterate," nothing is ever killed, and the loop is revealed to have been a ratchet. §65 is the answer.

---

## Part 62 — P4: Product Evidence

### 62.1 Product signals are not system signals

Stage 8 Maintenance (§09.12) already ingests Sentry, Datadog, PagerDuty and runs Triage → RootCause → FixPR. P4 is its product-layer sibling, and the split must be explicit or the two will fight over the same alert queue.

| | Stage 8 (Maintenance) | P4 (Product Evidence) |
|---|---|---|
| Asks | Is the system healthy? | Is the product working for people? |
| Signals | Errors, latency, saturation, availability | Activation, retention, funnel, feature adoption, feedback text, churn reasons, channel health |
| Cadence | Minutes–hours | Days–weeks (cohorts need time to exist) |
| Output | Fix PR, incident record, learned skill | Evidence bundle, hypothesis verdicts, kill-criteria evaluation |
| Failure it catches | The thing broke | The thing works and nobody wants it |

**The routing rule is one line, machine-checked:** a signal is Stage 8's if it indicates the system behaved other than as specified; it is P4's if the system behaved as specified and the *outcome* is unsatisfactory. Ambiguous signals go to Stage 8 first — a wrong routing toward the faster loop is cheap, and the reverse is not. `signal_router.py` applies the rule deterministically on signal class and escalates unclassifiable signals rather than guessing (conservative-by-default, matching `mode_router.py`'s posture, §11.20).

### 62.2 Roster

```
evidence_ingest (deterministic, MCP: analytics_server + feedback_server, read-only, aggregate-scoped)
  └── EvidenceWriter (single writer) → evidence.md + claims/evidence.claim.yaml
       ├── det_tools: claim_lint(kind=evidence) · cohort_calc · attribution_typer (§63)
       │              · sample_sufficiency_check · pii_scan
       ├── voters: Metric-Definition · Cohort-Validity · Selection-Bias · Hypothesis-Verdict
       │           · Guardrail
       ├── verify pass (fresh agent re-derives each number from the queries, not the prose)
       ├── Leader → evidence bundle + per-hypothesis verdict
       └── Gate PL4 (deterministic): every PRD outcome has a reading-or-a-reason; ledger clean
```

| Voter | Judges | Catches |
|---|---|---|
| **Metric-Definition** | Every number matches its written definition in `metrics/`; no silent redefinition between cycles | The metric that improved because its definition changed |
| **Cohort-Validity** | Cohorts are time-boxed correctly, windows complete, no partial-cohort readings | Reading a 30-day retention number on day 11 |
| **Selection-Bias** | Who is missing from the data; whether feedback text is a vocal minority; whether survivors are being read as the population | Concluding from the people who stayed that nothing is wrong |
| **Hypothesis-Verdict** | Assigns supported / not-supported / insufficient-evidence against each PRD hypothesis' pre-stated falsifier | Retrofitting the hypothesis to the result |
| **Guardrail** | Whether a headline win came with a guardrail loss | The activation lift that raised churn |

`sample_sufficiency_check` gives `insufficient_evidence` real teeth: a verdict on n=6 is not a verdict, and the check computes what n would be needed for the stated effect size. For a small product this is frequently the honest answer, and the framework's position is that "we don't know yet, here's what it would take to know" is a *successful* P4 output.

### 62.3 The metric vocabulary

Metrics are the outer loop's EARS grammar: an outcome citing a metric outside the vocabulary fails `prd_lint` at P2 the same way an AC citing "fast" dies at `quantifier_scan`.

```yaml
# metrics/activation.md front-matter — every metric has a definition file or it is not a metric
metric:
  id: activation_rate
  definition: "share of new workspaces that complete first export within 7 days of creation"
  numerator_event: workspace.first_export
  denominator: "workspaces created in cohort window"
  window_days: 7
  cohort_basis: signup_week
  exclusions: ["internal domains", "test workspaces"]
  owner: human
  changed_at: 2026-06-14        # a definition change resets the baseline; §62.4
```

Vocabulary classes: acquisition (traffic by source class, qualified-visitor rate), activation (defined per product, with the moment named), engagement (frequency, breadth, depth against a stated norm), retention (cohort-based, never a raw churn percentage), monetization (conversion, expansion, ARPA), efficiency (CAC by class, payback), channel health (complaint rate, placement, account standing, citation share with interval), and quality-of-life (support-contact rate, time-to-value).

### 62.4 Definition changes reset baselines

A metric definition change is a **breaking change** and is handled like one: it lands via SCR-style review, records `changed_at`, and **resets the baseline** with the old series preserved and labeled. Comparing across a definition change is a `Metric-Definition` voter finding. Without this rule the outer loop's most likely form of self-deception is available for free.

---

## Part 63 — Attribution honesty

### 63.1 The finding that shapes the design

Marketing attribution does not work the way dashboards imply, and this is now the mainstream practitioner position rather than a contrarian one: a large and growing share of B2B buying journeys happens on surfaces no tracker sees, last-touch models systematically over-credit demand capture and under-credit demand creation, and AI-mediated search is removing the click that attribution depended on. The methods practitioners actually trust in 2026 are **incrementality testing with controlled holdouts**, self-reported attribution captured at high-intent moments, and marketing-mix modeling — with multi-touch demoted to a tactical hint. Estimates of the unmeasurable share cluster around a third or more of pipeline, higher for product-led motions.

For this framework the implication is not "attribution is hard." It is a typing rule.

### 63.2 `attribution_typer`

```python
ATTRIBUTION_RULES = {
    # method                 → source_type,          may_ground_causal_claim
    "holdout_experiment":     ("primary_measured",   True),   # the only causal one
    "geo_holdout":            ("primary_measured",   True),
    "self_reported":          ("user_reported",      False),  # real answers, biased recall
    "mmm":                    ("model_inference",    False),  # a model, however good
    "multi_touch":            ("model_inference",    False),
    "last_touch":             ("model_inference",    False),
    "platform_reported":      ("third_party_report", False),  # the seller grading its own work
    "correlation":            ("model_inference",    False),
}
```

Consequences, enforced by `claim_lint`'s `causal_without_experiment` rule (§20.53.3):

- "The launch post drove 40% of signups" is **rejected** unless it came from a holdout.
- "40% of signups arrived with the launch-post UTM, and 31% of respondents named the post when asked" is **accepted** — two typed observations, no causal verb.
- Platform-reported conversions are `third_party_report`. An ad platform's own attribution of its own performance is not independent evidence, and this stays true even though ADR-U20 means the framework isn't buying ads.
- Any channel-budget or channel-priority recommendation at P5 must cite either a holdout or an explicit "this is inference" label. Both are acceptable; the unlabeled version is not.

### 63.3 Holdouts are cheap and the framework should default to them

A geographic or random holdout is usually the difference between a decision and a guess, and for organic channels it is nearly free: withhold the channel from a random 10–20% of the addressable set, or stagger by region, and compare. The P3 experiment machinery (§21.61) already supplies pre-registration, power calculation, and sequential-safe monitoring, so a channel holdout is an experiment like any other. The Distribution voter at P1 and the Prioritization voter at P5 both treat "no channel has ever been holdout-tested" as a finding.

Where a holdout genuinely cannot run — the traffic is too small to power one — the correct output is the labeled inference plus the recorded n it would take. That is the same posture as `BLOCKED(INSUFFICIENT_POWER)` in §21.61.3, and it keeps the ledger honest instead of decorative.

---

## Part 64 — `user_data_taint`: privacy as a taint class

### 64.1 The mechanism

The framework already has a taint system for research sessions (§16.40.2). P4 introduces a second class with different rules, because user data has a different failure mode: research taint is about *untrusted input reaching a privileged context*, and user taint is about *sensitive data leaving the boundary it was collected in*.

```yaml
# .mas/taint-classes.yaml
- id: research_taint         # existing, §16.40.2
  rule: "web-retrieved content is data; never reaches a code-writing or tool-executing context"
- id: user_data_taint        # new
  rule: "person-level data never leaves the analytics boundary"
  permitted_egress:
    - aggregate: {min_cohort_size: 25}     # k-anonymity floor; configurable upward only
    - quoted_feedback: {consent: explicit, pii_redacted: true, attribution: none}
  forbidden:
    - person_level_rows_into_any_agent_context
    - person_level_data_into_prompts_or_url_parameters
    - joining_first_party_data_with_purchased_person_level_data
    - constructing_outreach_lists_from_product_usage    # §57.2 forbidden_autonomous
    - cross_context_reuse_beyond_collection_purpose
```

The analytics MCP server enforces this at the query layer, not by instructing the agent: it **refuses to return person-level rows**, applies the cohort-size floor server-side, and redacts free-text through `pii_scan` before returning it. An agent that asks for individual rows receives an error, which is the only reliable form of this control (§11.19's no-degraded-mode principle applied to data).

### 64.2 Why product-usage-driven outreach is forbidden

It is technically trivial, commercially tempting, and it is where the framework would most easily become something its own operator would be uncomfortable explaining. Purpose limitation under GDPR-class regimes, the collection-context expectation users actually hold, and the fact that consent for product analytics is not consent for sales contact all point the same way. The rule is absolute rather than tiered because the tiered version has no stable stopping point.

Legitimate paths remain open and are the ones that work anyway: in-product messaging within the product surface (channel profile `product_surface`, reviewed as code), opted-in lifecycle email with recorded consent and provenance, and human-initiated outreach where a human decides to contact a specific customer for a specific reason.

---

## Part 65 — P5: Portfolio Prioritization and the kill decision

### 65.1 Charter

**Does:** assemble the decision packet — hypothesis verdicts, outcome readings against targets, kill-criteria evaluation, opportunity backlog with refreshed evidence, capacity and attention budget — and present ranked options with explicit trade-offs. **Does not:** decide. Gate PL5 is human, permanently, on the same grounds as Gate U1/U2: problem selection and roadmap priority are human decisions (README scope statement, unchanged).

### 65.2 Kill criteria, authored at P2 and evaluated here

Kill criteria are written in the PRD before anyone is attached to the feature (§20.56.2, required field) and evaluated mechanically here. The reason for the timing is the entire mechanism: criteria authored after seeing the results are not criteria, they are rationalizations, and the framework already knows this — it is the same insight as pre-registration in §21.61.3, applied to product decisions instead of experiments.

```python
def evaluate_kill_criteria(prd: dict, evidence: dict, loops_elapsed: int) -> dict:
    """Deterministic. Fires a MANDATORY human review; never decides.
    A fired criterion cannot be dismissed silently — Gate PL5 requires a recorded decision."""
    fired = []
    for k in prd["kill_criteria"]:
        if criterion_met(k, evidence, loops_elapsed):
            fired.append({"criterion": k["text"], "reading": reading_for(k, evidence)})
    exhausted = loops_elapsed >= prd.get("max_loops", 3)
    return {
        "fired": fired,
        "loop_budget_exhausted": exhausted,
        "requires_human_decision": bool(fired) or exhausted,
        "legal_outcomes": ["kill", "pivot", "continue_with_revised_criteria"],
        # note: "continue unchanged" is NOT a legal outcome once a criterion has fired
    }
```

Three structural rules, each closing a specific escape hatch:

- **A fired criterion mandates a recorded decision.** It cannot lapse, be deferred, or be resolved by continuing to work. `continue_with_revised_criteria` is legal but requires new criteria *and* new evidence justifying the revision — which is a real option honestly used and an obvious tell when abused.
- **Loop budget.** Every PRD carries `max_loops` (default 3). Exhaustion triggers the same mandatory review even if no criterion fired. This catches the feature that never quite fails and never quite works.
- **Kills are recorded, not deleted.** The kill registry is read by P0's Novelty voter (§20.54.3), so a killed idea returning as a fresh opportunity is surfaced with its history — including the case where circumstances genuinely changed, which is the point of keeping the reasons rather than just the verdicts.

```yaml
# .mas/kill-registry.yaml — append-only
- id: PRD-2026-009
  decided_at: 2026-06-20
  outcome: kill
  reason: "activation lift 2% vs 15% target across 2 loops; no cohort showed the effect"
  evidence_refs: [EV-2026-06-19]
  hypotheses_falsified: [H-2, H-4]
  reusable_learning: "export-first onboarding does not motivate this segment; the import path might"
  revisit_if: "we acquire a segment with existing structured data"
```

`reusable_learning` and `revisit_if` are what make the registry an asset rather than a graveyard, and they feed the compounding loop as *product* priors — kept in a separate ledger from agent skills, because they are knowledge about the world rather than knowledge about how to operate the machine.

### 65.3 Hypothesis reconciliation

The existing mechanism (§13.34.3) extends without modification. Every hypothesis — PRD demand hypotheses seeded through the handoff (§20.56.3), Discovery's own, and market hypotheses from P1 — carries a falsifier and gets a verdict here. The Hypothesis-Verdict voter at P4 assigns it against the *pre-stated* falsifier; P5 records it; falsified market hypotheses invalidate the claims that depended on them, which propagates by claim ID into the backlog's evidence bundles. This is the mechanism by which a bad P1 finding gets corrected instead of persisting as institutional belief.

### 65.4 The loop-closing contract

```yaml
# handoff/p4_to_p5.yaml
cycle:
  prd_ref: PRD-2026-014
  loop_index: 2
  outcomes: [{id: O-1, target: 0.18, reading: 0.128, n: 1840, ci: [0.113, 0.144],
              method: cohort, source_type: primary_measured}]
  hypothesis_verdicts: [{id: H-1, verdict: not_supported, falsifier_met: true, evidence_ref: EV-…}]
  kill_evaluation: {fired: [...], loop_budget_exhausted: false, requires_human_decision: true}
  channel_health: {email: {complaint_rate: 0.0004, placement: 0.91},
                   community: {standing: ok, self_promo_ratio: 0.08}}
  attention_spent: {gate_pl1: 0, gate_pl2: 1, gate_pl3: 11, gate_pl5: 0}   # in approvals
  unknowns: ["…"]
```

### 65.5 Gate PL5

```
Gate PL5 (human, the outer loop's Gate U2 analogue):
  entry:  P4 evidence bundle · kill evaluation · refreshed backlog with re-probed evidence
          (stale claims per §20.53.3 are re-probed or downgraded before this gate, not during it)
  rubric: [1] Did any kill criterion fire, and what is the recorded decision?
          [2] Which hypotheses are now falsified, and which claims does that invalidate?
          [3] What did we spend, in attention and calendar, per unit of evidence gained?
          [4] What is the single largest remaining unknown, and what is the cheapest test for it?
          [5] Continue / pivot / kill / new opportunity — and what does the loser get?
  outcome: routes to P0 (new opportunity) | P1 (pivot needing fresh market work)
           | P2 (iterate: revised PRD) — never directly into the inner loop
  forbidden_autonomous: this gate
```

The routing constraint at the end is load-bearing. A P5 decision that jumped straight to Stage 4 coding would bypass the PRD, the outcomes, the instrumentation check, and the kill criteria — which is precisely the failure mode the outer loop exists to prevent, arriving through the outer loop's own back door.

---

## Part 66 — Decision record, invariants, FMEA, metrics

### 66.1 ADR summary

**ADR-U19 — The product loop is in scope, as a second loop.** Reverses the README's "pricing, GTM, launch marketing" exclusion, narrowly: the system prepares evidence and options; humans choose at Gates PL1, PL2, PL3, PL5. *Rejected:* leaving it out (the inner loop optimizes building the wrong thing efficiently); *rejected:* splicing P-stages into the eight-stage spine (§20.52.2).

**ADR-U20 — The framework never spends money.** No paid acquisition, bidding, or budget action, in any tier. *Rejected:* capped spend (§21.57.3).

**ADR-U21 — Retrieval manipulation is forbidden by construction.** GEO tactics are admissible only in their verifiability-increasing form; the manipulation branch is blocked by `geo_extractability_check`, `injection_scan`, and `spam_policy_check`, not by a style guide (§21.60.4).

**ADR-U22 — Claims are typed and machine-linted; unfalsifiable claims fail the gate.** The outer loop's answer to the absence of a compiler. `claim_lint` is to product artifacts what `ears_lint` is to specs. *Rejected:* voter-only judgment of evidence quality (violates ADR-U05's deterministic-first ordering and gives the model discretion over its own grounding).

**ADR-U23 — Agents may not generate user needs, personas, testimonials, or reviews.** Only cluster and count real artifacts with resolvable locators. Charter (§13.26.7) plus enforcement plus, in the marketing direction, the FTC's per-se treatment of fabricated reviews (§20.53.4).

**ADR-U24 — Experiments are pre-registered and hash-pinned; two-stage with FDR control; underpowered tests are not run; inconclusive results enter nothing.** Grounded in measured FDR of 18–25% at α=0.05 with ~70% true nulls and ~57% of experimenters p-hacking (§21.61.1). *Rejected:* letting the agent pick winners from a variant pool (a false-discovery generator that then poisons the compounding loop).

**ADR-U25 — Causal claims require a holdout; attribution methods are typed at the tool boundary.** Multi-touch, MMM, and platform-reported figures are inference or third-party by construction (§63.2). *Rejected:* a "best available attribution" convention (it produces confident numbers that survive into strategy decisions with no marker of their provenance).

### 66.2 New invariants (extending 14.10–14.13)

| # | Invariant | Enforced by |
|---|---|---|
| 14.14 | No P-stage artifact passes its gate with a `claim_lint` failure | `claim_lint` in the P build gate; no degraded mode |
| 14.15 | No external publish, send, or public-property modification occurs without a scoped human approval recorded against that specific artifact | Policy loader `forbidden_autonomous`; Gate PL3 scoping (§21.61.5) |
| 14.16 | No person-level data enters any agent context | `analytics_server` query-layer refusal (§64.1) |
| 14.17 | No experiment result is adopted without a matching pre-registration hash | `preregistration_lock` at analysis time |
| 14.18 | No causal claim exists in any artifact without a holdout reference | `attribution_typer` + `claim_lint` `causal_without_experiment` |
| 14.19 | No PRD passes Gate PL2 without kill criteria and instrumented (or task-generating) outcomes | `prd_lint` |
| 14.20 | A fired kill criterion cannot be closed without a recorded human decision | `evaluate_kill_criteria` + Gate PL5 entry condition |

### 66.3 FMEA additions (format per §09 Part 13; extends F-18.1–.5)

| ID | Failure mechanism | Trigger | Symptom | Blast radius | Detection | Recovery |
|---|---|---|---|---|---|---|
| F-20.1 | Fabricated market fact grounds a scope decision | Unsourced number survives to Gate PL1 | Weeks of build on an imagined segment | Whole product cycle | `claim_lint` `unsourced_number`; Gate PL1 rubric [1] | Re-probe; invalidate dependent claims by ID; kill registry entry |
| F-20.2 | Retrieval poisoning shifts the market assessment | Adversarial/optimized page enters the snapshot corpus | Competitor or demand picture systematically skewed | Strategy | `injection_scan`; source-concentration finding; Disconfirmation voter | Quarantine source; re-run P1 excluding it; add pattern fixture |
| F-21.1 | False or unsubstantiated public claim published | Draft asserts a capability absent from `claims_available` | Regulatory exposure, correction, trust damage | External, irreversible | `claim_substantiation_check`; Gate PL3 rubric [1] | Correct publicly; incident record; register the gap as a fixture |
| F-21.2 | Sending domain burned | Volume ramp or list quality violates preflight thresholds | Placement collapse across all mail, including transactional | Company-wide, weeks to recover | `deliverability_preflight`; complaint-rate guardrail | Halt sends; re-warm; the pre-existing suppression discipline is the only prevention that works |
| F-21.3 | Community account banned or brand harmed by norm violation | Self-promo ratio or subreddit rule breach | Channel lost, sometimes permanently | Channel + reputation | Self-promo ratio tracker; Norm-Fit voter; Gate PL3 rubric [3] | Human-only remediation; the profile's ratio ceiling tightens |
| F-21.4 | Scaled-content-abuse penalty | Publish-rate or template similarity crosses policy | Property-wide search visibility loss | All organic traffic | `spam_policy_check` pre-publish; visibility monitor post | Depublish; consolidate; reconsideration; cadence ceiling lowered |
| F-21.5 | False discovery adopted and compounded | Variant pool + peeking + no correction | Wrong "learning" becomes permanent prior | Every later decision | `preregistration_lock`; two-stage validation; inconclusive-enters-nothing rule | Re-run as fresh pre-registered experiment; purge the prior; annotate the ledger |
| F-22.1 | Metric definition drift | Definition changed mid-series | Apparent improvement that is an artifact | Every trend claim | `Metric-Definition` voter; `changed_at` baseline reset | Restate series with break marked; re-evaluate affected decisions |
| F-22.2 | Survivorship/vocal-minority reading | Feedback text read as population | Roadmap driven by the loudest 1% | Product direction | `Selection-Bias` voter; denominator requirement | Re-derive with denominators; seek the silent cohort explicitly |
| F-22.3 | Zombie feature — never killed, never works | Kill criteria absent, vague, or serially revised | Capacity consumed indefinitely | Team throughput | `prd_lint` requires criteria; loop budget; mandatory review | Gate PL5 decision forced; registry entry with reusable learning |
| F-22.4 | Privacy boundary breach | Person-level data reaches an agent context or an outreach list | Regulatory exposure, trust loss | Severe, external | `analytics_server` refusal; `pii_scan`; `utm_and_instrumentation_lint` no-PII-in-URLs | Incident process; purge contexts; the query-layer control is the prevention |
| F-22.5 | Attention starvation | P3 approval queue consumes the human budget | Inner-loop gates delayed; review quality degrades | Whole system | Attention-budget metric (§66.4); `attention_spent` in the P4→P5 contract | Lower cadence ceilings; batch scoping; publish less |

F-22.5 is the one most likely to actually happen, because it results from the design working: draft-and-approve at scale is an approval-queue generator. §16.38.2's human-attention budget is not advisory here — it is the constraint that sets the outer loop's real throughput, and the honest response when it binds is fewer artifacts, not faster approvals.

### 66.4 Metrics (five, mirroring the five upstream and five downstream)

| Metric | Definition | Why this one |
|---|---|---|
| **Evidence quality ratio** | Share of claims in gate-passing artifacts that are `primary_measured` or `primary_cited`, by stage | The outer loop's direct analogue of test coverage; watch the trend, not the level |
| **Hypothesis resolution rate** | Falsified-or-confirmed hypotheses ÷ total open, per loop | A loop that resolves nothing is a ratchet |
| **Decision latency** | Gate PL1/PL2/PL3/PL5 entry → recorded decision | The outer-loop version of gate latency (§16.38); the first thing to degrade under attention starvation |
| **Kill rate** | Killed-or-pivoted ÷ decided at Gate PL5 | A rate near zero means the criteria are decorative. There is no correct target — a *stated* rate near zero over many loops is the finding |
| **Attention cost per resolved hypothesis** | Human approvals + gate minutes ÷ hypotheses resolved | The efficiency measure that makes the whole loop falsifiable. If this doesn't improve over quarters, the product loop is not paying for itself and should be simplified or dropped |

The last metric is deliberately aimed at this framework. A design document that adds six stages to a system should say how it would know it made things worse, and this is the number that would say so.
