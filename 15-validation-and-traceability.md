# 15 — Validation & Traceability Report

This document records a five-perspective validation of the full-lifecycle doc set (08–14), performed against (a) the software development cycle, (b) the 2025–26 research and tooling base, (c) build-guidance sufficiency, (d) the source methodology reference (`archive/external-reference-ai-mas-methodology.md`, §1–54) and the working sessions that produced this edition, and (e) the granularity standard set by documents 08–11. Where validation found gaps, the fixes are already applied in this edition; each is marked **[fixed]** with its location.

---

## 1. Completeness — SDLC stage coverage

Mapping the classical SDLC (plus the product and project management cycles the methodology reference merges in, §12.22.6):

| Lifecycle concern | Where it lives | Status |
|---|---|---|
| Problem/requirements discovery | Discovery MAS (§13.26): brief, hypothesis ledger, evidence classes | ✅ |
| Project planning (tasks, sequencing, capacity, sprint-equivalent cadence) | Planning MAS (§13.27): DAG, lanes, budget, calibrated estimates; weekly compounding cadence carries the retrospective rhythm | ✅ |
| **System design / architecture** | **Was a gap in the first upstream draft** — the methodology reference requires an architecture document (Phase 2/3, §29.2) and both Kiro and Spec Kit carry a design/technical-plan artifact. **[fixed]**: `spec/design.md` with required sections, Spec-voter coverage, human ack at Gate U3, and ADR-U07 two-pass planning (§13.28.2, §12.23.8) | ✅ |
| Detailed specification (ACs, contracts, test specs) | Spec MAS (§13.28): EARS + contracts + module deltas + skeletons + coverage matrix | ✅ |
| Implementation | Coding MAS (§13.29): single-writer lanes, test-first, build gate, SCR back-edge | ✅ |
| Code review | §09.4–.5 (unchanged, canonical) | ✅ |
| Testing (unit/integration/mutation/UI); UAT | §09.5.4.9–10 + §09.9.11; manual-UAT ACs (`uat: true`) surface as human checklists at Gate U3 and pre-release (§12.24.4-9) | ✅ |
| Release/deployment | §09.11 + release notes as changelog-fragment roll-up (§13.34.4) | ✅ |
| Maintenance/operations | §09.12 + hypothesis reconciliation (§13.34.3) | ✅ |
| Retrospective/continuous improvement | Compounding loop (§09.8.4) extended with upstream targets and `root_cause_stage` labeling (§13.34.2); Memory-Gate governance mapping (§13.32.3) | ✅ |
| Documentation/changelog | Per-task changelog fragments at the build gate (§13.29.7) | ✅ **[fixed]** |
| **Opportunity intake / problem selection** | **Was out of scope by design; now in scope as the outer loop.** P0 Opportunity Sensing (§20.54) over declared-standing signals; the framework prepares ranked candidates, humans choose at Gate PL1 | ✅ **[added, doc 20]** |
| **Market / viability analysis** | P1 (§20.55): bottom-up sizing with sensitivity ranges, probe-derived competitor facts, Disconfirmation voter, quarantined retrieval | ✅ **[added, doc 20]** |
| **Product definition (PRD)** | P2 (§20.56): outcomes, non-goals, kill criteria, instrumentation-or-task; machine-checked handoff into Stage 1 Discovery | ✅ **[added, doc 20]** |
| **Launch / GTM execution** | P3 (doc 21): seven deterministic backstops, channel profiles, pre-registered two-stage experiments; every external act human-gated, no spend ever | ✅ **[added, doc 21, bounded]** |
| **Product outcome measurement** | P4 (§22.62): cohort readings against PRD outcomes, hypothesis verdicts, typed attribution — distinct from Stage 8's system-health signals | ✅ **[added, doc 22]** |
| **Portfolio decision / stopping** | P5 (§22.65): mechanical kill-criteria evaluation, loop budget, append-only kill registry; human decision required, never automated | ✅ **[added, doc 22]** |

Deliberately out of scope, stated in README: executing real-user research, product strategy *ownership* (the outer loop prepares options; Gates PL1/PL2/PL5 decide), visual design authorship, auto-merge/auto-deploy/L4 — and, added by ADR-U20/U21/U23, **any money-spending action, retrieval manipulation, and fabricated user evidence of any kind**. These are exclusions by design, not omissions. The pricing/GTM exclusion is the one thing docs 20–23 reverse, and it is reversed narrowly: drafting and measuring are in scope, deciding and publishing are not.

## 2. Correctness — currency of solutions and best practices

