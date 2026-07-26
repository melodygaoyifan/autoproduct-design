# 18 — Traditional-Industry Gap Closure Plan

Parts 46–50. **Status: ACCEPTED (2026-07-25); implementation plan is doc 19.** This document plans the work to close the gaps that block adoption at a traditional-industry enterprise (working example: a Tyson-class food/CPG company — SAP-centric ERP estate, supply-chain integration middleware, data/ML pipelines for yield and demand forecasting, plant-floor OT, and a smaller modern digital-product organization). The README scope and reading-order updates landed with acceptance per the change-control protocol (§10 Part 11).

Citation calibration as everywhere: no unverified sources; tool names are cited as tools, industry-consensus claims are phrased as such. Cost/duration numbers are engineering defaults — run the Phase-0 calibration before trusting them (same disclaimer as the README).

---

## Part 46 — The three gaps, and the closure strategy

The applicability assessment against the Tyson-class profile found the eight-stage spine and bounded-autonomy posture transfer well (the gate philosophy *matches* regulated change-control culture), but three structural gaps block adoption beyond the modern digital teams:

| # | Gap | Where the docs say so |
|---|---|---|
| G1 | **Domain coverage.** Shipped profiles are web/mini-program/mobile/game (doc 17). The Tyson-class workload majority — data/ML pipelines, ERP/COTS configuration, embedded/OT — is marked "explicitly future" (§17 coverage table) or unmentioned (ERP). | §17 查漏补缺 table |
| G2 | **Substrate prerequisites.** Every deterministic gate presumes git/PR flow, CI/CD, observability (Sentry/Datadog/PagerDuty-class), progressive delivery, and Python 3.11+ as the only first-class language. Traditional-enterprise teams are often ticket-driven, Java/.NET/ABAP, quarterly-release. | §09 tool registry; README conventions & out-of-scope list |
| G3 | **Enterprise hardening.** Multi-tenancy, SSO/SAML, attestation ledger, authorization fabric, SOC 2 posture are explicitly out of scope (§08.96) — but they are procurement entry requirements at this class of company. | §08 out-of-scope list |

**Closure strategy — three tracks, one principle.** The principle is ADR-U12 unchanged: *extend by profile and policy, never fork the spine.* G1 closes with two new domain profiles (Part 48). G2 closes with a substrate-adoption ladder plus cross-language promotion (Part 47). G3 closes with an enterprise-hardening track that reverses one scope decision explicitly, by ADR (Part 49). Sequencing and the pilot shape are Part 50.

One reframe drives the sequencing: **the upstream stages are the wedge.** Discovery, Planning, and Specification consume and emit markdown/YAML artifacts and human gate decisions — they need almost no substrate. A team with no CI and no PR flow can still run brief → plan → spec with full voter/verify/leader machinery and get value on day one. Downstream stages light up as the substrate ladder is climbed. This inverts the usual "modernize first, then adopt tooling" adoption failure: the system's upstream discipline becomes the *reason* to build the substrate, not a casualty of its absence.

---

## Part 47 — Track 1: Substrate readiness and cross-language promotion (closes G2)

### 47.1 The substrate ladder

A new `.mas/substrate-profile.yaml` (loaded like `domain-profile.yaml`, validated the same way) declares what the adopting team actually has; the policy loader activates only the stages whose substrate floor is met, and reports the gap as a structured readiness assessment rather than failing obscurely at runtime.

```yaml
# .mas/substrate-profile.yaml
substrate:
  vcs: git | none                 # PR flow implies git
  pr_flow: true | false
  ci: true | false                # machine-runnable build+test on every change
  observability: [sentry, datadog, pagerduty, none]
  progressive_delivery: true | false
  languages: [python, java, csharp, abap, ...]
```

| Rung | Substrate present | Stages active | What the team gets |
|---|---|---|---|
| S0 | nothing (artifacts + humans) | Discovery, Planning, Specification | briefs, task DAGs, EARS specs, all upstream gates — full value, zero infra |
| S1 | git + PR flow | + Code Review, Coding | the downstream core |
| S2 | + CI | + Test (mutation, harness gates) | "tests pass" becomes machine-meaningful |
| S3 | + observability | + Maintenance | incident loop, hypothesis reconciliation |
| S4 | + progressive delivery | + Deployment Review (full) | canary machinery; below S4, Deploy Review runs in config-lint-only degraded mode |

Rules: a stage below its floor is **inactive, never silently degraded** — except Deploy Review's named lint-only mode, which is explicit in the verdict banner. Gate preconditions never weaken (same floor-not-default rule as §41.1). The readiness assessment is itself a deliverable: it is the modernization roadmap the adopting team's platform organization executes, with each rung unlocking named system value. **ADR-U15.**

