# 24 — Platform & Persona Editions: One Spine, Three Doors

Parts 68–72. This document turns the framework into a **platform**: the same eight-stage inner loop and P0–P5 outer loop (unchanged), packaged so that three very different adopters can each reach first value without reading nineteen design documents. It extends the delta mechanism of ADR-U12 (domain profiles, §17) and ADR-U18 (substrate ladder, §18) with one new layer — **editions** — and deliberately nothing else.

Companion: `25-distribution-and-ecosystem.md` (DX, packaging, benchmark, community). Numbering continues: ADR-U26+, invariants 14.21+, FMEA F-24.x.

---

## Part 68 — The platform thesis

### 68.1 What the 2026 landscape sells, and what it doesn't

The agent-framework market consolidated hard this year: Microsoft merged AutoGen and Semantic Kernel into Microsoft Agent Framework (GA April 2026), OpenAI archived Swarm for its Agents SDK, LangGraph hit 1.0, CrewAI crossed 1.0, and the field settled into a handful of orchestration styles — graph-based, role-based, handoff-based ([The Agent Report, 2026-05](https://the-agent-report.com/2026/05/ultimate-guide-open-source-ai-agent-frameworks/); [comparison surveys, 2026](https://alicelabs.ai/en/insights/best-ai-agent-frameworks-2026)). Every one of these is an **orchestration SDK**: it answers *"how do I wire agents together."*

None of them answers the question this repo answers: ***how does an idea become a built, maintained, and honestly marketed product, with every automated decision on the record?*** That is a lifecycle methodology, not a wiring library. It sits **above** the orchestration layer the way a build system sits above a compiler. The landscape gap is not rhetorical positioning — it is visible in the adoption data:

| What blocks adoption (measured) | What this framework already is |
|---|---|
| 88% of enterprise agent pilots never reach production; top blockers: evaluation/observability gaps (64%), governance friction (57%), model reliability (51%) — Anaconda/Forrester, replicated by a16z and MIT Sloan CIO panel ([survey compilation, 2026-04](https://www.digitalapplied.com/blog/ai-agent-adoption-2026-enterprise-data-points)) | Fixture-gated voters (§11.19), `eval-gate` regression baseline, attestation ledger, Gate R evidence bundles — the eval and governance story is the *architecture*, not an add-on |
| 70% of leaders name **non-deterministic outputs** as the #1 production-readiness barrier (same source) | ADR-U05: deterministic checks precede any LLM voting; the 12-Factor-Agents community independently converged on the same principle — "mostly deterministic code with LLM steps placed at exactly the right points" ([12-Factor Agents](https://github.com/humanlayer/12-factor-agents)) |
| Gartner: >40% of agentic-AI projects will be scrapped by 2027 for operationalization failures, not model failures ([reported 2026](https://www.kore.ai/blog/ai-agents-in-2026-from-hype-to-enterprise-reality)) | The substrate ladder (§18) exists precisely so a stage refuses to run vacuously below its infrastructure floor — `STAGE_INACTIVE` instead of theater |
| The 12% of pilots that *do* convert share a profile: 94% have a named owner with budget authority; 87% run automated evals on every change (same compilation) | That profile is this repo's gate-ownership table plus `autoproduct eval-gate` — the successful minority's operating model, shipped as the default |

The platform claim, stated in a claim-lint-survivable form: *this repo is a full-lifecycle MAS methodology with runnable deterministic gates; the measured blockers that kill most agent pilots are the things it was designed around.* Not "the best framework." Not "SOTA." Those would fail our own `unmeasured_superlative` check, and §76.3 makes that check binding on our own README.

### 68.2 Three doors, one spine

The goal — a platform serving **traditional-industry companies**, **one-person companies (OPC / 一人公司)**, and **SDE/MLE/agent engineers** — does not require three products. It requires three *entry configurations* over one unchanged spine:

```
                         ┌─ Edition E1: enterprise / traditional ─ docs 18–19 + §69
  FDR ─ inner loop ──────┼─ Edition E2: solo / OPC ──────────────  §70  (new)
  (8 stages, unchanged)  └─ Edition E3: engineer ────────────────  §71
  P0–P5 outer loop (unchanged)
```

An honest note on lineage, because the repo's own history is part of its provenance: the 2026-07-18 design session explicitly scoped this work as *"personal reusable harness + GitHub portfolio, **not product**"*, and produced a defensible-vs-not-defensible claims list to keep the README honest. The scope has since changed — docs 18–23 exist because it changed — but that session's discipline is retained and mechanized: the claims list became the claim ledger (§20.53), and §76.3 runs the platform's own positioning through its own linter. The scope grew; the honesty rules did not loosen.

### 68.3 ADR-U26 — Editions are preset bundles, never forks

**Decision.** An edition is a named preset over existing mechanisms: a default substrate rung, a gate-consolidation policy, default profiles, default cadence ceilings, and a documentation entry path. It is expressed as one YAML file (§72.1) resolved at workspace init. Editions may **narrow** (consolidate gates per explicit rules, lower WIP, lower cadence ceilings) but may never **widen** (skip a stage, remove a deterministic check, raise a compliance ceiling). *Rejected:* per-persona forks of the pipeline (three pipelines to maintain, and the personas migrate between editions as they grow — a solo founder who hires is an E1 customer with history); a "lite mode" that removes gates (the gates are the product; §68.1's data says removing them recreates the 88%).

---

## Part 69 — Edition E1: traditional industry / enterprise

Docs 18–19 already built the hard machinery (substrate ladder S0–S4, Gate R/CAB, Java/.NET lanes, evidence bundles, attestation). What was missing is the **adoption wrapper** — the artifacts a buying organization needs before the machinery is allowed to run. Survey data is blunt about what those are: among EU enterprises that considered AI and did not adopt, **70.9% cited a skills gap, 52.5% unclear legal/regulatory consequences, 48.8% data protection** ([Eurostat figures via SME adoption review, 2026](https://www.omago.ai/blog/sme-ai-adoption-2026-data)); only 21% of companies report a mature agent-governance model (Deloitte, cited ibid. compilation).

### 69.1 What E1 adds (and only this)

| Artifact | Content | Answers |
|---|---|---|
| **Procurement pack** `editions/enterprise/procurement/` | SECURITY.md cross-referenced to sandbox tiers (§11.17); data-flow one-pager (what leaves the machine: model API calls only; what never does: §22.64 taint classes); sample Gate-R evidence bundle from product-bench; license + provenance statement | the security questionnaire, before it is asked |
| **Pilot-to-production contract** template | Graduation criteria authored *as kill criteria* (§20.56.2) at pilot start: named owner, target outcome, `after_loops`, evaluation cadence. A pilot without them is the 88%. | "how do we avoid the pilot graveyard" — by making non-graduation a Gate PL5 decision, not a fade-out |
| **Named-owner requirement** | `edition.enterprise.require_gate_owner: true` — workspace init refuses without a named human per gate class | the 12%-conversion profile (§68.1), enforced at init rather than recommended in a slide |
| **Deployer-duty note** | EU AI Act Art. 50 applies 2026-08-02; the operating organization is the **deployer** for 50(4) disclosures (§21.58.2). E1 ships the compliance profile with `verified_on` fields the buyer's counsel confirms. | 52.5%'s "unclear legal consequences" — with a date and an article number instead of vibes |

### 69.2 What E1 explicitly does not promise

No claim of headcount replacement; no autonomous deploys (Gate 5 recommends, never deploys — unchanged); no "works with your ERP" until a det_tools lane exists for that stack and its seeded-defect catch rate is measured (§19's PROVISIONAL rule). The OECD's observation that SMEs overwhelmingly adopt off-the-shelf tools rather than custom AI (ibid.) is a constraint we accept: E1's pitch is *the off-the-shelf shape* — `autoproduct readiness` on day one, at whatever rung the org actually occupies — not a consulting engagement.

---

## Part 70 — Edition E2: solo / OPC (一人公司)

The genuinely new content. The persona is real and growing — solo-founded ventures are a rising share of new starts and AI adoption among solopreneurs is broad (practitioner surveys put both figures high; treat specific percentages as *third_party_report*, verify-at-adoption) — but one datum matters more than the boosterism, and it comes from the builder community itself: **the build barrier collapsed and the distribution barrier did not.** "2022: an MVP cost $50K–150K and took months. 2026: a solo founder ships in a weekend… Building got cheap. Distribution didn't." ([practitioner synthesis, 2026-05](https://www.buildmvpfast.com/blog/one-person-unicorn-ai-agents-solo-founder-billion-dollar-2026)). Fortune-class coverage of the "one-person company wall" says the same thing from the other side.

**Design consequence, stated plainly: for E2, the differentiator is not the coding MAS. Everyone sells the solo founder a build tool. The differentiator is docs 20–23** — the claim ledger, the marketing backstops, the experiment machinery, and the kill discipline — because distribution done honestly and cheaply is the unmet need, and distribution done dishonestly is now a legal exposure (§21.58, and Art. 50 lands in a week).

### 70.1 The binding constraint is attention, so the edition is built around it

Doc 16's human-attention budget and doc 22's F-22.5 (attention starvation, rated H×H) stop being one risk among many and become the design center. The 07-18 session's honest limit stands: the solo build budget was estimated at ~120 hours with a 30–32-week risk band if the Day-0 multiplier runs 1.5× — E2 does not shrink the work; it schedules it.

**Gate consolidation rules (the heart of E2):**

| May batch into the weekly founder review | May never batch |
|---|---|
| Gate 2 plan confirmations for `risk: low` tasks · Gate PL3 per-artifact publish approvals · trust-tier promotions · compound-loop CLAUDE.md proposals · cadence/WIP tuning | **Gate PL5 kill/pivot decisions** (a fired criterion interrupts the week — invariant 14.20 is not batchable) · **Gate 3 verdict acks on anything touching auth, payment, or user data** · **any consent/suppression override request** (there is none; §21.58.3 non-overridable) · **incident triage** (§10's clock still runs) |

Consolidation is *scheduling*, not deletion: every batched item still produces its full record; the ledger cannot tell E2 from E1.

### 70.2 The weekly founder review — the ritual as an artifact

`editions/solo/weekly-review.md` ships as a 30–45 minute agenda, in order: (1) fired or near-threshold kill criteria — first, while attention is fresh, because this is the decision that compounds; (2) queued Gate 2/PL3 batch with per-item dwell — `autoproduct dwell` already flags the rubber-stamp pattern (fast acks + zero overrides, F-18.3), and in E2 that check is promoted to a blocking weekly-review exit criterion, because a solo founder rubber-stamping their own gates has silently deleted the framework; (3) attention ledger — hours spent vs. §22.66.4's *attention cost per resolved hypothesis*; (4) next week's WIP, ceiling `wip: 1` product bet (E2 default; the outer loop's WIP 1–2 collapses to 1).

### 70.3 Minimum viable loop at S0-solo

E2's default substrate declaration is honest about a laptop-and-Railway reality: Stages 1–4 and 7 fully active; Stage 5 (deploy review) in config-lint mode until S1; Stage 8 ingesting only what exists (Sentry-or-nothing); P0 sensing capped at 3 standing sources; P1 sizing mandatory but time-boxed to one day; P3 restricted to `content_geo` + `product_surface` channels by default (email requires the §21.58.3 telemetry a fresh domain doesn't have — the edition makes the safe thing the default thing). Every restriction is a preset, not a capability removal: raising it is one YAML line and the ladder's normal rules apply.

### 70.4 FMEA additions

| ID | Failure | S×L | Detection / mitigation |
|---|---|---|---|
| F-24.1 | Founder rubber-stamps their own weekly batch | H×H | `dwell` as blocking exit criterion (§70.2); monthly self-audit prompt in the review template |
| F-24.2 | Solo bus factor: the one human is sick during a fired kill criterion | M×M | Fired criteria pause the loop, they never auto-decide (14.20); nothing degrades by waiting except opportunity cost |
| F-24.3 | Edition presets treated as ceilings forever; founder scales headcount but not rungs | M×M | `readiness` report nags when workspace history exceeds edition assumptions (e.g., >1 human acking gates) |

---

## Part 71 — Edition E3: engineer (SDE / MLE / agent engineer)

E3's user doesn't want a coach; they want a **harness they can extend without inheriting a belief system by accident**. E3 is therefore mostly *documentation topology plus extension contracts*, and one piece of positioning honesty.

### 71.1 What E3 exposes

- **Extension points, each with a machine-checked contract:** skills (YAML frontmatter + FixtureGate — a skill that cannot pass its fixture cannot register, §11.19), det_tools lane slots (§19, with the seeded-defect PROVISIONAL rule), channel/domain profiles (ADR-U12 deltas), editions themselves (§72), MCP servers (tier declaration mandatory, T3 for anything executing untrusted code).
- **product-bench as the eval harness** (§74): four workspaces with seeded defects and pinned expected findings; `autoproduct bench` is the regression bar an engineer's modification must clear.
- **Interop posture, current as of this writing:** MCP is the transport bet and it aged well — donated to the Agentic AI Foundation under the Linux Foundation in December 2025, ~97M monthly SDK downloads, ~9,400 public servers, with Server Cards (`.well-known` discovery) and statelessness on the 2026 roadmap ([WorkOS, 2026-03](https://workos.com/blog/everything-your-team-needs-to-know-about-mcp-in-2026); [Toloka, 2026-05](https://toloka.ai/blog/the-future-of-mcp-enterprise-adoption/)). Agent Skills became an open spec at agentskills.io (2025-12-18) with ~40 compatible products ([ecosystem report, 2026-06](https://agentman.ai/blog/agent-skills-ecosystem-report-2026)). Our skills remain internal-format but the frontmatter is deliberately close to the Skills spec; §75.2 tracks convergence as a watch item rather than a promise.
- **The quality-floor argument, which is E3's actual pitch:** the skills ecosystem's own benchmark found an average quality of 6.2/12 across 47,150 public skills, while curated skills raised agent pass rates by +16.2pp (SkillsBench, ibid.). *Catalog size is not quality.* This repo's answer is structural: **there is no way to register an unfixtured skill.** That is a falsifiable differentiator — an engineer can try to break it — which is the only kind worth shipping.

### 71.2 What E3 will not find, on purpose

No A2A/peer-messaging integration (ADR from doc 16 stands; noted honestly: 2026 hybrid MCP+A2A architectures are real and growing, and *if* this repo ever exposes external agent surfaces, that ADR gets formally revisited rather than quietly eroded); no RL fine-tuning loop (same doc, same rule); no orchestration-SDK shim layer — the harness *is* the orchestration opinion, and wrapping LangGraph would mean maintaining two sources of truth for state.

---

## Part 72 — Edition mechanics

### 72.1 `edition.yaml` (schema, resolved at `autoproduct init --edition <e>`)

```yaml
# .mas/edition.yaml — preset bundle; resolution order (later wins, may only narrow):
#   framework defaults → edition → domain profile(s) → substrate profile → workspace file
edition: solo                    # enterprise | solo | engineer
version: 1
defaults:
  substrate_rung: S0             # editions may set lower defaults, never disable the ladder
  wip_limit: 1
  channels_enabled: [content_geo, product_surface]
  cadence_ceilings: {content_geo: 2/week}      # ≤ framework ceiling or init fails
gate_policy:
  consolidation: weekly_review    # none | weekly_review
  never_consolidate: [PL5, incident, consent_override, gate3_sensitive]   # non-editable floor
  require_gate_owner: false       # enterprise sets true
attention:
  weekly_review_minutes: 45
  dwell_check_blocking: true
docs_entry: editions/solo/START-HERE.md
```

**`edition_lint` (deterministic, runs at init):** rejects any edition file that (a) lists a stage as skipped, (b) raises a cadence ceiling above the framework value, (c) removes an item from `never_consolidate`, (d) sets `require_gate_owner: false` while `substrate_rung >= S2`. Narrowing-only, enforced, not documented-and-hoped.

### 72.2 ADRs, invariants, metrics

**ADR-U26** (§68.3) — editions are narrowing preset bundles, never forks.
**ADR-U27 — Gate consolidation is scheduling, never deletion.** Batched gates produce identical records to unbatched ones; the audit ledger is edition-invariant. *Rejected:* a solo "trust mode" with reduced logging (the log is what makes the solo founder's later fundraise/acquisition diligence survivable, and F-24.1 is only detectable in the log).

| Invariant | Statement | Enforced by |
|---|---|---|
| 14.21 | No edition may disable a stage, a deterministic check, or a `never_consolidate` gate class | `edition_lint` at init; harness refuses unknown edition keys |
| 14.22 | Gate records are edition-invariant: identical schema and completeness regardless of batching | record writer ignores edition; `attest` chain verifies |

**Metrics added:** weekly-review completion streak; batched-gate median dwell (E2); procurement-pack question coverage — count of security-review questions answered by shipped artifacts vs. escalated (E1); edition migration events (E2→E1 growth is a success metric of the platform, and it is measurable because nothing forked).

---
*Cross-references: §16 (attention budget, WIP), §17 (profiles/ADR-U12), §18–19 (substrate, Gate R, lanes), §20–23 (outer loop), §25 (distribution). Research provenance for every external figure: doc 15 §6 research index, rows added this revision; secondary-source figures are marked third_party_report and carry verify-at-adoption semantics per §20.53.*
