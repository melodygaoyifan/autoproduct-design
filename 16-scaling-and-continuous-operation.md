# 16 — Scaling, Continuous Operation, and the Technique Radar

Parts 38–40. This document answers three questions the rest of the set deliberately deferred: how the system scales beyond one feature at a time, what the bounded outer loop of continuous operation looks like, and which post-publication techniques earn adoption. It is delta-shaped: nothing in 08–15 is modified; four ADRs and one metric are added. (Disambiguation: inside docs 09–10, citations of the form `§15.x`–`§21.x` refer to **Parts 15–21 of `11-ultimate-architecture.md`**, which predate documents 15–17. References to the newer documents always carry their Part numbers: `§16.38`–`§16.40` for this document, `§17.41`–`§17.45` for doc 17; doc 15 is cited as `doc 15 §n`.)

---

## Part 38 — Scaling model

### 38.1 Three axes, two already covered

**Depth** (how hard one change is examined) is the mode router — fast/standard/deep (§08.3.5, §12.24.3). **Width within a feature** is lanes: parallel worktrees proven file-disjoint at Gate U2 (§13.27.3), capped by `lanes_max`. This part covers the third axis: **width across features** — N features traversing the eight stages concurrently.

### 38.2 Concurrency model

The runtime already supports it structurally — one graph, per-feature checkpointer threads, Celery workers (§09.5, ADR-005). What was unspecified, and is specified here:

```yaml
# .mas/operations-policy.yaml (new; loaded like authoring-policy)
wip_limits:                    # per-stage feature count, systemwide
  discovery: 2
  planning: 2
  spec: 3
  coding_features: 2           # features with active coding lanes
  coding_lanes_total: 4        # ≤ Σ lanes across all features (worker sizing anchor)
  review_queue: 6              # PRs awaiting Stage-5 verdicts
gates:
  human_queue_limit: 5         # open gate decisions per approver → shed rule §39.3
  latency_slo_hours: 24        # business-hours median, gate-open → human decision
merge:
  queue: serial                # one merge at a time into main; rebase-and-retest on entry
  ci_concurrency_max: 3        # thundering-herd cap (F-16.1)
shared_files:
  registry: .mas/hot-files.yaml   # global serialization-lane registry across features
```

Rules that make cross-feature width safe:

1. **Global hot-file registry.** The per-feature serialization lane (§13.27.2) generalizes: `.mas/hot-files.yaml` lists globs (schemas, route tables, lockfiles, generated files) that only one lane *system-wide* may hold at a time. `lane_check` consults it across all active plans, not just the current feature's.
2. **Serial merge queue.** Lanes parallelize work; merges serialize truth. Every PR entering the queue rebases onto current main and re-runs the fast suite before merging — the cross-feature analog of reverse-merge safety (§09.7.2.8). Never-auto-merge is unchanged; the queue orders human-approved merges, it does not approve.
3. **CI as a budgeted resource.** `ci_concurrency_max` caps simultaneous full-suite runs; excess queues. Without the cap, five agents finishing simultaneously produce the thundering herd of F-16.1 — CI wait time silently becomes the dominant latency and agents "fix" it by running fewer tests.
4. **Worker sizing anchor.** Celery worker count ≥ `coding_lanes_total` + active voter panels × their parallelism; the §09.9 cost meter already reports per-stage wall time, which is the tuning signal.

### 38.3 What actually limits scale (the honest version)

Token throughput and worker count are purchasable. The binding constraints, in order: **(1) human gate attention** — every U1/U2/U3 crossing and every ESCALATE_* serializes on a person (Part 39); **(2) merge-queue throughput** on hot files — if every feature touches the same schema, lanes buy nothing (the registry makes this visible early, at plan time); **(3) correlated error across features** — one bad shared skill update degrades every panel at once (F-16.2; the benchmark-gated rollback in §09.8.4 is the containment). Recent theory on budgeted multi-agent synergy — predicting when adding agents improves, saturates, or collapses outcomes based on context limits, communication fidelity, and shared-error correlation — matches this ordering and moves off the watch list into design stance: **scale width until metric 6 (gate latency) or metric 4 (upstream-attributable findings) degrades, then stop adding features, not gates.** Cost scales near-linearly with feature count under the existing per-stage budgets (§13.33.3); the WIP limits, not budgets, are the intended throttle.

