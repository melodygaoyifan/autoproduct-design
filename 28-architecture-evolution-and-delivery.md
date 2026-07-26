# 28 — Architecture Evolution & Delivery Hardening: Keeping a System Honest Over Fifty Features

Parts 81–83. Closes **gaps 4 and 5**: the machinery that stops a complicated system from eroding as features accumulate (dependency contracts, a global architecture ledger, product API versioning), and the delivery layer that was implied but never specified (environment promotion, feature-flag lifecycle, migration rehearsal). Ends with the implementation track P21–P26 covering docs 26–28. Numbering: ADR-U34/U35, invariants 14.27–14.28, FMEA F-28.x.

---

## Part 81 — Architecture evolution

### 81.1 Dependency contracts: the design becomes a fitness function

Per-feature `design.md` declares layers and module responsibilities; today nothing *enforces* them after merge, which is exactly how architecture erodes — "discipline relies on willpower; willpower fails when deadlines approach" ([modular-monolith practice](https://thearchitectsnotebook.substack.com/p/ep-122-the-modular-monolith-part)). The fix is the architecture-fitness-function pattern (Ford/Parsons/Kua, *Building Evolutionary Architectures*): dependency rules as deterministic CI checks ([pattern reference](https://aipatternbook.com/architecture-fitness-function)). New det slot `arch_contract_check`, per language lane:

- **Python:** import-linter contracts (`type = forbidden` / `layers`) — e.g., `modules.users` and `modules.orders` may not import `modules.billing` internals.
- **JS/TS:** dependency-cruiser rules — layer purity, no-circular, no-orphans, public-entry-point-only ([dependency-cruiser as fitness function](https://xebia.com/blog/taking-frontend-architecture-serious-with-dependency-cruiser/)).
- **Java/.NET (E1 lanes, §18):** ArchUnit / Spring Modulith `verify()` and NetArchTest — the same rules in the ecosystem enterprises already trust; Spring Modulith additionally auto-generates C4/PlantUML docs from the verified module structure, which becomes our architecture-diagram artifact for free ([modular monolith 2026 guide](https://dev.to/x4nent/the-modular-monolith-2026-complete-guide-spring-modulith-archunit-fitness-functions-and-lessons-878)).

Two rules make this agent-native rather than bolted-on. First, **the contracts are generated from `design.md`'s declared layers** at spec time — the spec is the source of truth; the checker is its compiled form; editing the checker without an SCR is drift by definition. Second, **the check runs inside the coding MAS's verify slot, not only in CI** — an agent that sees "layer violation" in its own feedback loop fixes it in-iteration; a check that only fires post-PR teaches the agent nothing ([the agentic-governance point, ibid.](https://aipatternbook.com/architecture-fitness-function)).

**Brownfield adoption** uses the checkpoint pattern proven at scale in Shopify's pack system: existing violations are snapshotted into a `deprecated_references` baseline and *whittled down* — new violations fail immediately, old ones are debt with a visible count ([Shopify packs write-up, ibid.](https://dev.to/x4nent/the-modular-monolith-2026-complete-guide-spring-modulith-archunit-fitness-functions-and-lessons-878)). This slots directly into the substrate ladder: a legacy estate adopts the checker on day one at S1 without a big-bang refactor, and the debt counter joins the `debt_server` metrics.

### 81.2 The global architecture ledger — ADR-U34

Per-feature `design.md` files answer "what did feature N intend"; nothing today answers "what is the system now." Two accumulating artifacts fix that:

```yaml
# .mas/deps.yaml — the allowed module graph (compiled into arch_contract_check)
modules:
  users:    {public: [users.api], may_import: [shared]}
  orders:   {public: [orders.api], may_import: [users.api, shared]}
  billing:  {public: [billing.api], may_import: [orders.api, shared], owner: "@melody"}
```

plus `.mas/architecture.md` — the living system document (layers, data flows, async surfaces, stable interfaces — the Phase-2/3 artifact the source methodology always required, §12.23.8, now with a maintenance story). **ADR-U34: mutations to the module graph are SCR-class.** Adding a module, widening `may_import`, or moving a public boundary goes through the same human-approved change channel as a spec mutation — because it *is* a spec mutation, of the largest spec. Narrowing (removing an allowed edge that nothing uses) is a normal PR. *Rejected:* letting the coding stage update `deps.yaml` to make its own build pass (that is the erosion mechanism with extra steps); a wiki architecture page (unenforced documents describe the past).

### 81.3 The built product's own API gets the §74.2 treatment

Doc 74.2 defined SemVer over an enumerated contract surface for the *platform*; the same pattern turns outward: workspaces with external consumers declare `api_surface` in the spec (routes/events/schemas), `ESCALATE_CONTRACT_BREAK` (already in §13) keys off diffs to that surface, and a deprecation window (≥1 minor version, loud warnings) becomes a deploy-review check rather than a courtesy. Streaming topics' compatibility modes (doc 27 §80.1) are the same policy in event form — one versioning discipline, three surfaces (HTTP, events, schemas).

---

## Part 82 — Delivery hardening

### 82.1 Environments become an artifact — `.mas/environments.yaml`

```yaml
environments:
  - {name: dev,     parity: low,  promotes_to: staging}
  - {name: staging, parity: prod_mirror, promotes_to: prod, gates: [perf_regression]}
  - {name: prod,    parity: prod, gates: [gate5_deploy_review]}
```

Deterministic checks: the promotion graph is a DAG ending at prod; every gate named exists; doc 26's `perf_regression`/`perf_soak` slots may only cite runs from a `prod_mirror` environment (closing ADR-U30 precondition 4); a deploy targeting an environment out of promotion order is a Gate 5 finding. This is deliberately minimal — an ordered list with gates — because the promotion *model* was the gap, not promotion *tooling*.

### 82.2 ADR-U35 — Feature flags are registered assets with owners and expiry

**Decision.** Every flag lives in `.mas/flags.yaml` at creation: `{name, category, owner, created, expiry, final_state, removal_trigger}` with category ∈ `release | experiment | migration | ops_kill_switch | compat | permission` — the category determines lifecycle expectations, and only `ops_kill_switch`/`permission` may be long-lived ([flag-cleanup checklist pattern](https://www.momentslog.com/development/feature-flag-cleanup-checklist-how-to-prevent-temporary-toggles-from-becoming-production-risk-2)). Deterministic `flag_lint`: a flag referenced in code but absent from the registry = finding; past `expiry` = finding escalating to Gate 2 block after a grace week; **removal is scheduled as a real task at creation time**, because ~80% of flag removals touch more than one file — it is engineering work, not a chore ([2026 rollout-strategies playbook](https://www.digitalapplied.com/blog/feature-flag-rollout-strategies-2026-engineering-playbook)). Health telemetry follows the converged vendor lifecycle models (LaunchDarkly's six stages, 90–120-day healthy time-to-archive; Unleash's "stuck in Cleanup" as the debt indicator, ibid.): time-in-state joins the `debt_server` metrics. API preference: OpenFeature, to avoid vendor coupling in generated code ([2026 practice](https://zylos.ai/research/2026-02-12-feature-flags)). Test machinery: critical-journey tests run under declared flag *combinations*, not just all-on/all-off (ibid.) — the combination list lives beside the registry. *Rejected:* unregistered "quick" flags (they are the stale flags of six months from now); flag state as a deploy-review afterthought (flags interact with canary logic; Gate 5 sees the registry).

### 82.3 Migration rehearsal — the deterministic pre-signal for `ESCALATE_MIGRATION_DESTRUCTIVE`

§09.11 already escalates destructive migrations; what it lacked was evidence *before* the escalate. The delta: migrations follow **expand–migrate–contract** as the reviewed default (contract steps are separate, later PRs by construction), and `migration_rehearsal` runs every migration against a fixture-DB snapshot pre-review, recording: applied cleanly y/n, lock profile (longest table lock), row-scan estimate vs table size, and **reversibility** — the down-migration runs and round-trips to a byte-identical schema dump. A destructive change with a clean rehearsal record escalates with evidence attached; one *without* a rehearsal record doesn't reach review at all. At S0 the fixture DB is SQLite/pg-in-Docker from the hermetic suite; the rehearsal's fidelity rises with the substrate rung, and says so on the record.

---

## Part 83 — Implementation track P21–P26 and the scorecard flip

Extends doc 23's track; same buffer and change-control policy. **P21:** EARS perf grammar + `quantifier_scan` extension + k6 smoke slot. **P22:** `perf_regression`/`soak`/`spike` + VALID-run typing + `capacity.yaml` + seeded perf-defect manifest (lane lands PROVISIONAL). **P23:** realtime delta — `det_sim_scan`, replay-identity fixtures, netem profiles, WS spike scenario. **P24:** streaming delta — `stream_contract_check`, contract file, backpressure probe, replay verification. **P25:** `arch_contract_check` per lane + `deps.yaml`/ledger + brownfield checkpoint mode. **P26:** `environments.yaml` + `flag_lint` + `migration_rehearsal`; re-run the capability evaluation and publish the diff.

**Implementation status (2026-07-26, ai-product-autopilot v0.23.0):** the
deterministic core of P21–P26 shipped as `src/autoproduct/lanes/` — perf
grammar + VALID-run typing + capacity arithmetic, `det_sim_scan` + the
three replay checks, `stream_contract_check` (with 'default' lexically
rejected), `deps.yaml` + `arch_contract_check` + checkpoint mode,
`environments.yaml` + `flag_lint` + `migration_rehearsal` — all
fixture-tested. Pending, per the lane rules themselves: k6/netem/registry
execution wrappers (availability-gated) and the seeded perf-defect
calibration run that converts the lane from PROVISIONAL.

What the evaluation table flips to, honestly labeled: high-traffic backends ❌→**review-level ✅, empirical after P22 calibration**; realtime/multiplayer ❌→✅ (design), with `replay_identity` as the falsifiable core; streaming D→✅ (design); architecture evolution B+→A− (the remaining minus: fitness functions can't check what layers *should* exist, only that declared ones hold — that judgment stays human); delivery hardening ❌ rows → ✅. Every ✅ remains a design-coverage grade until its seeded manifest or fixture run converts it, per the standing rule.

| Invariant | Statement | Enforced by |
|---|---|---|
| 14.27 | The module graph changes only through the SCR-class channel; the checker is compiled from the graph, never hand-edited | ADR-U34; `arch_contract_check` provenance header |
| 14.28 | No unregistered feature flag; no migration reaches review without a rehearsal record | `flag_lint`; `migration_rehearsal` as Gate 5 precondition |

**FMEA:** **F-28.1** checkpoint baseline becomes a permanent excuse (debt count never falls) → the count is a `debt_server` metric with a trend alarm; a flat 90-day trend is a compounding-loop finding (M×H). **F-28.2** rehearsal fixture DB diverges from prod schema → rehearsal starts by diffing snapshot schema against migrations-applied-to-date; mismatch = INVALID rehearsal (M×M). **F-28.3** flag registry and flag platform disagree → nightly reconciliation, same pattern as F-27.4 (M×M).

---
*Cross-references: §09.11 (Gate 5), §12.23.8 (architecture artifact), §13 (ESCALATE_CONTRACT_BREAK, SCR), §18 (substrate rungs, debt_server), §74.2 (SemVer pattern), docs 26–27. Research index rows land in doc 15 §6.*