### 47.2 Cross-language promotion: Java/.NET to first-class

The README lists cross-language first-class support as out of scope. For this adopter class that exclusion is fatal — the estate is Java/.NET (and ABAP, handled in Part 48.2). Promotion is deliberately narrow: **first-class means the det_tools row and test-harness templating exist and are fixture-gated; it does not mean rewriting any prompt or voter** — voters are language-agnostic by design (they read diffs and findings, not ASTs).

| det_tools slot (Python today) | Java | .NET |
|---|---|---|
| lint/type (ruff, mypy) | Checkstyle + Error Prone / SpotBugs | Roslyn analyzers (`dotnet build` warnings-as-errors) |
| tests + coverage (pytest) | JUnit + JaCoCo | xUnit + Coverlet |
| mutation (mutmut-class) | PIT | Stryker.NET |
| SAST | Semgrep (multi-language rulesets already) | Semgrep |
| dependency/supply-chain | OWASP Dependency-Check / same registry checks | same |

Acceptance bar per language (the fixture-gate discipline of §11 applied to toolchains): the language's det_tools suite runs green on a seeded reference repo containing planted defects, and each planted defect class is caught by the intended tool — a toolchain doesn't register without passing its fixtures, exactly like an agent. Parity is measured, not assumed: the seeded-defect catch-rate per language is a published number, and a language whose catch-rate lags Python's by more than the calibrated margin is labeled *provisional* in the verdict banner (mitigates F-18.4). **ADR-U16.**

### 47.3 Gate R — regulated change control as a first-class external gate

Cheap win, high leverage: §41.3's Gate P1 (external platform review) generalizes verbatim to the change-advisory boards, SOX ITGC change controls, and food-safety/quality-system reviews (HACCP-adjacent validation, FSMA-driven records discipline) that gate releases at this adopter class. Same mechanics: entry = release candidate + preflight checklist 100% green; latency budgeted in the plan as a train; rejection reasons are structured input that become preflight fixtures where mechanizable and compounding-loop entries where not; the submission/approval action is human-only. The preflight checklist starts as the mechanizable shadow of the CAB's checklist (change record completeness, rollback plan present, affected-system inventory, evidence bundle attached) and sharpens with every rejection. No new machinery — a gate-class alias plus a starter checklist template.

---

## Part 48 — Track 2: New domain profiles (closes G1)

Both profiles obey §41.1: add checks/voters/vocabulary/gates, never weaken the core. Both get the full doc-13-style treatment (roster, skills, fixtures, verdict taxonomy, FMEA) when built; this part fixes their shape and acceptance bars.

### 48.1 Data/ML pipeline profile

Doc 17 already names the machine-checkable core: **data contracts + eval sets**. Filling it in:

| det_tools additions | What it catches |
|---|---|
| data-contract check (schema + constraint assertions at pipeline boundaries; dbt tests / Great Expectations-class suites) | breaking schema changes, constraint violations, silent null floods |
| DAG lint + dry-run compile (dbt compile, Airflow/Dagster DAG import test) | broken dependencies, config errors before any data moves |
| eval-set regression gate (frozen labeled sets per model; score deltas vs pinned baseline) | model/prompt/feature changes that regress quality — the ML analogue of the mutation gate |
| lineage/impact check | which downstream consumers a change touches; feeds blast-radius into Planning |
| backfill/idempotency check (re-run on fixture slice → identical output hash) | the reprocessing bugs that surface as month-old silent corruption |

Voter deltas: **DataContract voter** (semantic breaks that pass schema checks — unit changes, meaning drift, timezone handling), **BackfillSafety voter** (idempotency, late-arriving data, partition boundary hazards), **DriftAndCost voter** (unbounded scans, missing partition filters, warehouse-cost blowups — flags mechanism with the query plan, never restates the dry-run number). NFR vocabulary: freshness SLA (minutes/hours at p95), row-count tolerance bands, eval metric floors per model, cost budget per pipeline-run. An AC citing "accurate" or "fresh" dies at quantifier_scan, same as "fast" (§42.3).

The hypothesis ledger applies directly: a forecasting model's assumed lift is a Discovery hypothesis that reconciles against realized accuracy through the §13.34.3 machinery — this is the profile where the product loop's close is most literal.

Gates: eval-regression is a build-gate fail; **schema-breaking contract changes are Gate-R class** (human sign-off with the consumer-impact list attached), and `forbidden_autonomous_add: [production_backfill, training_data_mutation]`.

### 48.2 ERP-extension profile (SAP-class)