---

## Part 39 — Continuous operation: the bounded outer loop

### 39.1 The loop

```
while backlog is non-empty:
    if wip(stage) < wip_limits[stage] and human_queue < human_queue_limit:
        pull next approved item into its stage          # priority: human-ordered backlog
    advance all in-flight features per their subgraphs  # gates interrupt as designed
    weekly: compounding PR (STAR-L + metrics + GEPA proposals §40.1) — human-reviewed
```

Every inner loop is already bounded (3 attempts, 3 cycles, circuit breakers, `unattended_max_tasks`); this outer loop is bounded by **WIP limits and the human-attention shed rule** — not by trust in agents. The stance, stated once and citable: **bounded loops, unbounded learning** (ADR-U08). The system runs continuously; it never runs unattended *through a gate*. This is the design's reading of the field's own numbers — practitioners fully delegate only 0–20% of tasks (Anthropic 2026 trends report) — built into structure rather than left to discipline.

### 39.2 Metric 6 — gate latency & human queue depth

| # | Metric | Definition | Source | Target | What "bad" looks like |
|---|---|---|---|---|---|
| 6 | Gate latency / queue depth | median business-hours from gate-open to human decision; open gate decisions per approver | HITL Issue timestamps (§09.8.8 health check extended) | ≤ 24h median; ≤ 5 open/approver | Rising latency with flat queue = approver overload → lower WIP. Deep queue with fast latency = rubber-stamping → the gates' small-artifact design (§15 residuals) is failing; audit before scaling |

Little's Law makes the planning arithmetic explicit: sustainable feature throughput ≈ (approver decisions/day × approvers) ÷ (gate decisions per feature, ≈4–6). Scaling agents without scaling this number converts compute into a pile of stale escalations.

### 39.3 Shed rule and operator cadence

When `human_queue > human_queue_limit`: the dispatcher stops pulling new backlog items (in-flight work continues to its next gate and waits). Recovery is a human choosing — decide, delegate an approver, or lower WIP — never the system approving for them. Operator cadence that keeps the loop healthy: a daily 15-minute gate sweep (the Issues are designed to be decidable in minutes — small artifacts, evidence attached) and the existing weekly compounding-PR review. If the daily sweep routinely exceeds 15 minutes, that is metric 6 speaking: reduce WIP or split approver duty; do not extend the sweep.

### 39.4 Rollout order

Adopt in this order, each gated on the previous being boring: (1) two features concurrent, shared-file registry live; (2) merge queue + CI cap; (3) metric 6 dashboards for two weeks; (4) raise WIP by one and re-observe; (5) only then consider `unattended_max_tasks > 0` for the qualifying task classes (§13.29.9). Skipping to (5) first is the failure mode SusVibes catalogs (§15 index).

---

## Part 40 — Technique radar (2026-H2)

Adoption bar: verified source, load-bearing value, delta-shaped fit. Everything below is indexed in doc 15 §6.

### 40.1 ADOPTED — GEPA as the compounding loop's proposal engine