Verified in working sessions dated 2026-07-18 via web search against primary sources; the load-bearing choices and their evidence:

| Design choice | Evidence (verified) | Status |
|---|---|---|
| Vote, don't debate; independent parallel judges | Debate-or-Vote (NeurIPS 2025, arXiv:2508.17536); Kaesberg et al. (arXiv:2502.19130) | current |
| Spec failures dominate MAS failures → invest upstream | MAST (arXiv:2503.13657), ~42/37/21 split | current |
| Single-writer generation; no coding voter panel | §08.2.2.9 + Anthropic multi-agent engineering (15× tokens; write-heavy ≠ parallel) | current |
| EARS acceptance criteria; spec-anchored not spec-as-source | AWS Kiro (GA 2026, EARS + SMT-based requirements analysis); Spec Kit v0.8.x, 93k+ stars, 30+ agents (May 2026); 2026 SDD field guides converge on "spec-anchored" | current |
| Fresh-context revision; state in files | arXiv:2505.06120 (~39% multi-turn drop); community long-run loop patterns (stop hooks, fresh context/iteration; Claude Code native Loop, 2026) | current |
| Delta-based context/skill evolution; no wholesale rewrites | ACE (arXiv:2510.04618): brevity bias & context collapse | current |
| Package-hallucination defense, calibrated | USENIX Sec'25 (arXiv:2406.10279): ~19.7% avg, ~5.2% commercial vs ~21.7% OSS — errata applied §12.24.4-2 | current, corrected |
| Deterministic-first hybrid; hooks enforce | Harness-engineering consensus; §09.11.6 | current |

No post-May-2026 development surfaced in the sessions that overturns any of these; the two genuinely open questions are logged as indeterminate with A/B plans (§12.23.9: preflight voter, voter counts).

## 3. Sufficiency as build guidance

The test used: for each subsystem, does the doc set answer *what to build, how it behaves at the edges, and what "done" looks like* without inventing on the spot? Post-expansion status: base classes and node code (§13.25.2, §13.29.2–3, §13.30), deterministic tools with implementations (dag/lane/ears/coverage/assertion_delta, §13.27.3/28.4/29.5), 18 complete skill definitions with good/bad examples, per-stage verdict taxonomies, gate preconditions, HITL Issue bodies (§13.32.4), full policy schema + loader ceiling (§13.32.2), 4 worked fixtures + the 120-fixture contract (§13.33.2), metrics with computation sources (§13.33.1), 12-week plan with day-level early weeks and per-day done-criteria (doc 14), and Day-0 Track B as the calibration gate. Known intentional residue: illustrative `...` bodies inside otherwise-specified functions (prompt assembly, artifact writing) — their contracts, schemas, and tests are specified; their prose is the implementer's. Verdict: **sufficient to build from**, with doc 10's caveat inherited: estimates are calibrated by Day-0, not promised.

## 4. Traceability — methodology reference (§1–54) → this edition

Every load-bearing concept from the source methodology and the working sessions, and where it landed. (References: `M§n` = methodology reference section.)

