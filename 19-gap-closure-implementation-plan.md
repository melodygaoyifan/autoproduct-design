# 19 — Gap-Closure Implementation Plan (Traditional-Industry Track)

Part 51 + Appendices I–L. The gap-closure track (G1–G24) implements doc 18: substrate ladder + cross-language promotion (Track 1), data-pipeline and ERP-extension profiles (Track 2), enterprise hardening (Track 3). Same conventions as docs 10/14: day-by-day granularity while the ground is new (G1–G3), week-level once patterns repeat; every week ends with checkable success criteria; the change-control protocol and 20% week-buffer policy of §10 Part 11 apply verbatim. Time budget: **24 weeks**, calibrated by the Phase-0 rerun in G1–G2 before trusting anything after G6.

**Prerequisite:** v1.3.0 minimum (Discovery/Plan/Spec live — the S0 wedge is built from them), v1.4.0 recommended. **External dependency — new for this track:** two pilot partners (one traditional-stack product team, one data team; the ERP lane joins at G18). Partner availability is on the critical path; every phase names a fallback that keeps the build moving if a partner slips (internal simulation on retro artifacts), but **milestone release gates require the real pilot** — simulated green does not release (mitigates F-18.5's inverse: shipping adoption features no adopter has exercised).

Build order rationale (from §18.50.1): **wedge first** (needs nothing, proves cultural fit, cheapest kill-switch for the whole track), **language parity second** (unblocks the pilot's downstream rungs), data profile third (second pilot, overlapping), **enterprise before ERP** (audit acceptance of the evidence bundle is what makes the ERP Gate-R cycle credible).

---

## Milestones

| Version | Weeks | Contains | Release gate |
|---|---|---|---|
| **v1.5.0** wedge | G1–G6 | substrate loader + readiness report + rung banners + Gate R + CAB preflight template + S0 pilot live | one real feature brief→plan→spec through human gates at the pilot; ≥1 CAB submission using the evidence bundle; ADR-U15..U18 recorded |
| **v1.6.0** parity | G7–G12 | pilot-language det_tools first-class (fixture-gated) + seeded-defect benchmark + provisional labeling + pilot at S1/S2 | catch-rate published, within calibrated margin of Python or labeled provisional; Code Review + Test live on the pilot repo |
| **v1.7.0** data | G10–G16 | data-pipeline profile v1 (det_tools, 3 voters, NFR vocab, gates) on a real pipeline | planted-regression suite caught end-to-end; one hypothesis-ledger reconciliation against realized pipeline metrics |
| **v1.8.0** enterprise | G13–G20 | SSO/OIDC on HITL surfaces + role-mapped gate authority + attestation ledger (signed export) + VPC reference deploy | internal audit accepts an attestation export as CAB evidence; all HITL surfaces behind SSO; deploy doc reproduced by someone who didn't write it |
| **v2.0.0** traditional-industry GA | G18–G24 | ERP-extension profile v1 behind Gate R + doc updates + retrospective | one CAB cycle passed with system-generated evidence on the ABAP/integration lane; zero vanilla-config tasks accepted (F-18.2 counted at zero); §18.50.2 claim published |

---

## Week G1 — ADRs + substrate loader (deterministic first)

**Day 1 — ADR ratification.** ADR-U15..U18 through change control; README + doc-18 status updates land in the same PR. *Done:* ADRs recorded; doc 18 marked accepted.

**Day 2 — `substrate-profile.yaml` schema + loader.** JSON-schema checked in; loader validates structurally (same pattern as the domain-profile loader, §41.1) and computes the active rung. *Done:* malformed profile rejected with a useful error; unit tests cover every rung boundary.

**Day 3 — stage-activation wiring.** Dispatcher consults the rung before routing; a stage below its floor returns `STAGE_INACTIVE(rung_required, rung_present)` — never a silent skip. Deploy Review's lint-only degraded mode is the one named exception, and its verdict banner says so. *Done:* an S0 profile routes spec fine and refuses code-review with the structured notice; the empty-det_tools load-time failure (F-18.1) has a test.

**Day 4 — readiness report generator.** `tools/adoption/readiness_report.py`: profile in, markdown report out — active stages, missing rungs, what each missing rung would unlock (the modernization-roadmap framing of §18.47.1). *Done:* reports generated for two synthetic profiles (S0 and S3) read correctly to a non-author.

**Day 5 — rung banners.** Every artifact banner and verdict banner carries the rung (mitigates F-18.5). *Done:* banner snapshot tests; a spec produced under S0 visibly says so.

## Week G2 — Gate R + evidence bundle

**Day 6-7 — Gate R gate-class.** Alias of Gate P1 mechanics (§41.3) with CAB semantics: entry = release candidate + preflight 100% green; outcome approved/rejected(reasons); rejection reasons → preflight fixtures where mechanizable, compounding-loop entries where not; submission human-only (`forbidden_autonomous_add: [cab_submission]`). *Done:* gate traverses on a synthetic RC; a scripted rejection lands a new fixture in the preflight suite.

**Day 8 — CAB preflight checklist template.** Starter shadow of a generic ITGC change checklist: change record completeness, rollback plan present, affected-system inventory, evidence bundle attached, approver-role match. Project-extendable like `.mas/spec-lint.yaml`. *Done:* checklist runs deterministically over a synthetic change package.

**Day 9-10 — evidence bundle exporter v0 (unsigned).** Gate decisions, verdicts, overrides, forbidden-action denials already exist as structured state (§09); exporter assembles them per-change into one reviewable bundle. Signing waits for G15 (attestation ledger) — v0 is the format, not the guarantee. *Done:* bundle for a real historical autoproduct change reads as CAB evidence to someone who has sat in a CAB.

## Week G3 — Wedge pilot onboarding

**Day 11-12 — Phase-0 calibration rerun.** Day-0-style calibration (day-0-calibration.md, Track B shapes) on the pilot team's *real* artifacts — their brief, their plan, their last quarter's change tickets. Publish the numbers; recalibrate G4+ durations against them. *Done:* calibration note committed; week plan adjusted or explicitly confirmed.

**Day 13 — pilot S0 configuration.** Substrate profile authored with the pilot team; readiness report delivered as their roadmap. *Done:* their profile loads; Discovery/Plan/Spec active, everything else `STAGE_INACTIVE`.

**Day 14-15 — first traversal.** One real, small pilot feature: brief → Gate U1 → plan → Gate U2 → spec → Gate U3, all human gates run by pilot-team owners, not us. *Done:* traversal logged; every gate decision in the YAML mirror; friction notes filed as fixtures or backlog.

## Week G4–G6 — Wedge operation → v1.5.0

Pilot runs 2–4 more features at S0; spec-defect and gate-friction fixtures harvested into `tests/integration/voters/fixtures/upstream/`; first real CAB submission using the G2 evidence bundle (their CAB, their change record). Weekly metric: gate latency + approval-dwell-time distribution (the F-18.3 instrumentation, live from day one). Fallback if pilot slips: retro-run the wedge on three already-shipped pilot-team changes — build stays on schedule, **release waits for the live traversal**. **v1.5.0** on the milestone gate.

## Week G7–G9 — Language toolchain (pilot's language only, per §18.50.1)

G7: seeded reference repo — planted defects per det_tools slot (lint/type, test, mutation-survivor, SAST, dependency), hand-labeled, ~30 defects. This is the fixture gate for toolchains (§47.2): no toolchain registers without its catch-rate measured against it. G8: adapters for the pilot language (Java: Checkstyle/Error Prone/SpotBugs, JUnit+JaCoCo, PIT; .NET: Roslyn analyzers, xUnit+Coverlet, Stryker.NET; Semgrep + OWASP Dependency-Check either way) wired into det_tools/build gate behind the existing tool registry. G9: catch-rate benchmark run + published; parity margin computed vs the same seeded suite in Python; below-margin slots get the `provisional` verdict-banner label (F-18.4). *Success:* every slot registered or explicitly provisional with a named gap.

## Week G10–G12 — Pilot climbs + data profile starts → v1.6.0

G10–G11: pilot team to S1 (PR flow on their repo — their platform work, our support) then S2 (CI); Code Review and Test stages activate; first downstream verdicts on their real PRs; voter fixtures harvested from any human-marked-wrong finding (R-U1 discipline unchanged). G12: soak + **v1.6.0**. In parallel from G10, the data profile begins (below) — separate lane, separate pilot, no shared critical path until G16.

## Week G10–G16 — Data-pipeline profile v1 → v1.7.0

G10–G12: det_tools — data-contract check (dbt-test/Great-Expectations-class suites), DAG lint + dry-run compile, eval-set regression gate (frozen labeled sets, score-delta vs pinned baseline), lineage/impact check, backfill-idempotency check (fixture-slice re-run → identical output hash), each with unit fixtures per the §11 discipline. G13–G14: DataContract, BackfillSafety, DriftAndCost voters + 8-fixture gates each; NFR vocabulary (freshness p95, row-count tolerance, eval floors, cost-per-run) into the Spec stage's vocabulary loader; `forbidden_autonomous_add: [production_backfill, training_data_mutation]`. G15–G16: live on the data pilot's real pipeline; planted-regression suite (schema break, silent null flood, eval regression, non-idempotent backfill) must be caught end-to-end; one hypothesis-ledger reconciliation against realized pipeline metrics (§13.34.3 machinery, no changes). **v1.7.0.**

## Week G13–G20 — Enterprise hardening → v1.8.0

G13–G14: SSO (OIDC/SAML) on every HITL surface; IdP-group → gate-class authority mapping in the policy loader (the *who* dimension on trust-tier ceilings, §18.49.1); test: an unauthorized-role approval attempt is refused and logged. G15–G16: attestation ledger — append-only signed export over the structured gate/verdict/override state; retention policy config; the G2 evidence bundle upgrades from v0-unsigned to ledger-backed. G17–G18: VPC reference deployment — self-hosted compose/terraform reference, model access via configured enterprise endpoints (config, not architecture — MCP transport unchanged), data-classification tags on `.mas/` artifacts. G19–G20: hardening drills — F-18.3 detection verified by scripted rubber-stamp pattern (dwell-time collapse must alarm); SOC-2 control mapping documented extending SECURITY.md; internal-audit review of a real attestation export. **v1.8.0** when audit accepts the export as evidence.

## Week G18–G24 — ERP-extension profile + GA → v2.0.0

G18–G19: det_tools — abaplint (ATC where the pilot's licensing allows), transport dependency & sequence check, integration-contract check (IDoc/API schemas vs consumer registry); done-vocabulary admits only transport/code/integration artifacts (the F-18.2 plan-lint tripwire). G20–G21: IntegrationBlastRadius + ComplianceControl voters + fixtures; `deploy_impact` gains `cab_review: true` train tasks (§18.48.2). G22–G23: live on the ERP pilot lane — one real custom-extension change through the full spine, Gate R cycle with ledger-backed evidence, their CAB. G24: docs public, §18.50.2 claim published verbatim with the measured numbers behind it, retrospective; buffer absorbs overrun per the 20% policy. **v2.0.0** on the milestone gate — zero vanilla-config tasks accepted across the pilot, counted, in the retrospective.

---

## Appendix I — File tree delta (extends §14 Appendix E)

```
autoproduct/
├── tools/adoption/{substrate_loader,readiness_report}.py
├── tools/gates/{gate_r,cab_preflight,evidence_bundle}.py
├── tools/lang/{java,dotnet}/            # det_tools adapters, per-slot
├── tools/data/{contract_check,dag_lint,eval_gate,lineage_check,backfill_check}.py
├── tools/erp/{abap_lint,transport_check,integration_contract}.py
├── harness/{authz.py,attestation.py}    # role→gate-class mapping; signed ledger export
├── deploy/vpc-reference/                # compose/terraform + endpoint config
skills/profiles/{data,erp}/*.md          # 5 new voters
tests/toolchains/seeded/{java|dotnet}/   # planted-defect reference repo (~30 defects)
tests/integration/voters/fixtures/{data,erp}/{voter}/*.yaml
.mas/{substrate-profile.yaml,cab-preflight.yaml}
```

## Appendix J — Dependencies delta (extends §14 Appendix F)

Language toolchains (Checkstyle/Error Prone/SpotBugs/PIT or Roslyn/Stryker.NET; Semgrep, OWASP Dependency-Check) run as **external pinned binaries behind the tool registry**, not Python deps — same posture as existing det_tools. `abaplint` (Node, pinned) likewise. Data profile: the pilot's own dbt/GE install is the runtime; autoproduct wraps, never vendors. New Python deps: an OIDC client library and a signing library (attestation ledger) — both pinned at G13/G15; nothing else.

## Appendix K — Risk register delta (extends §14 Appendix G; F-18.1–.5 are the design-level FMEA, §18.50.3)

| ID | Risk | L×I | Mitigation |
|---|---|---|---|
| R-G1 | Pilot-partner slip stalls the critical path | H×M | Fallback simulations keep the build moving; release gates wait for live pilots — schedule slips, quality doesn't |
| R-G2 | Wedge succeeds socially but produces no measurable spec-quality delta | M×H | First-pass-gate-rate + fixture-harvest counts from G4; a metrics-flat wedge at G6 is a stop-and-learn gate for the whole track |
| R-G3 | Seeded-defect repo overfits — catch-rate flatters the toolchain | M×M | Defects sourced from the pilot's real historical bugs where possible; benchmark re-run on every toolchain version bump |
| R-G4 | Enterprise auth work balloons (IdP quirks, legacy SAML) | M×M | OIDC first, SAML only if the pilot IdP demands it; scope is HITL surfaces only — no ambient service mesh |
| R-G5 | ERP pilot's licensing blocks ATC | M×L | abaplint is the floor and is license-free; ATC is an upgrade, not a dependency |
| R-G6 | Two overlapping pilots exceed the human-attention budget (§16.39) | M×H | WIP limits apply to pilots as to features: G10–G16 overlap is the only planned concurrency, and metric 6 is watched weekly |

## Appendix L — Glossary delta (extends §14 Appendix H)

**Substrate rung (S0–S4)** the adopting team's declared infrastructure level; activates stages, never weakens gates (§18.47.1, ADR-U15) · **Wedge** the S0 deployment of Discovery/Plan/Spec — full upstream value on zero infrastructure · **Gate R** the CAB/regulated-change-control external gate; Gate P1 mechanics pointed at internal bureaucracy (§18.47.3) · **Evidence bundle** the per-change export of gate decisions/verdicts/overrides assembled for CAB review; ledger-backed after G15 · **Attestation ledger** append-only signed record of every gate decision and forbidden-action denial (§18.49) · **Seeded-defect catch-rate** the fixture gate for toolchains: fraction of planted defects a language's det_tools suite catches (§18.47.2, ADR-U16) · **Provisional toolchain** a language lane whose catch-rate lags the calibrated parity margin; labeled in every verdict banner (F-18.4) · **Readiness report** the generated modernization roadmap: missing rungs and what each unlocks · **G1–G24** the gap-closure track weeks (this doc).