[GEPA (ICLR 2026 Oral, arXiv:2507.19457)](https://arxiv.org/abs/2507.19457) evolves prompts via natural-language reflection over execution traces with Pareto candidate selection — outperforming GRPO-style RL by ~6pp average (up to ~19pp) with up to 35× fewer rollouts, and MIPROv2 by >10pp. [MAS-PromptBench (arXiv:2606.23664)](https://arxiv.org/abs/2606.23664) extends it to multi-agent systems by optimizing **one agent's prompt at a time** while holding others fixed — exactly this framework's single-writer discipline applied to self-improvement. Production use is documented (Decagon, 2026-03).

The fit is unusually clean because the framework already has GEPA's three inputs: a metric μ (**fixture pass rate** + per-voter precision from production labels), rich textual feedback μf (**verify-pass outcomes, STAR-L signals, Leader calibration notes** — far richer than a scalar), and a governance channel (**the weekly human-reviewed compounding PR**). Integration contract:

```yaml
# .mas/gepa.yaml
enabled: false                 # start manual; enable after two clean weekly cycles
targets: [voter_skills, writer_templates]     # never policies, never gates, never code
metric: fixture_pass_rate + production_precision
feedback: [verify_results, star_l, leader_notes]
budget_rollouts_weekly: 40
holdout_fixture_fraction: 0.25   # F-16.4 Goodhart guard: optimizer never sees these
proposal_channel: compounding_pr # human review + benchmark rollback unchanged (§09.8.4)
one_agent_per_cycle: true        # MAS-PromptBench discipline
```

GEPA proposes; the existing loop disposes. It replaces nothing — it makes the "propose targeted fixes" step of §09.8.4 systematic instead of artisanal. **ADR-U11.**

### 40.2 ADOPTED (posture) — CaMeL-grade injection defense, staged

[CaMeL (DeepMind, arXiv:2503.18813)](https://arxiv.org/abs/2503.18813) defeats prompt injection *by design*: control/data-flow separation (a privileged LLM plans from trusted input; a quarantined LLM touches untrusted data without tools) plus value-level capabilities enforced at every tool call — solving most of AgentDojo with provable security, no model changes. The multi-agent security survey ([arXiv:2505.02077](https://arxiv.org/abs/2505.02077)) treats it as the reference architecture.

Honest self-assessment: this framework **already implements the dual-LLM/quarantine half** — the Discovery two-invocation flow (§26.2) is precisely privileged/quarantined separation, and the taint lockout (§13.31.2) + per-tool RBAC (§11.17) are session-granularity capabilities. What CaMeL adds beyond current design is **value-level** provenance (capabilities attached to each datum, not each session). Adopted as the documented upgrade path, triggered when either condition arrives: research output needs to flow into L1+ workflows within one run, or untrusted inputs expand beyond Discovery (e.g., customer-filed issues feeding Maintenance directly). Until then, session-granularity is sufficient and simpler — complexity deferred is not security deferred, because the coarse control strictly contains the fine one.

### 40.3 ADOPTED — voter model cascades with a heterogeneity floor

At cross-feature scale, voter cost dominates (§13.33.3 × N features). Cascading is the standard lever: a cheap-family first pass per voter; escalate to the premium family only when the cheap pass emits a finding, reports low confidence, or the panel disagrees. Guardrails that keep it from quietly gutting the design: **counted votes must still span ≥2 model families** (`critics_min_distinct_families` applies to the escalated set, not the cheap set); fixture gates run **per model configuration** (a voter skill passing on the premium family is not certified on the cheap one); and cascade hit-rates join the weekly metrics so silent quality drift is visible. Routing research (e.g., CASTER-style structural routers) is watch-listed for the router itself; the cascade needs no learned router to pay for itself. **ADR-U10.**

### 40.4 ADOPTED (operations) — sandbox isolation for execution surfaces

The two places agent-driven execution touches real compute — the implementer's worktree hooks and `test_exec` — move under OS-level isolation at scale (container minimum; microVM-class isolation where infrastructure allows), matching the 2025-26 practitioner consensus for agent runtimes (sandboxed-execution defaults in major agent harnesses; dual-use posture per the 2026 trends report, trend 8). This changes deployment, not design: the MCP risk ladder and mounts (§11.17) are unchanged; the sandbox is the floor they stand on. One SECURITY.md line added.

### 40.5 EVALUATED AND REJECTED (with reasons, per the calibration rule)

- **A2A/ACP peer-to-peer agent protocols.** Interop standards for agent-to-agent messaging solve a problem this architecture deliberately does not have: voters never talk to each other (P3), writers are single, and all coordination is deterministic dispatch over shared typed state. Adopting peer messaging would reintroduce the failure surface MAST attributes ~37% of failures to. MCP remains the only transport. **ADR-U09.** *Re-examine if* the system must federate with external agent products as peers rather than as tools.
- **Structured-debate variants (incl. confidence-gated debate for small models).** Niche gains for SLM code generation do not overturn the NeurIPS-scale evidence for independent voting in this system's regime. Stays rejected; stays on the watch list only as literature to track.
- **RL/GRPO fine-tuning of agents.** GEPA reaches comparable-or-better adaptation with ~35× fewer rollouts *inside* the existing governance channel; fine-tuned private weights would also break the heterogeneity audit (family identity becomes unverifiable). Rejected for this system.
- **Full CaMeL interpreter today.** See §40.2 — staged, not rejected; deferred with explicit triggers.
- **"Long context solves context assembly."** 1M-token windows do not replace manifests: the July-2026 field signal is that long context is necessary-not-sufficient without tool discipline, navigation, and acceptance criteria — and the ~39% multi-turn degradation result is about accumulation, not capacity. The manifest + fresh-context protocol stands.

### 40.6 Watch list (updated; supersedes the doc 15 §6 list)

Learned routing for cascades (CASTER-class) · confidence-gated debate literature · value-level capability tooling maturing around CaMeL (Foerster et al. 2026 line) · spec-registry ecosystems (Tessl) as an alternative grounding source for `repo_capability_probe` · **resolved and removed:** budgeted-MAS phase-transition theory (→ §38.3 design stance) · OWASP LLM Top-10 mapping (→ SECURITY.md, shipped).

---

## FMEA additions (format per §09 Part 13)

**F-16.1 CI thundering herd.** *Trigger:* N lanes finish together. *Symptom:* CI queue latency dominates; agents time out or shrink test scope. *Detection:* CI wait time in the weekly metrics; build-gate duration trend. *Recovery:* `ci_concurrency_max` throttle (queue, never skip); worker/back-pressure sizing. *Mitigation:* the cap ships on by default.

**F-16.2 Correlated cross-feature degradation via shared assets.** *Trigger:* a bad skill/template/fixture update lands. *Symptom:* action-rate or first-pass-gate-rate drops across all features simultaneously. *Detection:* metrics are per-week and per-voter — a synchronized drop fingerprints a shared-asset cause. *Recovery:* benchmark-gated rollback (§09.8.4.3) reverts the compounding PR; GEPA proposals inherit the same rollback. *Mitigation:* one-agent-per-cycle change discipline (§40.1) keeps blast radius attributable.

**F-16.3 Human-attention collapse.** *Trigger:* WIP raised past approver capacity. *Symptom:* metric 6 latency climbs, then rubber-stamping (deep queue, suspiciously fast decisions). *Detection:* metric 6 both components; §09.8.8 health check. *Recovery:* shed rule halts intake; explicit human choice to decide/delegate/lower WIP. *Mitigation:* Little's-Law sizing in §39.2 makes capacity arithmetic, not vibes.

**F-16.4 Optimizer Goodharting the fixtures.** *Trigger:* GEPA over-fits skills to the fixture suite. *Symptom:* fixture pass rises while production precision/action rate falls. *Detection:* held-out fixture split (never shown to the optimizer) + production metrics in the same weekly view. *Recovery:* reject/rollback the proposal; promote the divergence case into the held-out set. *Mitigation:* `holdout_fixture_fraction` ships non-zero and non-optional.

---

## Architecture decision records

**ADR-U08 — WIP-limited continuous operation; unbounded autonomy is a non-goal.** *Accepted.* The outer loop runs indefinitely under WIP limits and a human-attention shed rule; no configuration removes gates from the path. Grounds: delegation reality (0–20% full delegation, Anthropic 2026), sustained-autonomy risk taxonomy (SusVibes), and the arithmetic of §39.2 — throughput is bounded by decisions, so the design budgets decisions instead of pretending them away. *Rejected:* auto-approve-on-timeout (converts latency into silent risk); autonomous backlog selection (problem selection is `forbidden_autonomous`). *Re-examine:* never for the gate principle; WIP numbers are tunable by metric 6.

**ADR-U09 — MCP-only transport; no A2A/ACP peer messaging.** *Accepted.* §40.5 first bullet. Coordination is dispatch over typed state; peer messaging reintroduces the coordination-failure surface by construction.

**ADR-U10 — Model cascades permitted, heterogeneity floor mandatory.** *Accepted.* Cost lever with three guardrails: family floor on counted votes, per-configuration fixture certification, cascade metrics in the weekly view. *Rejected:* single-cheap-family panels (recreates same-family blindness, §08.2.2.3).

**ADR-U11 — GEPA inside the compounding loop; proposals only.** *Accepted.* Targets are voter skills and writer templates only — never policies, gates, or code; held-out fixtures guard Goodhart; one agent per cycle; human PR review and benchmark rollback unchanged. The optimizer is a stronger *proposer* for a loop whose *disposer* was already designed. *Rejected:* GEPA-direct-to-production (removes the human channel that makes learning auditable); optimizing gate thresholds (thresholds are policy, and policy is not a fitness surface).