| Source concept | Landing | Notes |
|---|---|---|
| Reverse interrogation (M§1.1) | Discovery posture (§13.26.1); Spec Completeness voter procedure (§13.28.5) | bounded to 10/5 archetypal questions |
| No stage skipping; stage gates (M§1.2, M§26) | Gate ladder U1–U4 (§13.32.1) + downstream Gates 1–3; structural (agents cannot fetch missing artifacts) | |
| Evidence over vibes; Evidence Report (M§1.3, M§33) | Evidence draft schema at build gate (§13.29.4/.7); evidence ledger §09.9 | |
| Four LLM risks: context degradation, stochasticity, self-assessment bias, context pollution (M§2) | Manifest+fresh context (§13.29.3, §13.25.4); fixed SOP/templates; external completion judgment (build gate, router); lanes+locks (§13.27.3) | |
| Three-layer governance; CLAUDE/AGENT.md (M§3–5) | §09.10 CLAUDE.md integration; constitution = CLAUDE.md + `.mas/*` policies; <50-line pointer discipline retained | |
| Directory/feature-folder structure (M§4, M§15) | `features/{id}` layout (§13.25.5) | superset of the source layout |
| Product/NFR/Gap agents (M Phase 1) | Desirability+Viability (product), Feasibility (technical/NFR reality), ScopeDiscipline+reverse interrogation (gap) (§13.26.3) | roles preserved, verification-first shape |
| Plan template incl. §7 Technical Design (M Phase 2) | plan.yaml (§13.27.5) + design.md (§13.28.2) via ADR-U07 two-pass | |
| PRD / Architecture doc / Data protocol / Test spec (M Phase 3, M§28–29) | brief (PRD-lite) · design.md · contracts/ · test-skeletons + EARS | data protocol = contracts, schema-compiled |
| AgentTask type; shared state (M§3.3, M§24, M§51) | UpstreamFields TypedDict (§13.30.1) + dual state mirror (§09.6); grounding/evidence/tool-governance/security/observability fields all present | AntiHallucinationState fully absorbed |
| Dual-agent per stage; voting; reconciliation (M§8, M§25) | Writer + heterogeneous voter panel per stage; Leader filter replaces Reconciliation Agent (cross-ref ruling R2: disagreement → ESCALATE_VOTER_DISAGREEMENT to human, never LLM-arbitrated) | |
| 3-fail escalation (M§32.2) | §12.22.7 table; circuit breakers | |
| Git worktree strategy; merge checks (M§9) | Lanes proven disjoint at U2 (§13.27.3); reverse-merge safety §09.7.2.8; never-auto-merge unchanged | |
| Sprint structure (M§27) | Cadence carried by weekly compounding PR + milestone plan (doc 14); a per-team sprint template remains a project-integration choice (§09.10 project.yaml), not a framework mandate | conscious thinning, documented |
| Leader duties / Stage Decision Report (M§23) | Leader nodes + verdict taxonomies; the mirror's run report (§13.33.4) is the decision report | |
| Handoff / Decision Record formats (M§31) | Handoff/PR template (§13.32.4); ADRs + design.md decision-record section | |
| Failure modes & defenses (M§32) | FMEA §09.13 + §13.35 | |
| Vibe→Controlled coding (M§34) | fast/standard/deep modes (§12.24.3) + unattended-loop policy (§13.29.9) | |
| Semi-automated version; human control points (M§37) | forbidden_autonomous ceilings (§13.32.2) = exactly the M§37 human list (enter dev, scope lock, architecture accept, review conflict, merge, release, memory writes) | |
| Hallucination forms & abstention (M§38–39) | BLOCKED_* statuses; sources_read receipts; charter rules 11–13 (§13.26.7) | |
| Grounding per stage (M§40); Context Manifest / JIT (M§41) | ContextManifest + hash receipts (§13.25.2, §13.29.3) | |
| Eval harness & regression evals (M§45) | Fixture gates (120 upstream) + production-miss→fixture pipeline (§13.33.2) — the M§45.3 regression rule, mechanized | |
| Memory Gate, memory types (M§46) | §13.32.3 mapping onto the compounding loop's controls | six questions → five enforced controls + human PR review |
| Runtime observability, run report, drift (M§47) | §13.33.1/.4 + §09.9 | |
| Prompt injection & agent security (M§48) | §09.4.2.2 + taint lockout (§13.31.2) + credential-free research | |
| P0/P1/P2 gap list (M§49) | All P0/P1 items present in 08–14; P2 "skill library" = learned-skill registry §09.12.12 | |
| Anti-hallucination 10 rules (M§50) | §08.1.7 + §13.26.7 extension | |
| Top-10 rules; final principles (M§36, M§54) | §08.1.3 principles; "less autonomy, more accountability" is the autonomy contract | |
| MVP SOP (M§19) | Day-0 calibration + Week U1–U3 minimal path is the runnable MVP | |
| Ralph-loop long-run mode | §13.29.9 unattended operation, harness-judged completion | |
| Maturity ladder vs trust tiers (session ruling C3) | §13.32.1 orthogonality note + loader warning | |
| Three-cycle merge (M§22) | §12.22.6 | |

No load-bearing session decision (R1–R6, C1–C4, A-series adoptions) is contradicted anywhere in 12–15; R1 (deterministic state machine over LLM orchestrator), C1 (never auto-merge), C4 (L3/L4 structural unreachability) are restated where upstream touches them.

## 5. Granularity parity with 08–11

Standard applied: doc 09's density — full base-class code, complete skills with positive *and* negative examples, executable tool implementations, full graph/conditional code, schemas, HITL bodies, fixtures, FMEA with recovery paths, ADRs with rejected alternatives. Post-expansion, doc 13 carries: 2 base classes and 6 orchestration modules in real code; 5 deterministic tools implemented (not described); 18 skill blocks in the §09.4.4 format; 4 verdict taxonomies; 3 HITL Issue templates; full policy file + loader ceiling; 4 worked fixtures; 9 FMEA entries in the 5-field format; 7 ADRs with alternatives and re-examine triggers. Doc 14 carries per-day done-criteria for U1–U3 and code-relevant deltas per week. Remaining density difference versus 09 is proportional to subject size (four generative stages reuse §09's verify/leader/HITL machinery rather than restating it), and every reuse is an explicit cross-reference, not an omission.