Scope discipline first, because this is where the profile lives or dies: the profile covers **custom extension code and integrations** — ABAP/RAP developments, BTP-class side-by-side extensions, IDoc/API integration flows, and transport-managed custom objects. It explicitly does **not** cover vanilla module configuration/customizing, which is consultant work with no code artifact for voters to read (mitigates F-18.2). The honest value ceiling: lower than greenfield services, still real — custom ABAP is long-lived, weakly tested, and change-reviewed by committee, which is precisely the environment where deterministic gates plus verified findings displace meeting time.

| det_tools additions | What it catches |
|---|---|
| ABAP static analysis (abaplint; ATC where licensed) | the lint/type slot for the ABAP lane |
| transport dependency & sequence check | the missing-object / wrong-order transport failures that dominate ERP release incidents |
| integration-contract check (IDoc/API schemas vs consumer registry) | breaking a downstream WMS/MES/plant system silently |
| custom-code regression suite gate (whatever harness the team has — the substrate ladder applies within the profile) | S2-rung equivalent for the ERP lane |

Voter deltas: **IntegrationBlastRadius voter** (which plants/warehouses/partners a change reaches — feeds Planning's risk-sequencing), **ComplianceControl voter** (segregation-of-duties touchpoints, audit-relevant object changes flagged for the Gate-R evidence bundle). Release cadence is a train behind Gate R (§47.3) — the plan's `deploy_impact` gains `cab_review: true` tasks exactly as mini-programs gained `platform_review: true` (§43.2). `forbidden_autonomous_add: [transport_release, production_client_change]`.

### 48.3 Embedded/OT — deferred, with explicit triggers and a hard ceiling

Stays out-of-scope-with-a-path (unchanged from §17). Deferral triggers for revisiting: a HIL (hardware-in-the-loop) test rig the system can drive deterministically, and a pilot partner with a safety case owner. Hard ceiling regardless of trigger: anything reaching plant-floor control (SCADA/PLC) is **advisory-only forever** — findings and evidence bundles for human engineers; no write-path tool below L0 read-only ever registers for OT targets. Safety-instrumented systems are not a domain profile problem; they are a "the ceiling is the product" problem. **ADR-U18.**

---

## Part 49 — Track 3: Enterprise hardening (closes G3)

This track reverses one explicit scope decision (§08.96) and must say so: **enterprise deployability moves in scope; multi-tenant SaaS stays out.** The system remains a single-org deployment — what changes is that the single org can now be a 100,000-employee regulated public company. **ADR-U17.**

Work items, in dependency order:

1. **AuthN/AuthZ on human surfaces.** SSO (SAML/OIDC) on every HITL gate UI and escalation surface; gate-approval authority mapped to IdP groups. The trust-tier ceilings (§13.32) gain a *who* dimension: which roles may approve which gate classes (a spec scope-unlock approver ≠ a production-action approver).
2. **Attestation ledger.** Every gate decision, verdict, override, and forbidden-action denial already exists as structured state (§09); the ledger work is append-only signed export with retention policy — the SOX ITGC evidence bundle becomes a query, not a quarterly archaeology project. This is the feature that makes Gate R (§47.3) cheap to pass repeatedly.
3. **Deployment envelope.** Self-hosted/VPC reference deployment; model access via the org's approved enterprise endpoints (Bedrock/Vertex/direct enterprise API — config, not architecture, since MCP transport already isolates tool servers); no artifact leaves the boundary. Data-classification tags on `.mas/` artifacts so briefs/specs containing commercially sensitive material inherit handling rules.
4. **SOC 2 posture, not certification.** Control mapping documented (extending SECURITY.md's OWASP LLM mapping pattern); certification is the operating company's program, not this system's deliverable.

Explicitly still out: multi-tenancy, marketplace/SaaS packaging, pricing.

---

## Part 50 — Sequencing, pilot shape, and acceptance

### 50.1 Phases

Durations assume the doc-14 cadence (one team, part-time platform support); calibrate at Phase 0 before trusting them.

| Phase | Weeks | Deliverables | Acceptance criteria |
|---|---|---|---|
| **P0 — Decisions + calibration** | 1–2 | ADR-U15..U18 accepted; substrate-profile loader + readiness report; Day-0-style calibration rerun on the pilot team's real artifacts (their brief, their plan, their diffs) | ADRs recorded; readiness report generated for 2 real teams; calibration numbers published |
| **P1 — Upstream wedge pilot (S0)** | 3–6 | Discovery/Plan/Spec running for one traditional-stack team with zero substrate; Gate R alias + CAB preflight checklist template | one real feature brief→plan→spec end-to-end through human gates; ≥1 CAB submission using the evidence bundle; spec-defect fixtures harvested |
| **P2 — Language + substrate rungs** | 7–12 | Java or .NET first-class per §47.2 (pick the pilot team's language, not both); pilot team climbs to S1/S2 | seeded-defect catch-rate published and within margin of Python's; Code Review + Test stages live on the pilot repo |
| **P3 — Data-pipeline profile v1** | 10–16 (overlaps P2) | §48.1 profile built to doc-13 standard on a second pilot (a real forecasting/reporting pipeline) | contract + eval gates catch a planted regression suite; one hypothesis-ledger reconciliation against realized pipeline metrics |
| **P4 — Enterprise hardening** | 13–20 | §49 items 1–3; item 4 documentation | SSO on all HITL surfaces; attestation export accepted by the pilot org's internal audit as evidence; VPC reference deploy documented |
| **P5 — ERP-extension profile v1** | 18–24 | §48.2 on a real ABAP/integration lane, behind Gate R | transport + integration checks green on the lane; one CAB cycle passed with system-generated evidence; scope discipline held (zero vanilla-config tasks accepted) |

Ordering rationale: P1 before everything because it needs nothing and proves cultural fit — if the upstream wedge fails at a traditional-stack team, stop and learn before spending P2–P5. Enterprise hardening (P4) lands before the ERP pilot (P5) because CAB/audit acceptance of the evidence bundle is what makes P5's Gate R cycle credible. Embedded/OT has no phase — it has triggers (§48.3).

### 50.2 What "easily applied" will mean afterward (the honest version)

After P5, the claim upgrades from "fits the modern digital teams" to: **any team at S0+ gets upstream value immediately; Java/.NET/Python teams at S1+ get the downstream core; data teams and ERP-extension teams get first-class profiles; the compliance apparatus consumes system evidence natively.** Vanilla ERP configuration, OT/plant-floor control, and org-wide DevOps modernization remain outside — the first two by ADR, the third because the ladder makes it *legible and incremental*, not because the system performs it.

### 50.3 FMEA additions (format per §09 Part 13)

- **F-18.1 Vacuous gates on missing substrate.** *Trigger:* stage activated below its floor by config error. *Detection:* substrate loader validates structurally; a gate whose det_tools set is empty for the active profile is a load-time failure, not a quiet pass. *Mitigation:* ADR-U15's inactive-never-degraded rule.
- **F-18.2 ERP profile scope creep into vanilla configuration.** *Symptom:* plan tasks with no code artifact in the ERP lane. *Detection:* done-vocabulary for the profile only admits transport/code/integration artifacts; such tasks die at plan lint. *Mitigation:* §48.2 scope statement; P5 acceptance explicitly counts this at zero.
- **F-18.3 Compliance theater.** *Symptom:* attestation ledger exported but gate approvals rubber-stamped (queue latency near zero, override rate near zero, defect escape rate unchanged). *Detection:* metric 6 (gate latency, §16.39.2) already measures the queue; add approval-dwell-time distribution to the weekly report. *Recovery:* same shed rule and operator cadence as §16.39.3.
- **F-18.4 Language parity drift.** *Symptom:* Java/.NET lanes pass gates that would fail in Python because a det_tools slot is weaker. *Detection:* seeded-defect catch-rate per language, re-run when any toolchain version bumps. *Mitigation:* provisional label in verdict banners until parity margin is met (§47.2).
- **F-18.5 Wedge pilot mistaken for full adoption.** *Symptom:* S0 success reported upward as "the system is deployed," downstream investment cancelled, value plateaus. *Mitigation:* the readiness report names the rung in every artifact banner; P1 acceptance language states the rung explicitly.

### 50.4 ADR summary

- **ADR-U15 — Substrate adoption ladder; stages below their floor are inactive, never silently degraded.** *Rejected:* best-effort degraded stages (vacuous green is worse than honest absence); requiring full substrate up front (kills the wedge).
- **ADR-U16 — Java/.NET promoted to first-class via fixture-gated toolchains; voters stay language-agnostic.** *Rejected:* per-language voter forks (divergence tax, same grounds as ADR-U12); LLM-as-linter substituting for missing det_tools (violates deterministic-first).
- **ADR-U17 — Enterprise deployability in scope; multi-tenant SaaS still out.** Reverses §08.96 for SSO/audit/deployment-envelope only. *Grounds:* procurement entry requirements at the target adopter class; attestation is a structured-state export, not new machinery.
- **ADR-U18 — OT/plant-floor control is advisory-only forever; embedded revisit gated on HIL rig + safety-case owner.** *Rejected:* treating OT as "just another profile" (the failure mode is physical).