Docs 20–23 are held to the same standard at their own subject size: 2 deterministic tools implemented in full (`claim_lint`, `evaluate_kill_criteria`) plus 5 more specified to executable precision with their finding rules enumerated; 7 artifact schemas (claim ledger, sizing, PRD, experiment, three handoff contracts); 24 voter charters in the "judges / explicitly not / failure it exists to catch" format; 3 gate rubrics with entry conditions, presented material, and legal outcomes; 13 FMEA entries in the 5-field format; 7 ADRs with rejected alternatives; 7 new invariants; 5 metrics including one deliberately aimed at falsifying the track itself; a 16-week plan with day-level detail through P5 and week-level after, plus 4 appendices. Where they are thinner than doc 09 it is because they reuse rather than restate — the generate→tools→vote→verify→leader→gate template, the fixture gate, the trust tiers, the taint mechanism, and the profile-delta loader are all inherited unchanged, and each inheritance is a cross-reference.

---

## 6. Research index — every verified finding and where it lands

Complete list of findings verified across the working sessions (searches dated 2026-07-18; product-loop rows added 2026-07-26), with citation and application. Items marked ⓘ are context/motivation only — verified and indexed here so nothing found is absent from the published set, but no design element depends on them.

| Finding | Source | Where applied |
|---|---|---|
| MAS failures: ~42% specification/system-design, ~37% inter-agent misalignment, ~21% verification/termination | MAST, arXiv:2503.13657 (NeurIPS 2025) | §08.2, §12.22.2 — resource allocation to Spec + Verification |
| Voting beats debate for independent judgments; debate ≈ martingale | arXiv:2508.17536 (NeurIPS 2025) | P3 vote-don't-debate, all voter panels |
| Majority voting +13.2% on code tasks | Kaesberg et al., arXiv:2502.19130 | §08.2 voter-panel sizing rationale |
| Context evolution needs delta updates; brevity bias & context collapse on rewrites | ACE, arXiv:2510.04618 (+10.6%) | Compounding loop's append/delta discipline (§09.8.4) |
| Production AI review: 16%→54% acted-on rate via verification pass; <1% incorrect-comment rate; no auto-approve | Anthropic Claude Code Review engineering (2026-03) | Verify pass, action-rate metric, never-auto-approve |
| Package hallucination: ~19.7% avg across 576k samples; ~5.2% commercial vs ~21.7% OSS; 58% names recur | USENIX Sec'25, arXiv:2406.10279 | slopsquat_check; errata §12.24.4-2 |
| ~39% average multi-turn performance drop | arXiv:2505.06120 | Fresh-context revision protocol (§13.25.4); manifest discipline |
| Multi-agent ≈ 15× tokens; write-heavy tasks parallelize poorly | Anthropic multi-agent engineering | ADR-U01 single-writer Coding; mode gating |
| Spec Kit v0.8.x, 93k+ stars, 30+ agents; constitution→specify→plan→tasks→implement | GitHub Spec Kit (verified May 2026 state) | Stage alignment; spec-anchored posture (§12.23.1) |
| EARS notation; Kiro GA with SMT-solver requirements analysis (2026) | AWS Kiro | ears_lint; AC grammar (§13.28.4) |
| Design artifact between intent and implementation; ordering split (Kiro design-then-tasks vs Spec Kit plan-then-tasks) | Kiro / Spec Kit docs | design.md + ADR-U07 two-pass planning |
| Review-variance collapse in LLM reviewer panels (27.2%) | AgentReview, arXiv:2406.12708 | Independence: no cross-voter visibility |
| MCP supply-chain RCE precedent | CVE-2025-6514 | §11.17 subprocess isolation, pinned servers |
| Graduated autonomy tiers for agents | arXiv:2508.11867 | Trust tiers + forbidden_autonomous ceilings |
| Policy-as-Prompt: deterministic checks first, LLM policy second | arXiv:2509.23994 | Deterministic-first hybrid (§09.11.6, ADR-U05) |
| Reviewer-pattern taxonomy (9 patterns) | DAPLab | Voter roster mapping (§09.4) |
| Agentic pentest CSRF/SSRF probes | Tenzai reports | Security voter probes (§09) |
| Mutation testing as adversarial test gate | mutmut; AdverTest arXiv:2602.08146 (66.63% Defects4J) | Stage-6 mutation loop |
| Sustained-autonomy vibe-coding risk taxonomy | SusVibes, arXiv:2512.03262 | Unattended-mode policy bounds (§13.29.9) |
| SOP + document-mediated agent collaboration (and its weak-verification lesson) | MetaGPT arXiv:2308.00352; ChatDev arXiv:2307.07924 | Artifact-mediated handoffs; verification-first correction |
| Long-run loop pattern: stop hooks, external completion judgment, fresh context/iteration | Community (Huntley) + Claude Code native Loop (2026) | §13.29.9 unattended operation |
| AGENTS.md as a cross-tool standard; root file as short pointer (<50 lines), grow-on-error ⓘ | AGENTS.md standard, 30+ tools | CLAUDE.md conventions (§09.10) already follow the discipline; standard named here for portability |
| Devs use AI on ~60% of work; fully delegate only 0–20% of tasks | Anthropic 2026 Agentic Coding Trends Report | Corroborates bounded autonomy / Assistive-forever gates |
| Agent-PR economics: ~28% merge near-instantly; reviewer abandonment ≈38% of rejected agent PRs; cheap-signal circuit breakers work; review "wasn't built to recover missing intent" | Early-Stage Prediction of Review Effort (Jan 2026, 33,707 PRs) + companion abandonment study; O'Reilly synthesis (June 2026) | Evidence-draft PR bodies (intent made recoverable, §13.29.7); mode router; per-task circuit breaker |
| Production multi-agent review pipelines converged on trigger→context→adversarial verification→dedupe→policy engine→feedback loop | 2026 industry survey (CodeRabbit code-graph+MCP context, Qodo Merge) | Independent corroboration of the §09 vote→verify→leader→policy shape |
| Dev trust gap: 84% adopt AI tools, 33% trust accuracy ⓘ | Stack Overflow 2025 survey | Motivates the verification-heavy budget split |
| Library spec registries (10k+ specs) against API hallucination ⓘ | Tessl Spec Registry | Ecosystem alternative alongside repo probes + slopsquat_check |
| Symbol-index navigation ≈77% active-token reduction vs whole-file reads ⓘ | 2026 practitioner reports | Supports code_intel-first context assembly (§13.29.3) |
| Injection defense by design: control/data-flow separation + value-level capabilities; dual privileged/quarantined LLMs | CaMeL, arXiv:2503.18813 (DeepMind); survey arXiv:2505.02077 | §16.40.2 — Discovery two-invocation flow = the quarantine pattern; taint lockout = session-level capabilities; value-level = staged upgrade path |
| Reflective prompt evolution beats RL adaptation (~6pp avg, up to ~19pp, ≤35× fewer rollouts); per-agent sequential optimization for MAS | GEPA, arXiv:2507.19457 (ICLR 2026 Oral); MAS-PromptBench arXiv:2606.23664; production report (Decagon 2026-03) | §16.40.1 + ADR-U11 — proposal engine inside the governed compounding loop; held-out fixtures guard Goodhart |
| Budgeted-MAS synergy phase transitions (improve/saturate/collapse by context, fidelity, error correlation) | 2026 theory line (indexed via agent-papers survey) | §16.38.3 — resolved from watch list into the scale-until-metrics-degrade stance |
| Agent interop protocols (A2A, ACP) alongside MCP | 2026 protocol landscape | §16.40.5 + ADR-U09 — evaluated, rejected: vote-don't-debate removes peer messaging by design |
| Sandboxed execution as the agent-runtime default ⓘ | practitioner consensus, 2025-26 harnesses | §16.40.4 — deployment floor under the MCP risk ladder |
| QA-agent capability line: strong on regression/visual/contract, weak on usability & exploratory judgment | 2026 QA-agent landscape surveys | §17.41.2 — the machine-core / human-remainder split every profile applies |
| Visual regression discipline: concentrate on design-system components, marketing pages, checkout; mid-flow visual assertions; Playwright/Chromatic/Percy ecosystem | 2026 visual-testing field guides | §17.42 — baselines as fixtures, thresholds+masks, baseline changes ride the compounding PR |
| 小程序 hard constraints: main/subpackage ≤2MB (total ~10MB), domain whitelist + HTTPS, dual-thread no-DOM, setData discipline, 40-100MB memory, strict review; official DevTools automation | platform docs + practitioner constraint sets (limits verified 2026-07; re-verify at release) | §17.43 — constraints as build-gate checks; rejection reasons → preflight fixtures |
| Mobile 2026 defaults: Maestro YAML flows via accessibility layer with settle-and-retry; Espresso/XCUITest/Appium tiering; benchmarks (cold start <2s, iOS first frame <400ms, <5%/hr battery, 4h soak, p95 net <2s); real-device gap; store rejection for single missing permission prompt | 2026 mobile-testing guides | §17.44 — flows from ACs, device-tier gate, store preflight, staged rollout = §09.11 canary |
| Game-agent field consensus: receipt-heavy supervised automation, internal branches, kill switches, "human playtest gate always" ("tests pass, game unfun"); AI playtesting at thousands-of-sessions scale; Unity AI open beta (2026-05) with custom-MCP pipelines outperforming it | 2026 game-dev agent guides + hands-on reports | §17.45 — independent corroboration of this framework's posture; playtest gate as core gate |
| "Product review" paradigm: agents diff live UI on real devices against design files | 2026 mobile-agent tooling reports | §17.42.2 DesignFidelity voter; design authorship stays human (README) |
| GEO named and benchmarked: statistics-addition, source-citation, and quotation-addition raise generative-engine visibility up to ~40% on a 10k-query benchmark; classical keyword-density signals show minimal influence | Aggarwal et al., *GEO: Generative Engine Optimization*, KDD 2024, [arXiv:2311.09735](https://arxiv.org/abs/2311.09735) | §21.60.1–.2 — the tactics that work are the tactics that make a page verifiable; `geo_extractability_check` requires inline sources for every statistic |
| Generative-engine visibility measurement is unstable across samples; single-shot measurement is not a measurement | [arXiv:2604.07585](https://arxiv.org/abs/2604.07585) | §21.60.3 — repeated sampling on a fixed prompt set, intervals required, vendor scores typed `third_party_report` |
| LLM product visibility is manipulable by crafted content; a single polluted page can shift generative recommender output | [arXiv:2404.07981](https://arxiv.org/abs/2404.07981); [arXiv:2606.13610](https://arxiv.org/abs/2606.13610) | §20.55.4 quarantined retrieval + source-concentration finding; ADR-U21 forbids the same tactics in our own output |
| Google spam policy defines scaled content abuse method-agnostically (many pages primarily to manipulate rankings, little value), names generative AI as a mechanism, and now governs AI Overviews/AI Mode surfaces | [Google Search spam policies](https://developers.google.com/search/docs/essentials/spam-policies) | §21.58.4 `spam_policy_check`; cadence ceilings with no publish-rate target (§21.59.5) |
| FTC applies Section 5 and the amended Endorsement Guides (16 CFR Part 255) to AI-generated advertising with no AI exemption; charged a vendor for *supplying* review-generation capability | [FTC, Operation AI Comply (2024-09)](https://www.ftc.gov/news-events/news/press-releases/2024/09/ftc-announces-crackdown-deceptive-ai-claims-schemes) | ADR-U23 synthetic-user prohibition; §21.58.2 `disclosure_lint` hard-fails endorsement/testimonial content |
| Sector regulators name AI agents as a distinct risk class — autonomous action, authority overreach, auditability gaps when actions aren't logged and reviewed ⓘ | FINRA 2026 Annual Regulatory Oversight Report (as reported) | §21.57.1 — corroborates the scoped-approval + full-action-log posture already required by §18.49's attestation ledger |
| Platform automation converges on draft-and-approve: official APIs only, browser automation prohibited, fully automated posting is the documented route to a ban; community self-promotion ratios are norms no API exposes | 2026 platform-ToS analyses and automation field guides (LinkedIn §8.2, Reddit API + subreddit norms) | §21.57.1, §21.59 — `publish_external` in `forbidden_autonomous`; community profile tracks self-promo ratio |
| Bulk-sender requirements moved from advisory to enforced: SPF+DKIM+DMARC aligned, RFC 8058 one-click unsubscribe, complaint-rate ceiling ~0.30% with ~0.10% as the practical operating target, bounce ceiling ~2%; unwarmed domains at agent volume lose placement within weeks | Mailbox-provider bulk-sender requirements (Feb 2024 onward) + 2026 deliverability field reports; thresholds carried as config with `verified_on` | §21.58.3 `deliverability_preflight` — placement thresholds tunable, consent and suppression hard-coded |
| A/B testing FDR is 18–25% at 5% significance and 28–37% at 10%, driven by ~70% true nulls rather than low power; ~1 in 5 significant interventions is ineffective in the field; two-stage designs (screen many, validate the leader) reduce it | Berman & Van den Bulte, *False Discovery in A/B Testing*, [Management Science](https://pubsonline.informs.org/doi/10.1287/mnsc.2021.4207) | ADR-U24 — two-stage screening→validation mirrors the existing vote→verify→leader shape; underpowered tests are not run |
| ~57% of experimenters p-hack by stopping at significance, raising FDR from ~33% to ~42%; continuous monitoring invalidates fixed-horizon inference without a sequential design | Berman & Pekelis, *p-Hacking and False Discovery in A/B Testing*; Johari et al., *Peeking at A/B Tests*, KDD 2017 | §21.61.3 — hash-pinned pre-registration, sequential monitoring with a pre-specified spending function, inconclusive-enters-nothing |
| Attribution: a large share of the buying journey is invisible to trackers; last-touch systematically over-credits demand capture; incrementality holdouts, self-reported attribution, and MMM are the trusted stack, multi-touch demoted to a tactical hint | 2026 attribution field reporting (dark-funnel/incrementality practitioner consensus) | ADR-U25 + §22.63.2 `attribution_typer` — only holdouts may ground a causal claim; MMM/MTA/last-touch type as `model_inference`, platform-reported as `third_party_report` |
| 88% of enterprise agent pilots never reach production; blockers: eval/observability 64%, governance 57%, model reliability 51%; the converting 12%: 94% named owner, 87% automated evals per change | Anaconda/Forrester, replicated a16z + MIT Sloan CIO panel — [compilation, 2026-04](https://www.digitalapplied.com/blog/ai-agent-adoption-2026-enterprise-data-points) | §68.1, §69 — E1 is the converting-minority profile as default; *third_party_report* grade |
| Gartner: >40% of agentic-AI projects scrapped by 2027 for operationalization, not model failure | [cited 2026](https://www.kore.ai/blog/ai-agents-in-2026-from-hype-to-enterprise-reality) | §68.1 — the substrate ladder's reason to exist |
| EU non-adopter barriers: skills 70.9%, unclear legal consequences 52.5%, data protection 48.8% | Eurostat via [SME review, 2026](https://www.omago.ai/blog/sme-ai-adoption-2026-data) | §69.1 procurement pack, §75.1 telemetry default |
| Agent-framework consolidation: MS Agent Framework GA 2026-04 (AutoGen+SK merged), Swarm archived for Agents SDK, LangGraph 1.0, CrewAI 1.0 — all orchestration SDKs, none lifecycle methodologies | [The Agent Report, 2026-05](https://the-agent-report.com/2026/05/ultimate-guide-open-source-ai-agent-frameworks/) | §68.1 layer positioning; §76.2 complements-not-competitors |
| Solo-founder economics: build barrier collapsed, distribution didn't; "<3% of bootstrapped SaaS founders crack $1.2M ARR" | [practitioner synthesis, 2026-05](https://www.buildmvpfast.com/blog/one-person-unicorn-ai-agents-solo-founder-billion-dollar-2026) | §70 — E2 centers docs 20–23, not the coding MAS; *third_party_report*, verify-at-adoption |
| MCP: donated to Agentic AI Foundation (Linux Foundation) 2025-12; ~97M monthly SDK downloads; ~9,400 public servers; Server Cards + statelessness on 2026 roadmap | [WorkOS 2026-03](https://workos.com/blog/everything-your-team-needs-to-know-about-mcp-in-2026); [Toloka 2026-05](https://toloka.ai/blog/the-future-of-mcp-enterprise-adoption/) | §71.1 — the ADR-007 transport bet, aged well |
| Agent Skills: open spec at agentskills.io 2025-12-18; ~40 compatible products; SkillsBench: mean quality 6.2/12 over 47,150 public skills, curated skills +16.2pp pass rate | [ecosystem report, 2026-06](https://agentman.ai/blog/agent-skills-ecosystem-report-2026) | §71.1, §75.2 — "catalog size is not quality"; FixtureGate is the structural answer |
| Always-valid inference (mixture SPRT) gives p-values and confidence sequences valid at **every** n, so continuous monitoring becomes a legal stopping rule; deployed at scale on a commercial A/B platform | Johari, Pekelis & Walsh, *Always Valid Inference*, [Oper. Res. 70(3), 2022](https://pubsonline.informs.org/doi/10.1287/opre.2021.2135); [arXiv:1512.04922](https://arxiv.org/abs/1512.04922) | §21.61.3 — **supersedes the alpha-spending method in the first draft** (errata §15.8-1). Implemented and empirically validated in `product_loop_tools.py` |
| EU AI Act Art. 50 applies from **2026-08-02**: 50(1) interaction disclosure, 50(2) machine-readable marking of synthetic output (provider), 50(4) human-perceivable disclosure of deepfakes and public-interest AI text (deployer). Deployers cannot discharge 50(4) via provider marking. Carve-out for assistive standard editing, to be read restrictively. Transitional window to 2026-12-02 for 50(2) on pre-existing systems | [Art. 50 text](https://artificialintelligenceact.eu/article/50/); [Commission guidance + Code of Practice](https://digital-strategy.ec.europa.eu/en/policies/guidelines-transparency-ai-generated-content) | §21.58.2 — an operator running P3 into the EU is a **deployer** with a live obligation from August |
| C2PA v2.3 (Jan 2026) extended Content Credentials to **manifests for unstructured text**, i.e. LLM output; no single marking technique meets all four Art. 50(2) criteria, so the Code of Practice prescribes none. Practical limits: platforms strip metadata, no free certificate tier | [C2PA specifications](https://spec.c2pa.org/); EU Code of Practice on marking and labelling | §21.58.2 — the concrete mechanism behind the machine-readable-mark check; sidecar manifests for web text |

**Watch list:** superseded by doc 16 §40.6 (phase-transition theory and the OWASP mapping are resolved and shipped; remaining items tracked there).

## 7. Publication readiness (GitHub)

Verified: README is a working entry point with reading order and an architecture diagram; all citations are inline links to primary sources; no copyrighted text is reproduced (original prose throughout); known limitations are stated (§11.21, §15.5 residuals); estimates are explicitly Day-0-calibrated, not promised. Shipped with the bundle: `LICENSE` (MIT, neutral holder), `CONTRIBUTING.md`, `SECURITY.md` (OWASP LLM Top 10 : 2025 mapping), and the cited methodology reference now included at `archive/external-reference-ai-mas-methodology.md` — all internal citations resolve. Doc 16 extends the set with scaling/continuous-operation design and the adopted-technique record (GEPA, CaMeL posture, cascades) under the same citation calibration. Docs 20–23 add the outer product loop under a stricter version of the same rule — the claim schema of §20.53 is that rule made executable, and the framework now holds its own artifacts to it. Where the subject is platform behavior nobody publishes rigorously (deliverability thresholds, enforcement posture), the numbers are carried as config with a `verified_on` date and are never constants in code, matching the §17.43 platform-limit discipline. **Remaining owner decisions — see `PUBLISHING.md`:** confirm or swap the license/holder, and decide author-name handling (keep as attribution vs anonymize).

---

**Residual honest limitations** (inherited from §11 Part 21, plus upstream-specific): the 80-confidence threshold and voter counts remain engineering defaults pending Day-0/U-track data; `root_cause_stage` labeling accuracy bounds metric 4 until the audit queue accumulates; estimate calibration is empty at cold start by design; and no gate can make a human read what they acknowledge — U1/U3 are designed to make the artifact small enough that they will.

## 8. Errata (product loop)

**§15.8-1 — sequential monitoring method, doc 21 §61.2.** The first draft specified an O'Brien–Fleming alpha-spending function. That is a *group*-sequential method assuming a small number of pre-specified interim looks; an agent monitoring continuously has none. Corrected to always-valid inference via the mixture SPRT (Johari/Pekelis/Walsh). `check_experiment` now emits `group_sequential_for_continuous` when a design specifies alpha-spending with continuous monitoring, so the superseded choice is caught rather than merely deprecated.

**§15.8-2 — sequential inference is not free, and the docs now say how much.** Measured in the companion script's self-test: with τ tuned to the absolute MDE, always-valid inference needs **≈1.17×** the fixed-horizon per-arm sample, stable across baselines from 2% to 20%; mistuning τ by 4× costs up to ≈1.5×. A design sized fixed-horizon but monitored continuously is flagged (`power_ignores_sequential_cost`). Empirical type-I error under adversarial continuous peeking: **1.3% for mSPRT vs 37.1% for a naive fixed-horizon test** at nominal α=0.05 — the p-hacking failure of §21.61.1 reproduced in simulation.

**§15.8-3 — overflow in the shipped likelihood ratio.** Found by running the code rather than reading it: at large n with a real effect the mSPRT exponent exceeds float range and `math.exp` raises mid-experiment. The statistic is now computed in log space. Recorded here because "the code was written but never run" is the class of defect this framework exists to catch, and it applied to the framework's own tooling.

**§15.8-4 — superlatives escaped the substantiation check.** `check_substantiation` originally only examined sentences containing a capability verb or a number, so "We are the fastest exporter on the market" was skipped entirely. Superlatives are now a trigger in their own right, and are flagged whether or not they match a register entry — a comparative is an assertion about products we do not control, so an unmatched superlative is two findings, not zero.
