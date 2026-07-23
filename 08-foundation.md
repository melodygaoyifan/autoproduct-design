# 08 — Foundation

*Problem statement, research foundation, and architecture overview for `autoproduct`. Part A of three authoritative design documents.*

---

## Part 0 — Preamble

### 0.1 What this document does

Three things: state the problem `autoproduct` solves, synthesize the research that grounds its design, and establish the architectural shape. Everything specific — agents, state schema, code — lives in `09-system-design.md`. Everything prescriptive about building — daily tasks, code snippets, success criteria — lives in `10-implementation-plan.md`.

After reading this document the reader should be able to:

1. Explain what `autoproduct` covers and does not cover
2. Cite the key empirical findings that motivate specific design choices
3. Draw the four-layer architecture from memory
4. Judge whether a proposed change is consistent with the design philosophy

### 0.2 How to read

- **Part 1** (problem statement) is essential context. Read once.
- **Part 2** (research foundation) is reference material. Skim on first read; return when a design decision feels arbitrary.
- **Part 3** (architecture overview) is load-bearing. The diagrams should be reproducible from memory after reading.

Code in Part 3 is architectural illustration. Real code lives in `09-`.

### 0.3 Versioning

This is a snapshot. When the design changes materially, a new numbered document supersedes or extends this one. Documents are not edited in place.

---

## Part 1 — Problem statement

### 1.1 What autoproduct does

`autoproduct` is a multi-agent system that covers four stages of the software development cycle: code review, test, deployment review, and production maintenance. Given a PR (or, for maintenance, a production signal) as input, it:

1. **Code Review.** Analyzes the diff through 6+ heterogeneous specialist voters in parallel; runs deterministic code-analysis tools (SAST, secret scanning, dependency audit, symbol-graph analysis); independently verifies every candidate finding before reporting; synthesizes findings through a Leader agent.
2. **Test.** Runs adversarial mutation testing in an isolated git worktree; generates UI tests for new user flows; produces a structured test report.
3. **Deployment Review.** Reviews CI/CD config, infrastructure-as-code, migration scripts, and canary analysis specifications; integrates with Argo Rollouts / Flagger CRDs to evaluate canary metrics; emits ROLLBACK / PROMOTE / ESCALATE_DEPLOY_RISK / ESCALATE_MIGRATION_DESTRUCTIVE verdicts (full taxonomy in §09.11).
4. **Production Maintenance.** Triages incoming Sentry/Datadog/PagerDuty signals; correlates incidents with recent PRs to localize regressions; root-cause investigators explore parallel hypotheses; generates fix-PRs that re-enter the Code Review stage; learned-skill registry accelerates recurring incident classes (full taxonomy in §09.12).

Across all four stages, `autoproduct` posts structured artifacts (PR comments, evidence ledgers, incident reports), respects a uniform 3-fail-then-escalate autonomy pattern, and accumulates structured signals into a project constraint file (`CLAUDE.md`) and a learned-skill registry through a weekly compounding loop.

Scope boundary: `autoproduct` covers the **review-side closure of the SDLC** — every stage where autoproduct acts is one where the action is to *review*, *generate tests*, *evaluate against policies*, or *propose patches via PR*. The system never auto-merges, never auto-deploys to production, and never auto-mutates production state outside a small allowlist of pre-approved guardrail actions (§09.12.6). Discovery, Plan, Spec, and Coding stages remain out of scope (Claude Code's `/plan` and `/ultraplan` cover those well; pair if needed).

### 1.2 Why this system

Four real problems motivate building it rather than using an existing tool.

**Problem 1: AI-generated code fails in systematic ways that generic review tools miss.** [Columbia DAPLab](https://daplab.cs.columbia.edu/general/2026/01/08/9-critical-failure-patterns-of-coding-agents.html) ("9 Critical Failure Patterns of Coding Agents", SOSP 2025 workshops, blog Jan 2026) documented nine failure patterns observed in every one of five frontier coding agents tested (Cline, Claude Code, Cursor, Replit, V0). Independent 2025–2026 security reports ([Apiiro](https://apiiro.com/), [CodeRabbit analyses](https://www.coderabbit.ai/), [SusVibes (arXiv:2512.03262)](https://arxiv.org/abs/2512.03262)) consistently show AI-generated code carries measurably elevated vulnerability rates relative to human-written baselines. Generic linters and human reviewers are not calibrated for these specific failure patterns. A system designed to hunt them is.

**Problem 2: Cross-file consistency is a major real-failure category, and single-file review misses it.** Multiple independent evaluations of production code review agents converge on cross-file consistency being a large fraction of real-world LLM review misses. DAPLab's pattern #8 ("Codebase Awareness and Refactoring Issues") is a specific named failure: agents refactor a function signature without updating the callers because they only see the file in the diff. A review system that reads only the diff misses this category by design.

**Problem 3: Same-family model review has shared blind spots.** Different model families exhibit different failure modes, which is the entire design premise behind Andrej Karpathy's [llm-council](https://github.com/karpathy/llm-council) (Nov 2025) assembling councils across OpenAI, Anthropic, Google, and xAI. A system built on one model family is systematically blind to its family's failure modes. Using multiple families is not a marginal enhancement; it is the structurally-required design.

**Problem 4: Static review tools don't accumulate.** Every review is independent. Lessons from past reviews are not converted into constraints for future reviews. [ACE: Agentic Context Engineering (arXiv:2510.04618)](https://arxiv.org/abs/2510.04618) (Stanford/SambaNova, October 2025) formalizes the insight: the highest-leverage optimization target is often the scaffolding (project constraints, agent skills, evaluation criteria), not the model weights. A review system that accumulates structured signals into its own constraints compounds; one that doesn't, stagnates at initial capability.

### 1.3 Engineering philosophy

Seven principles. Each is grounded in specific research synthesized in Part 2. Every subsequent design decision validates against these.

**Principle 1: Deterministic control flow, probabilistic analysis.**
The orchestrator is a deterministic Python state machine. LLMs live inside agents as data transformers producing structured outputs that Python consumes. LLMs do not decide which agent runs next, when to escalate, or whether to retry. Those decisions are code. Grounded in: the broader practitioner consensus emerging in 2025–2026 production agent writeups that deterministic control flow plus LLM-in-the-loop produces more debuggable and reliable systems than LLM-orchestrated flow, and in the specific design of LangGraph 1.0 itself, which explicitly separates graph topology (code) from node behavior (LLMs).

**Principle 2: Hooks enforce, skills guide.**
Anything that must happen regardless of LLM output is a hook — deterministic code with the power to block (exit-code-2 pattern). Anything the agent should consider is a skill — LLM-readable instructions the model may or may not follow. When in doubt, err toward hook. This mirrors the pattern Claude Code itself uses: hooks are the deterministic enforcement layer (e.g., pre-commit lint, test gates); skills are the soft guidance the model consults.

**Principle 3: Parallel voting over sequential debate for opinion tasks.**
When multiple agents form opinions about the same input, they run in parallel and produce independent findings that a leader synthesizes. No agent reads another agent's output in the main flow. Grounded in: [NeurIPS 2025 Spotlight "Debate or Vote"](https://arxiv.org/abs/2508.17536) — majority voting accounts for most gains attributed to multi-agent debate; debate induces a martingale over belief trajectories and does not improve expected correctness. Exception: ground-truth-backed adversarial loops (mutation testing) are not opinion-based and are empirically positive.

**Principle 4: Heterogeneous models are structurally required.**
Every voter runs on a different model family (Claude, GPT, Gemini, Grok). Same-family voting requires explicit engineering-judgment justification in the commit or PR message. Grounded in: §2.2.3 — different model families exhibit different failure modes, and the ensemble gain from cross-family review is the design purpose (Karpathy's llm-council assembles councils from OpenAI, Anthropic, Google, and xAI precisely for this reason).

**Principle 5: The system compounds.**
Every review emits structured signals. A weekly compounding loop aggregates signals and proposes updates to the project's constraint file via pull request for human approval. Static capability is not the goal; accumulation is. Grounded in: ACE (Agentic Context Engineering, arXiv:2510.04618) — the highest-leverage optimization target is often the scaffolding (constraints, accumulated knowledge), not the model weights. The compounding loop is treated as a first-class component, not an optional extension, but scoped conservatively (only `CLAUDE.md` updates, all human-reviewed) because reward-hacking is a known failure mode of self-updating context systems.

**Principle 6: Communicate via structured documents, not dialogue.**
Agents talk to each other through typed state and structured artifacts (YAML findings, evidence ledgers, test reports), never through free-form natural-language exchanges. This is the lesson of MetaGPT vs ChatDev — the same models perform substantially better when forced to express decisions as structured documents rather than chat. Concretely: voters emit `VoterOutput` envelopes (§09.4.3), the Leader emits a structured verdict + findings list, HITL Issue bodies are template-rendered (§09.8.3), the per-voter log is YAML (§09.8.5), the evidence ledger is a markdown table (§09.9.5.1). The system has no "agent A messages agent B" pattern — that absence is intentional. When natural language is used (voter prompts, suggested fixes), it lives inside structured fields, never as a free-form channel between agents.

**Principle 7: Spec is first-class. Harness enforces. MCP transports.**
Every voter has a machine-checked YAML frontmatter spec declaring inputs, outputs, MCP servers/tools allowlist, fixture requirements, and risk ceiling. The harness validates voter specs at load time, runs fixture gate at registration time, and runtime-checks input/output contracts on every voter invocation. Tools live in MCP servers (subprocess-isolated, dynamically discovered, RBAC-scoped) — the protocol is internal in v1.0.0 (no external MCP exposure due to supply-chain risk per [arXiv:2511.20920](https://arxiv.org/abs/2511.20920) and CVE-2025-6514) and the architecture positions us for v1.1.0 external exposure with substantially reduced refactor effort (server internals unchanged; OAuth + HTTP transport + gateway RBAC are additive ~144hr work — see §17.1 for the honest cost). Module-level specs (`.mas/specs/{module}.spec.yaml`) declare invariants and forbidden patterns that Code Review checks against, implementing the [Augment Code spec-driven prevention pattern](https://www.augmentcode.com/guides/ai-technical-debt-compounds-spec-driven-development). Full architectural treatment in `11-ultimate-architecture.md`.

### 1.4 Non-goals

To prevent scope creep, the following are explicitly **not** goals:

- **Auto-merge to main.** The system never merges PRs. Human is always the final gate. (Same for compound-loop CLAUDE.md updates and for fix-PRs generated by the Maintenance stage — a fix-PR is reviewed like any other PR before merge.)
- **Auto-deploy to production without human approval.** The Deployment Review stage (§09.11) reviews and recommends; the human (or a CI/CD policy gate) executes. Within the trust-tier framework (§09.11.5), *staging* deploys can become autonomous after a sustained track record of correct decisions; *production* deploys remain human-gated per deploy as a hard architectural boundary, not a tunable threshold.
- **Auto-hotfix in production without human approval.** Maintenance (§09.12) can propose a fix-PR (which then re-enters Code Review), can recommend a known-safe action within pre-approved guardrails (e.g., scale a service up by one replica), and can execute that recommendation autonomously *only* if it falls inside the explicit guardrail allowlist for the project. Anything outside the allowlist escalates per the 3-fail-then-human pattern.
- **Auto-rotate secrets, run destructive migrations, modify auth/billing.** L4 tools (§09.7.1) are never exposed to any voter or maintenance agent.
- **Autonomous feature code generation.** The system reviews, generates tests, and generates fix-PRs; it does not generate feature code from a spec.
- **Discovery / Plan / Spec / Coding stages of the SDLC.** Out of scope. Pair with separate tools or Claude Code's `/plan` and `/ultraplan` for those stages. `autoproduct` is the *review-side closure* of the SDLC, not the full SDLC.
- **Enterprise features.** No multi-tenancy, no SSO/SAML, no attestation ledger, no authorization fabric, no SOC 2 posture.
- **Cross-language first-class support.** Python is primary. TypeScript is architecturally supported (tools abstract on language) but not implemented. Other languages out of scope.
- **Self-modifying code.** The compounding loop proposes changes via PRs for human review. It never directly modifies the harness, skills, or constraint files.
- **Beating any specific benchmark.** Benchmarks exist for regression detection, not marketing claims.
- **SaaS / productization.** The system is personal infrastructure and an open-source reference implementation.
- **Free-form inter-agent dialogue / Multi-Agent Debate (MAD).** Voters do not message each other. Communication is exclusively structured, single-direction, and bounded (tool output → voter, voter → leader, finding → verifier, voter → peer-scorer in deep mode, signal → triage → root-cause → fix-PR generator). Justified by the "Debate or Vote" finding ([Choi et al., NeurIPS 2025 Spotlight, arXiv:2508.17536](https://arxiv.org/abs/2508.17536)) and detailed in §1.5.

### 1.5 On voting vs communication — why no inter-agent dialogue

A natural question for any multi-agent code review system: should voters talk to each other? Should they debate findings, refine each other's reasoning, build consensus through discussion? `autoproduct`'s answer is **no**, and the answer is load-bearing — it shapes the state machine, the cost model, and the verdict logic.

**The empirical case for voting over debate.** Choi, Zhu, and Li's [Debate or Vote (NeurIPS 2025 Spotlight, arXiv:2508.17536)](https://arxiv.org/abs/2508.17536) decomposed Multi-Agent Debate (MAD) into two components — ensembling (multiple agents producing answers) and inter-agent communication — and isolated each empirically across 7 benchmarks. The result: **ensembling produces nearly all the performance gain; communication adds little.** Their theoretical framework proves debate forms a martingale over agents' belief trajectories, meaning expected correctness does not improve through dialogue alone.

[Kaesberg et al. 2025 (arXiv:2502.19130)](https://arxiv.org/abs/2502.19130) ran the same analysis specifically on voting vs consensus protocols across 7 decision rules: voting outperformed consensus by 13.2% on reasoning tasks. Code review is a reasoning task.

**The mechanism case against dialogue.** When voters communicate, three things go wrong:

1. **Conformity bias collapses the ensemble.** [AgentReview (EMNLP 2024 Oral, arXiv:2406.12708)](https://arxiv.org/abs/2406.12708) measured a 27.2% reduction in rating standard deviation after a single rebuttal round — agents converge regardless of who's right. The whole point of running 6 heterogeneous voters is that they have different blind spots; making them talk reintroduces the homogeneity we deliberately fight.

2. **Sycophancy compounds in same-family scenarios.** When Claude reviews Claude-generated code (the AgentHire case), the bias toward "this looks fine" is already strong. Adding inter-agent communication where Claude voters can "agree" with each other amplifies it — which is exactly why [Karpathy's llm-council](https://github.com/karpathy/llm-council) anonymizes responses and assembles councils across providers.

3. **Cost scales linearly with rounds.** Standard mode at $0.30-0.80 per review (§9.4.1) becomes $1.50-3.00 with 3 rounds of debate. The marginal accuracy gain — per the empirical literature — is approximately zero.

**What we do have, that looks like communication but isn't.** Five forms of structured, single-direction "communication" exist in the design and are necessary:

| Channel | Direction | What it isn't |
|---|---|---|
| Tool output → Voter | One-way data feed | Not dialogue; voter cannot "ask" Semgrep for clarification |
| Voter → Verifier (§4.6) | One-way; verifier sees only finding + diff | Not negotiation; verifier never relays back to original voter |
| Voter → Leader (§4.4.7) | Many-to-one synthesis | Not consensus-building; Leader decides unilaterally |
| Voter → Peer-scorer (deep mode, §5.4.6) | One-way scoring, anonymized | Not editing; peer cannot rewrite original voter's finding |
| Per-voter log → Human → CLAUDE.md (§8.4) | Asynchronous, human-mediated | Not LLM-to-LLM; the human is the bandwidth-limiter and reward-hack defense |

Each channel is structured (typed YAML), bounded (one hop), and serves a synthesis function rather than a deliberative one. None of them is "Voter A messages Voter B."

**When would dialogue become valuable?** Two scenarios — neither applies here:

- *Open-ended creative tasks* where idea collision produces novel solutions (e.g., research ideation, architectural brainstorming). Code review is convergent: there's a finite set of bug categories and the goal is independent coverage, not synthesis.
- *Reasoning tasks with low base accuracy* (~30%) where debate can rescue mistakes through cross-agent error correction. Code review baseline is much higher (single SOTA models clear 50% precision); the Free-MAD finding that "noisy generations actively mislead other agents, propagating errors across rounds" is the dominant risk, not the upside.

**Operational guarantee.** No graph node in §5.4 implements message-passing between voters. `vote_node` runs voters in parallel with no shared mutable state during execution. `peer_review_node` is read-only scoring of completed findings. `verify_node` is single-finding-in, single-verdict-out. The state machine is structurally incapable of supporting agent dialogue without a graph rewrite — which is the right place for that rigidity to live.

### 1.6 Completion criteria

`autoproduct` is complete when the following are all true:

1. **End-to-end pipeline works.** `autoproduct review <PR-URL>` on a real PR produces structured findings, a PR comment, and YAML artifacts in under five minutes.
2. **Four gates are operational.** Definition of Ready gate (before INIT), Test Gate (after adversarial test), Review Gate (HITL on `ESCALATE` or 3× voter failure), and Rollback path (when a compounding-loop merge causes benchmark regression).
3. **Benchmark baseline is committed.** Review recall ≥ 40% and precision ≥ 50% on a 20-instance subset of a real-world PR benchmark (chosen at implementation time; see §10 Week 5). Reproducible via `make bench-fast`.
4. **HITL loop tested.** Injected failure triggers `interrupt()`, GitHub Issue opens, human response resumes execution correctly.
5. **Mutation testing active.** `mutmut` runs on every PR in standard mode; surviving mutants become taxonomy signals. Generated tests are written to an isolated git worktree, not the main checkout.
6. **UI testing active for frontend projects.** When `codebase_profile.ui.framework` is set (e.g., React), Playwright tests in the repo are run against the PR; UI-specific voter or finding category is populated.
7. **Test report is structured.** The POST stage emits a structured test report covering: unit, mutation, coverage, security, dependency, integration, UI, performance — each section present or marked N/A.
8. **Per-voter log is populated.** Each voter invocation produces an entry in `.mas/voters/{voter_name}/log.yaml`; failures, HITL overrides, and human-marked-incorrect findings are logged for later inspection.
9. **Compounding loop operational.** Weekly cron proposes a `CLAUDE.md` update PR; the PR format is readable and actionable. Benchmark regression auto-triggers rollback.
10. **Deep-dive mode usable.** `autoproduct deep <PR-URL>` runs the full pipeline with mutation testing, UI test generation, and peer review enabled.
11. **At least one project integrated.** A real codebase uses `autoproduct` for real PRs end-to-end.
12. **Design docs public.** Documents 08–10 are on GitHub with an archive of the evolution.

### 1.7 Anti-hallucination charter

`autoproduct` makes claims about other people's code. The cost of a wrong claim — a hallucinated bug that doesn't exist, a fabricated CVE, a made-up API — is borne by the PR author, who has to spend time disproving it. The cost of a missed real issue is also bad but is the same cost as having no review at all. So the asymmetric design priority is: **a voter that doesn't know is more valuable than a voter that confidently makes things up.**

This charter binds the design of every voter, every tool, and every state contract. Each rule below has concrete cross-references into the specification.

1. **No guessing.** If a voter lacks the context to judge, it returns `BLOCKED_MISSING_CONTEXT` with the missing source list — never an empty findings list, never a fabricated finding. Schema in §09.4.3. Leader behavior on BLOCKED voters in §09.4.4.7.
2. **Evidence required.** Every finding has a `file_path`, `line_start`, `line_end`, `evidence` text quoting the actual code, and a `taxonomy_hint` linking to either DAPLab patterns or a deterministic-tool match. Findings without locatable evidence are filtered by the Leader. Evidence ledger in §09.9.5.1.
3. **Source grounding.** Voters read real code via tools (`read_file`, `grep`, `tree_sitter_query`) before judging. The voter prompt template explicitly forbids "from memory" claims — see voter base class in §09.4.2 and tool registry in §09.7.1.
4. **No fake APIs.** When a voter references a function, package, or endpoint, the reference must come from the diff, the repo's `read_file` output, or a deterministic tool result — never from the model's prior. Cross-file checks live in the Repo Graph voter (§09.4.4.5), which uses tree-sitter + pyright, not LLM memory.
5. **No self-approval.** Leader (synthesizer) is a different model invocation from any voter. Voters cannot edit each other's findings; peer review (§09.5.4.6) is an optional re-scoring step that never rewrites. Adversarial test generation (§09.5.4.9) writes to an isolated worktree, never the main checkout.
6. **Tool safety.** Tool registry enforces risk-level ≤ 2 for any voter-callable tool (§09.7.1). Levels 3-4 (modify auth, schema, secrets, deploy) do not exist as voter tools. The structural impossibility is the safety mechanism — not policy.
7. **Untrusted content stays as data.** PR diff, code comments, commit messages, and tool output are wrapped in `<untrusted_*>` tags in voter prompts (§09.4.2.2). Prompt injection cannot escalate a voter to a destructive action because no destructive action is reachable.
8. **State discipline.** Every super-step writes to both the LangGraph checkpointer and the YAML mirror (§09.6). Per-voter log appended at POST (§09.8.5). Evidence ledger written at POST (§09.9.5.1). The dual-write means a crash cannot leave the system in an indeterminate state.
9. **Test before done.** A verdict of `APPROVE` requires Gate 2 (Test Gate) pass: unit tests, coverage threshold, mutation score threshold, UI tests if framework configured (§09.5.4.10). Mutation testing in deep mode catches "tests that pass but don't actually test anything."
10. **Human escalation.** Three voter retries failed → HITL (§09.5.3 routing). Two BLOCKED voters → REQUEST_CHANGES with missing-source request. Three BLOCKED voters → ESCALATE_MISSING_CONTEXT (§09.4.4.7 verdict taxonomy). Safety-removal pattern → immediate ESCALATE_SECURITY_RISK regardless of other findings.

These ten rules are the operational contract for every component. They are not aspirational — when a design decision in 09 or 10 violates one of them, that decision is wrong and gets revised.

### 1.8 SDLC stage scope and uniform autonomy contract

`autoproduct` covers four contiguous stages of the SDLC, each implemented as a stage MAS following the same architectural template. The motivation for covering deployment and maintenance — and not stopping at code review + test — is that AgentHire is a customer-facing product: a regression that survives review still hurts users if it ships, and a production incident that goes uninvestigated still hurts users until it is resolved. Catching bugs at code review is necessary but not sufficient.

**Four stages, one autonomy contract.** Every stage runs on the same core pattern:

```
analyze → tools → vote → verify → leader → gate → next stage (or escalate)
```

with the same 3-fail-then-escalate-to-human rule (§1.5 codified) applied uniformly:

- **Code Review (§09.4)** — 3 voter failures or 3 BLOCKED → ESCALATE_VOTER_FAILURE / ESCALATE_MISSING_CONTEXT
- **Test (§09.5.4.9-10)** — 3 mutation-loop iterations without hitting threshold → ESCALATE_TEST_INADEQUATE
- **Deploy Review (§09.11)** — 3 canary-analysis failures or 3 guardrail-violation hits → ESCALATE_DEPLOY_RISK / ESCALATE_MIGRATION_DESTRUCTIVE
- **Maintenance (§09.12)** — 3 root-cause-investigation passes below confidence threshold → ESCALATE_INCIDENT_UNRESOLVED; 3 guardrail-blocked auto-actions → ESCALATE_MAINTENANCE_BOUNDARY

The 3-fail rule applies *per stage*, not globally — a deploy review can escalate without affecting the upstream code review's verdict. This isolation matters because each stage has different latency budgets (review = minutes, deploy = hours of canary observation, maintenance = on-call response time).

**Trust tiers, not autonomy levels.** Within the autonomy contract, each stage has a configurable trust tier per the framework in [arXiv:2508.11867 (AI-Augmented CI/CD Pipelines)](https://arxiv.org/abs/2508.11867):

| Tier | Behavior | What can be set to this tier |
|---|---|---|
| **Insight** | Surface findings only, never act | Default for all stages on day 1 |
| **Assistive** | Recommend action; human approves before execution | Code Review (always, by design); fix-PR proposal in Maintenance |
| **Autonomous-within-guardrails** | Execute action if it falls inside the policy allowlist; otherwise escalate | Test Gate (kicks back PRs that fail thresholds); compound-loop CLAUDE.md proposal (auto-opens PR, but PR still needs human merge); staging deploy after track record; pre-classified maintenance actions (e.g., scale-up by one replica) within explicit allowlist |

**Production deploys and any L4-tool action stay at Assistive forever.** This is a hard architectural ceiling — the trust tier for "deploy to production" cannot be configured to `autonomous`. Same for any action that touches secrets, runs migrations, modifies auth/billing, or modifies the harness itself. The structural impossibility is the safety mechanism, mirroring the tool risk-level enforcement in §09.7.1.

**The flow view in §3.3 reflects this scope:** four stage MAS, six explicit gates (Definition of Ready → Test → Review/HITL → Rollback for code; Deploy Review → Production Health for deploy/maintenance), with HITL crossings at every stage boundary.

---

## Part 2 — Research foundation

Literature synthesis. Each cited work is tied to a specific design choice. Skim first; return when justifying a decision.

Calibration note on this section: citations use inline hyperlinks in practitioner style rather than academic form. Only references and numbers that have been verified against their primary source are included. Where a claim reflects industry consensus rather than a specific named paper, the phrasing reflects that (e.g., "recent empirical work suggests..." instead of a fabricated citation).

### 2.1 Multi-agent code review landscape (April 2026)

**[Anthropic Claude Code Review](https://code.claude.com/docs/en/agent-teams)** (launched March 9, 2026). Multi-agent PR reviewer in research preview for Claude Team and Enterprise customers. Runs multiple specialized agents in parallel, verifies and ranks findings, posts ranked comments to GitHub. Per [The New Stack's launch coverage](https://thenewstack.io/anthropic-launches-a-multi-agent-code-review-tool-for-claude-code/) and [InfoQ](https://www.infoq.com/news/2026/04/claude-code-review/): Anthropic's internal deployment moved substantive review comments from 16% of PRs to 54%; fewer than 1% of findings were marked incorrect by engineers; cost is ~$15–25 per review, typical completion ~20 minutes. Configuration via `REVIEW.md` for review criteria and `CLAUDE.md` for project context.

Architectural details that are publicly confirmed: logic-aware, not style-focused (explicit product choice to reduce false positives); agents run in parallel; does not approve PRs (human gate preserved). Specifics of how many agents, which specialties, and how findings are ranked are not documented publicly. This is the current SOTA reference point for the category.

Relative to autoproduct's design space: Claude-only (no heterogeneous models); closed-source; uses Anthropic's own [Agent Teams](https://code.claude.com/docs/en/agent-teams) orchestration infrastructure which itself is marked experimental. autoproduct's departure points are heterogeneous models, open source, and an explicit compounding loop.

**Community OSS and patterns:** multiple independent Claude Code skills and subagent sets for code review exist (several listed under the [llm-council topic on GitHub](https://github.com/topics/llm-council)), converging on similar parallel-specialist patterns. Direction is validated across independent teams.

### 2.2 Key empirical findings

Each finding below maps to a specific design choice.

#### 2.2.1 DAPLab 9-pattern vibe-code failure taxonomy

Columbia's [DAPLab](https://daplab.cs.columbia.edu/) (Data, Agents, and Processes Lab) published the [9 Critical Failure Patterns of Coding Agents](https://daplab.cs.columbia.edu/general/2026/01/08/9-critical-failure-patterns-of-coding-agents.html) (January 2026 blog; research presented at SOSP 2025 workshops). Team iteratively built 15+ applications with 5 frontier coding agents (Cline, Claude Code, Cursor, Replit, V0) and documented hundreds of failures into 9 patterns, each observed across every agent tested:

| # | Pattern |
|---|---|
| 1 | Presentation & UI Grounding Mismatch |
| 2 | State Management Failures |
| 3 | Business Logic Mismatch |
| 4 | Data Management Errors |
| 5 | API & External Service Integration Failures |
| 6 | Security Vulnerabilities |
| 7 | Repeated Code |
| 8 | Codebase Awareness & Refactoring Issues |
| 9 | Exception & Error Handling |

DAPLab and [related commentary](https://towardsdatascience.com/the-reality-of-vibe-coding-ai-agents-and-the-security-debt-crisis/) (Columbia researcher writeup, Feb 2026) identify a specific failure mechanism that runs across the taxonomy and is particularly load-bearing: **LLMs optimize for acceptance**. The simplest way to make an error message go away is often to remove the safety check that caused it — validation, authentication, rate limit, etc. This "safety removal" pattern is the single highest-priority signal for a code reviewer to catch.

**Design consequence:** Each voter's skill explicitly targets a slice of the taxonomy. Correctness Voter: #2, #3, #4, #9. Security Voter: #6 plus the safety-removal meta-pattern. Context Voter: #7, #8. The mapping appears explicitly in each voter's skill definition (§09.4).

#### 2.2.2 Cross-file consistency is a dominant real-world failure mode

Multiple independent sources converge on cross-file consistency being a large fraction of real-world LLM code review misses — a review system that reads only the diff misses this category by design. Specific examples from practice: DAPLab's pattern #8 ("Codebase Awareness and Refactoring Issues") documents agents breaking callers because they refactored a signature without updating dependents. Evaluations of production code review agents (including Anthropic's internal data) consistently show cross-file breakage as a significant defect category.

The exact percentage breakdown varies by benchmark and is not pinned to a single canonical number here.

**Design consequence:** Dedicated Repo Graph Voter (§09.4) uses tree-sitter and pyright to trace cross-file symbol references. This is the single highest-leverage addition over a file-level-only review pipeline.

#### 2.2.3 Cross-model review catches bugs same-family review misses

Heterogeneous model families exhibit different failure modes. Running review agents across multiple families (rather than multiple instances of one) produces ensemble gains that single-family review cannot. This is consistent with [Andrej Karpathy's llm-council project](https://github.com/karpathy/llm-council) (November 2025), which explicitly assembles councils from OpenAI, Anthropic, Google, and xAI precisely to get cross-family diversity, and with Anthropic's own design choice for Claude Code Review to run multiple specialists rather than a single reviewer.

**Design consequence:** The voter roster in §09.4 uses multiple model families (Claude, GPT, Gemini, Grok). Same-family voting requires explicit engineering-judgment justification in the commit or PR message.

#### 2.2.4 Majority voting dominates debate for opinion tasks

["Debate or Vote: Which Yields Better Decisions in Multi-Agent LLMs?"](https://arxiv.org/abs/2508.17536), Choi / Zhu / Li, NeurIPS 2025 Spotlight. The authors disentangle Multi-Agent Debate (MAD) into two components — majority voting and inter-agent debate — and measure each independently across seven NLP benchmarks. Key finding from the abstract:

> Majority Voting alone accounts for most of the performance gains typically attributed to MAD.

They further prove theoretically that debate induces a martingale over agent belief trajectories, meaning debate alone does not improve expected correctness. Wins credited to "agents arguing productively" are wins from ensembling N independent opinions. Code: [deeplearning-wisc/debate-or-vote](https://github.com/deeplearning-wisc/debate-or-vote).

**Design consequence:** Voters run in parallel and produce independent findings. No cross-voter conversation in the main flow. Leader synthesizes but does not orchestrate a debate.

**Exception:** the mutation-testing adversarial loop (§2.2.6) has ground truth and is not opinion-based. The NeurIPS finding addresses opinion-forming, not ground-truth-backed feedback, and does not apply there.

#### 2.2.5 Anonymized peer review pattern

[karpathy/llm-council](https://github.com/karpathy/llm-council) (Andrej Karpathy, November 2025) implements parallel opinions → anonymized peer review → chairman synthesis. Models are queried in parallel; then each model sees the others' responses with identities stripped (replaced by "Response A/B/C…"), and ranks them; finally a designated Chairman model produces the synthesis. Anonymization prevents models from deferring to identifiable "bigger" models.

**Design consequence:** Optional peer-review stage (§09.5) between independent voting and Leader synthesis. Voters see other voters' findings anonymized and re-score them; voters cannot retroactively edit their own findings during peer review. Known risk: across heterogeneous model families, stylistic fingerprints may leak through anonymization — to be tested empirically at implementation; fallback is to disable peer review in heterogeneous mode if leakage is observed.

#### 2.2.6 AdverTest adversarial mutation-testing loop

["Test vs Mutant: Adversarial LLM Agents for Robust Unit Test Generation"](https://arxiv.org/abs/2602.08146) (AdverTest, February 2026). Two agents in an adversarial loop: a test-case generator and a mutant generator. The mutant generator creates program mutations that evade the current test suite; the test generator writes new tests to kill surviving mutants. Iteration continues until coverage and mutation score plateau.

Results on Defects4J with DeepSeek V3.2: **66.63% fault detection rate**, compared to 61.38% for HITS and 40.80% for EvoSuite — an 8.6% relative improvement over the best prior LLM-based method and 63.3% over search-based methods. Statistical significance confirmed (McNemar's test, p < 0.01). Ablation confirms both the adversarial loop and mutant-guided feedback are load-bearing.

**Design consequence:** Mutation testing is a first-class phase (§09.4, §09.7). Runs on every PR in `standard` mode. The mutant generator is [`mutmut`](https://mutmut.readthedocs.io) — deterministic, compiler-backed, not an LLM. The LLM side writes tests to kill surviving mutants.

Why this is consistent with §2.2.4: ground truth is "does mutation survive." Objective, compiler-checked fact, not an opinion. The NeurIPS finding about debate applies to opinion-forming; it does not apply here.

#### 2.2.7 Context as an evolving playbook — the compounding frontier

[ACE (Agentic Context Engineering), arXiv:2510.04618](https://arxiv.org/abs/2510.04618), Zhang et al., Stanford/SambaNova, October 2025. Treats context as an evolving playbook that accumulates, refines, and organizes strategies through generation, reflection, and curation. The key insight is that the highest-leverage optimization target is often the scaffolding — instructions, constraints, accumulated knowledge — not model weights. ACE demonstrates +10.6% on agent benchmarks and +8.6% on finance benchmarks, with a smaller open-source model matching top-ranked production agents on AppWorld when using an evolved playbook.

ACE and related work also document a specific failure mode for automated context-updating systems: **reward hacking and context collapse**. Monolithic LLM-driven rewrites can cause the context to drift toward shorter, less informative summaries over time; and if an evaluation metric is gameable, LLMs can learn to update the context in ways that game the metric rather than improve real capability.

Precedent for humans-in-the-loop on context updates: Anthropic's own research on reward tampering documents that LLMs can learn to game evaluation mechanics, which motivates keeping human review on the loop for any self-updating context system.

**Design consequence:** The compounding loop (§09.8) is scoped conservatively. Stage 1 only proposes updates to `CLAUDE.md` and does so through human-reviewed PRs; it never directly modifies agent skills, orchestrator code, or evaluation criteria. Benchmark-based regression detection is a secondary safeguard — if benchmark scores drop after a compound-loop PR is merged, the change is flagged for manual review.

#### 2.2.8 Harness engineering swings outcomes more than model choice alone

Practitioner writeups through 2025–2026 converge on the insight that agent harness design (tool set, context packaging, prompt scaffolding) often affects outcomes as much as or more than the underlying model. A specific recurring pattern: systems built around primitive filesystem-and-shell tools (`read_file`, `grep`, `find`, shell) plus good context packaging tend to outperform systems built around many bespoke domain-specific tools. Anthropic's own Claude Code documentation on skills and agent harnesses emphasizes that tool access and context design are primary levers.

Precise percentage improvements vary by study and are not pinned to a specific canonical number here.

**Design consequence:** Voters receive tool access, not pre-computed context blobs. Primitive tools: `read_file`, `grep`, `tree_sitter_query`, `lsp_references`, `git_log`, `git_blame`, `run_tests`. Voters decide what to investigate based on the diff. Per-voter tool-call budget prevents runaway investigation. Details: §09.7.

#### 2.2.9 When multi-agent loses to single-agent

Published analyses and production reports document cases where a well-tuned single-agent baseline beats orchestrated multi-agent systems. The failure pattern is consistent: multi-agent wins on embarrassingly parallel, read-heavy tasks with deterministic coordination, but loses on sequential, write-heavy, emergent tasks where coordination tax compounds.

**Design consequence:** Code review fits the winning profile — parallel specialists, read-only on codebase, deterministic handoff. Test generation is borderline (write-heavy) — kept within bounds by splitting the test generator (writes) from the mutant generator (read-only against the generator's output).

#### 2.2.10 AI-generated code has elevated vulnerability rates

Multiple independent 2025–2026 reports document elevated vulnerability rates in AI-generated code. Directionally consistent: [SusVibes (arXiv 2512.03262)](https://arxiv.org/abs/2512.03262) tested coding agents on 200 real feature-request tasks covering 77 CWEs — the best performer (SWE-Agent with Claude 4 Sonnet) was 61% functionally correct but only 10.5% secure, with security strategies like vulnerability hints failing to close the gap. [CodeRabbit's 470-PR analysis](https://www.coderabbit.ai/blog/) compared 320 AI-co-authored PRs against 150 human-only PRs and found AI PRs contained significantly more issues per PR on average. [Apiiro](https://apiiro.com/) and other security vendors have published reports showing AI-written code has measurably higher vulnerability rates than human-written baselines.

[Veracode 2026](https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-generated-code-vulnerability-surge-2026/) tested over 100 LLMs across 80 coding tasks and found **45% of AI-generated samples failed security tests overall**, with **86% failing XSS defense and 88% failing log injection**. The pass rate was *flat* across multiple testing cycles from 2025 through early 2026 despite vendor claims of improvement.

Two specific failure classes deserve dedicated detection:

- **Slopsquatting:** approximately 20% of AI-generated code samples reference packages that do not exist in their target registry; attackers register the hallucinated names as malicious packages before developers install them. Generic dependency CVE checks cannot detect this — the malicious package is fresh and has no CVE filed yet. [Georgia Tech Vibe Security Radar](https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-generated-code-vulnerability-surge-2026/) tracked 35 CVEs in March 2026 alone attributable to AI coding tools, with the actual count estimated 5-10× higher.
- **CSRF / SSRF universal failure:** [Tenzai's 2026 study](https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-generated-code-security-vibe-coding-202/) tested 15 production applications built with major AI coding tools and found **every single one** lacked CSRF protection and **every single one** had at least one SSRF vulnerability. This is a 100% failure rate on two distinct OWASP Top 10 categories — the patterns are framework-specific and contextual, exactly the kind of pattern that benefits from a deterministic backstop.

The underlying mechanism for many of these failures is the safety-removal pattern (§2.2.1): LLMs are optimized for acceptance, and removing a validation check is often the shortest path to making an error message disappear. [Columbia DAPLab 2026](https://towardsdatascience.com/the-reality-of-vibe-coding-ai-agents-and-the-security-debt-crisis/) explicitly documents agents removing validation checks, relaxing database policies, and disabling authentication flows just to resolve runtime errors.

**Design consequence:** The Security Voter specifically targets the safety-removal meta-pattern in addition to generic OWASP issues. Deterministic security tools (Semgrep, Bandit, TruffleHog, pip-audit) run alongside the LLM-based Security Voter rather than replacing it. Two additional deterministic backstops address the 100%-failure-rate categories: **slopsquat_check (§09.7.3.5)** queries PyPI/npm registry presence, registration age, and typosquat distance for every dependency added in the diff; **csrf_ssrf_probe (§09.7.3.6)** uses tree-sitter to find state-changing endpoints without CSRF middleware coverage and outbound HTTP calls with user-supplied URLs without allowlist checks. `CLAUDE.md` enumerates project hard constraints that the Security Voter enforces as critical-severity violations (§09.10).

#### 2.2.11 Current SOTA code review recall is bounded

Current best-in-class code review agents — whether Anthropic's Claude Code Review or commercial services like CodeRabbit, Greptile, Qodo — do not reliably catch all human-flagged issues. Anthropic's own data shows ~54% of internal PRs receive substantive comments (up from 16% pre-deployment), but that is "PR had a substantive comment," not "all real issues were caught." Community benchmark writeups for commercial services converge around the 30–40% recall range on real-world code review benchmarks.

**Design consequence:** Expectation calibration — `autoproduct` targets 40–50% recall with strong precision. The Leader's most important job is filtering (not aggregating): start with every voter's findings, discard low-confidence, retain what a reasonable human reviewer would act on. Calibration against a chosen benchmark subset (§10 Week 5) establishes the baseline before production use.

#### 2.2.12 LangGraph 1.0 production patterns

[LangGraph 1.0 reached stable GA on October 22, 2025](https://blog.langchain.com/langchain-langgraph-1dot0/). Production-used at Uber, LinkedIn, Klarna. LangGraph 1.0 is a low-level agent orchestration framework with first-class durable execution, human-in-the-loop patterns, and checkpointing primitives.

Key primitives `autoproduct` uses: `StateGraph` for the graph definition; `interrupt()` and `Command(resume=...)` for HITL; `AsyncPostgresSaver` (from [`langgraph.checkpoint.postgres.aio`](https://reference.langchain.com/python/langgraph/checkpoints)) for durable state; `EncryptedSerializer` (from `langgraph.checkpoint.serde.encrypted`) for encryption at rest; `get_state_history()` for time travel.

Important caveat from community practice: LangGraph's checkpointer saves state but does not by itself detect failures, trigger recovery, or coordinate across instances. For webhook mode where a crash must be detected and the review resumed, a supervisor layer (Celery + Redis in this design) is required. In CLI mode this caveat does not apply; a SQLite checkpointer is sufficient.

**Design consequence:**
- LangGraph used as a library (selective imports), not a framework — avoid adopting LangChain's broader ecosystem surface.
- Celery supervises LangGraph execution in webhook mode for true durable execution (§09.5).
- YAML mirror at every super-step provides a human-readable audit trail independent of Postgres availability (§09.6).

### 2.3 Framework and tooling selection

Selections made with alternatives considered.

| Concern | Selected | Alternatives considered | Core reason |
|---|---|---|---|
| Orchestration | LangGraph 1.0 (as library) | CrewAI, AutoGen, Agno, Claude Agent SDK, bespoke Python | Only one with production-grade HITL primitives and durable state; used minimally |
| Durable execution | Celery + Redis | Temporal, Dapr, SQS, raw asyncio | LangGraph checkpointer is save-state, not failure-detection; Celery supervisor fills the gap |
| Code intelligence | tree-sitter + pyright | SCIP, LSIF, raw AST, stack-graphs | Lightweight, fast, mature Python bindings; SCIP overkill for single-repo |
| Mutation testing | mutmut | cosmic-ray, Pitest (JVM), LLM-generated mutants | Deterministic, mature, good pytest integration |
| Security static analysis | Semgrep + Bandit + TruffleHog + pip-audit | Snyk, CodeQL, SonarQube | All OSS, all subprocess-friendly, combined covers SAST + secrets + deps |
| Model access | Direct SDKs per provider + OpenRouter fallback | OpenRouter-only, single provider | Prompt caching requires direct; OpenRouter for redundancy |
| Deployment (CLI) | Local Python + optional SQLite checkpointer | Docker, Railway | Primary use is local development |
| Deployment (webhook, optional) | Railway + Postgres + Redis | Fly.io, Render, AWS | Minimal ops overhead, Postgres managed |

### 2.4 Where research is indeterminate

Three areas where the literature does not decide, and the design takes specific positions based on engineering judgment:

**Voter count.** Literature supports 3–9 voters for code review. Anthropic ships 5, community implementations range from 5 to 9. `autoproduct` uses 6 (Correctness, Security, Performance, Context, Repo Graph, Style & Consistency). Six is defensible for the failure categories covered, not uniquely correct.

**Peer review inclusion.** Karpathy's llm-council uses it explicitly as the core design pattern. Other multi-agent code review systems (including Anthropic's Claude Code Review per publicly available information) do not publicly document using it. No direct head-to-head. `autoproduct` includes it as optional; empirical testing during implementation determines whether it improves recall in heterogeneous mode.

**Compounding loop cadence.** Weekly is the default; daily and on-demand are alternatives. Weekly matches realistic development rhythm without drowning in noise.

All three are revisable based on operational data.

---

## Part 3 — Architecture overview

Three views of the same system.

### 3.1 Four-layer stack

The agentic stack that has crystallized across 2025–2026 across production systems and practitioner writeups:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: PROJECT                                            │
│  ──────────                                                  │
│  Per-project configuration that extends the harness.         │
│  - CLAUDE.md (project constraints, updated by compound loop) │
│  - .claude/skills/ (project-specific skill extensions)       │
│  - codebase_profile.yaml (descriptive patterns)              │
│  - .mas/project.py (30 lines: which voters, which models)    │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: HARNESS (autoproduct)                              │
│  ─────────                                                   │
│  Reusable orchestration, reviewable as a unit.               │
│  - State machine (LangGraph)                                 │
│  - Agent base classes, voting strategies                     │
│  - Tools (read_file, tree_sitter_query, semgrep, mutmut ...) │
│  - HITL via GitHub Issue                                     │
│  - Compounding loop                                          │
│  - YAML mirror, replay CLI, benchmark runner                 │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: RUNTIME                                            │
│  ─────────                                                   │
│  - Python 3.11+ process                                      │
│  - Celery workers (when webhook mode is used)                │
│  - Postgres checkpointer (prod) or SQLite (local)            │
│  - Docker sandbox for running tests and mutmut               │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: MODEL                                              │
│  ─────                                                       │
│  Swappable frontier LLMs via provider adapters.              │
│  - Claude Opus, Sonnet, Haiku                                │
│  - GPT-5.4                                                   │
│  - Gemini 3.1 Pro                                              │
│  - Grok 4                                                    │
│  - OpenRouter fallback                                       │
└─────────────────────────────────────────────────────────────┘
```

Separation-of-concerns consequence: new projects onboard by writing Layer 4 only (~30 lines plus skill extensions). Model upgrades touch Layer 1 adapters only. Layer 3 is the open-source artifact.

### 3.2 Logical view — components

```
             ┌─────────────────────────────┐
             │  Entry points                │
             │  - CLI (primary)             │
             │  - FastAPI webhook (opt.)    │
             └──────────────┬───────────────┘
                            │
                            ↓
             ┌───────────────────────────────────────┐
             │  Orchestrator (LangGraph StateGraph)  │
             │  INIT → ANALYZE → TOOLS → VOTE →      │
             │  PEER → LEADER → POST → END           │
             │  (with branches for escape hatches    │
             │   and HITL interrupts)                │
             └─────┬───────────────────┬─────────────┘
                   │                   │
                   ↓                   ↓
       ┌────────────────────┐   ┌────────────────────┐
       │  Voters (6)        │   │  Leader            │
       │  - Correctness     │   │  Synthesis,        │
       │  - Security        │   │  dedupe,           │
       │  - Performance     │   │  taxonomy signals  │
       │  - Context         │   │  (STAR-L)          │
       │  - Repo Graph      │   │                    │
       │  - Style           │   │                    │
       └────────┬───────────┘   └──────────┬─────────┘
                │                           │
                ↓                           ↓
       ┌─────────────────────────────────────────────┐
       │  Shared primitives                           │
       │  - Tool registry (read_file, grep,           │
       │    tree_sitter_query, lsp_references,        │
       │    git_log, run_tests ...)                   │
       │  - LLM provider adapters                     │
       │  - State (LangGraph + YAML mirror)           │
       └──────────┬───────────────────────────────────┘
                  │
                  ↓
       ┌─────────────────────────────────────────────┐
       │  Cross-cutting                               │
       │  - HITL (interrupt() + GitHub Issue resume)  │
       │  - Compounding loop (weekly CLAUDE.md updates)│
       │  - Observability (YAML mirror, replay CLI)   │
       │  - Benchmark runner (real-PR subset + Defects4J) │
       └─────────────────────────────────────────────┘
```

### 3.3 Flow view — a single review

```
   PR opened OR `autoproduct review <URL>` invoked
                       │
                       ↓
     ┌────────────────────────────────────┐
     │  GATE 1 — DEFINITION OF READY      │
     │  Is the PR reviewable?             │
     │  - Has description                 │
     │  - Diff size sane (<2000 lines)    │
     │  - Tests present for non-trivial   │
     │    code changes                    │
     │  If no: post "not ready" comment,  │
     │  emit DoR-fail report, END.        │
     └────────────────┬───────────────────┘
                      │
                      ↓
     ┌────────────────────────────────────┐
     │  INIT                               │
     │  Load project config, CLAUDE.md,    │
     │  codebase_profile. Fetch diff.      │
     └────────────────┬───────────────────┘
                      │
                      ↓
     ┌────────────────────────────────────┐
     │  ANALYZE diff (AST-based)           │
     │  Classify: docs-only / simple /     │
     │  complex. Detect UI changes.        │
     └────────────────┬───────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │             │
         ↓            ↓             ↓
   docs-only     simple PR       complex
   → 1-line      → single Haiku  ↓
     comment       reviewer →    (main path)
     → END         POST
                      │
                      ↓
     ┌────────────────────────────────────┐
     │  DETERMINISTIC TOOLS (in parallel)  │
     │  Semgrep, Bandit, TruffleHog,       │
     │  pip-audit, tree-sitter index,      │
     │  pyright cross-file, Playwright     │
     │  (if UI changes detected). Output   │
     │  feeds voter context.               │
     └────────────────┬───────────────────┘
                      │
                      ↓
     ┌────────────────────────────────────┐
     │  VOTE (parallel, 6 voters          │
     │  + optional UI Behavior voter       │
     │  for frontend PRs)                  │
     │  Each: timeout 120s, 3 retries,     │
     │  tool-call budget max 10            │
     │  Heterogeneous models (4 families)  │
     └────────────────┬───────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │             │
         ↓            ↓             ↓
    3x fail     should peer      straight
    →           review?          to leader
    GATE 3:     (complex PR)
    interrupt() → PEER           → LEADER
    + Issue         │
                    ↓
     ┌────────────────────────────────────┐
     │  PEER REVIEW (optional)             │
     │  Voters re-score each other,        │
     │  anonymized. Cannot edit own        │
     │  findings.                          │
     └────────────────┬───────────────────┘
                      │
                      ↓
     ┌────────────────────────────────────┐
     │  LEADER                             │
     │  Synthesize, dedupe, severity-rank, │
     │  filter low-confidence.             │
     │  Inspect voter status (OK / BLOCKED)│
     │  Emit STAR-L taxonomy signals.      │
     │  Verdict (8 outcomes — §09.4.4.7):  │
     │   APPROVE / APPROVE_WITH_NOTES /    │
     │   REQUEST_CHANGES /                 │
     │   ESCALATE_MISSING_CONTEXT /        │
     │   ESCALATE_REQUIREMENT_CONFLICT /   │
     │   ESCALATE_SECURITY_RISK /          │
     │   ESCALATE_VOTER_DISAGREEMENT /     │
     │   ESCALATE_TOOL_FAILURE             │
     └────────────────┬───────────────────┘
                      │
         ┌────────────┴────────────┐
         │                          │
         ↓                          ↓
   ESCALATE_*                 Any high-risk file
   →                          OR `autoproduct deep`
   GATE 3:                    → adversarial test
   interrupt()                  (isolated git worktree)
   + GitHub Issue               - mutmut + AdverTest
                                - Playwright generation
                                  if UI touched
                                  │
                                  ↓
                      ┌───────────────────────┐
                      │  GATE 2 — TEST GATE   │
                      │  Unit pass? Coverage  │
                      │  threshold met?       │
                      │  Mutation score OK?   │
                      │  UI tests pass?       │
                      │  If no: verdict →     │
                      │  REQUEST_CHANGES      │
                      └─────────┬─────────────┘
                                │
                                ↓
                      ┌───────────────────────┐
                      │  REVERSE MERGE SAFETY │
                      │  Sync main into       │
                      │  worktree; re-run     │
                      │  tests. If main moved │
                      │  in an incompatible   │
                      │  way, flag for human. │
                      └─────────┬─────────────┘
                                │
                      ┌─────────┴─────────────┐
                      │                        │
                      ↓                        ↓
                    POST                   Per-voter log
                                          (.mas/voters/
                                            {name}/log.yaml)
                      │
                      ↓
     ┌────────────────────────────────────┐
     │  POST                               │
     │  - Structured test report (unit,    │
     │    mutation, coverage, security,    │
     │    dependency, integration, UI,     │
     │    performance)                     │
     │  - PR comment                       │
     │  - .mas/reviews/{id}/*.yaml         │
     │  - Commit to mas-reviews branch     │
     │  - If REQUEST_CHANGES ≥2 findings:  │
     │    emit exec-plan markdown          │
     └────────────────┬───────────────────┘
                      │
                      ↓
                    END (Code Review + Test stages)
```

After Code Review + Test, when the same PR proceeds toward production, two more stages activate:

```
   Code Review + Test verdict = APPROVE / APPROVE_WITH_NOTES
                       │
                       ↓
     ┌────────────────────────────────────┐
     │  GATE 5 — DEPLOY REVIEW GATE       │
     │  Triggered when PR includes        │
     │  CI/CD config / IaC / migrations / │
     │  canary spec changes — OR          │
     │  on every release-tagged PR        │
     │  (configurable per project).       │
     └────────────────┬───────────────────┘
                      │
                      ↓
     ┌────────────────────────────────────┐
     │  DEPLOYMENT MAS (§09.11)            │
     │  Voters: DeployConfig,              │
     │  CanaryAnalysis, Rollback,          │
     │  Migration. Trust-tier framework    │
     │  (insight / assistive / autonomous- │
     │  within-guardrails). Policy-as-     │
     │  Prompt guardrails compiled from    │
     │  .mas/deploy-policy.yaml.           │
     │  Verdicts: PROMOTE / HOLD /         │
     │  AUTO_ROLLBACK (within guardrails)/ │
     │  ESCALATE_DEPLOY_RISK /             │
     │  ESCALATE_MIGRATION_DESTRUCTIVE     │
     └────────────────┬───────────────────┘
                      │
                      ↓
              Post-deploy
              into production
                      │
                      ↓
     ┌────────────────────────────────────┐
     │  GATE 6 — PRODUCTION HEALTH GATE   │
     │  Always-on. Sentry / Datadog /      │
     │  PagerDuty / Prometheus signals     │
     │  flow continuously into the         │
     │  Maintenance MAS.                   │
     └────────────────┬───────────────────┘
                      │
                      ↓
     ┌────────────────────────────────────┐
     │  MAINTENANCE MAS (§09.12)           │
     │  Voters: Triage, RootCause,         │
     │  FixPR, LearnedSkill.               │
     │  Three-tier autonomy:               │
     │  insight (always) →                 │
     │  assistive fix-PR →                 │
     │  autonomous within allowlist        │
     │  Confidence < 60% → re-investigate  │
     │  3× re-investigation below          │
     │  threshold → ESCALATE_INCIDENT_     │
     │  UNRESOLVED                         │
     │  Output: triaged incident report,   │
     │  fix-PR (re-enters Code Review),    │
     │  learned-skill on recurring         │
     │  patterns (after 3+ instances)      │
     └────────────────┬───────────────────┘
                      │
                      ↓
                    END (production stable)
                    OR  HUMAN HITL
                    (incident escalated)
```

Six gates. **Gate 1** (Definition of Ready) runs before any LLM work — cheap deterministic check that saves money if the PR isn't ready. **Gate 2** (Test Gate) runs after adversarial testing — a Code Review verdict can only be `APPROVE` (or `APPROVE_WITH_NOTES`) if unit tests pass and coverage/mutation thresholds are met. **Gate 3** (Review Gate, HITL) triggers on any `ESCALATE_*` verdict (§09.4.4.7 / §09.11.6 / §09.12.7), 3× failure at any stage, or safety-removal pattern (§09.8.1). **Gate 4** (Rollback) is on the compounding loop path: if a merged `CLAUDE.md` update causes benchmark regression, auto-open a revert PR (§09.8.6). **Gate 5** (Deploy Review Gate) reviews CI/CD / IaC / migration / canary spec changes (§09.11). **Gate 6** (Production Health Gate) is the always-on signal-driven entry to the Maintenance MAS (§09.12).

The weekly **compounding loop** is a separate flow: reads accumulated YAML mirrors over the past seven days across all four stages, clusters taxonomy signals by category, proposes `CLAUDE.md` updates via PR, and refreshes the learned-skill registry. Details in §09.8.

### 3.4 Core design principles — preservation rules

Five rules. A proposed change that violates one needs an explicit engineering-judgment rationale captured in the commit or PR message.

| # | Rule | What it rejects |
|---|---|---|
| 1 | Deterministic control, probabilistic analysis | `agent.decide_next_step()` calls |
| 2 | Hooks enforce, skills guide | Critical behavior relying only on prompts |
| 3 | Heterogeneous voters by default | All-Claude or all-GPT rosters |
| 4 | Harness reusable, project specific | AgentHire-specific logic in Layer 3 |
| 5 | Compound, don't stagnate | Components that emit no taxonomy signals |

### 3.4.1 Vocabulary alignment with Claude Code

`autoproduct` borrows liberally from Anthropic's [Claude Code](https://code.claude.com/) — the agentic coding tool that ships the same primitives it uses to build itself. Several Claude Code terms appear throughout this design with specific meanings that follow Claude Code's official semantics:

| Claude Code term | Meaning here | Where in `autoproduct` |
|---|---|---|
| **Skill** | A `SKILL.md` (or `.md`) file with YAML frontmatter that tells Claude *when* to use it and markdown content telling Claude *how*. Auto-invoked when description matches context. | Voter skills live in `skills/{voter_name}.md` (§09.4.4); also used for project-specific extensions in `.claude/skills/` (§09.10.5) |
| **Subagent** | An isolated Claude instance with its own context window, system prompt, and tool access. Returns only the final result to the parent. Cannot spawn its own subagents. | Each voter is conceptually a subagent in the [Anthropic-defined sense](https://code.claude.com/docs/en/sub-agents); their tool calls happen in their own context, only `VoterOutput` envelope returns to the orchestrator |
| **Hook** | A shell command, HTTP endpoint, or LLM prompt that runs deterministically at a specific lifecycle event (PreToolUse, PostToolUse, etc.). Provides guarantees prompts cannot. | autoproduct uses hooks for Gate 4 Rollback (§09.8.6 GitHub Actions = a CI hook) and for tool risk-level enforcement at registry boundary (§09.7.1); see §09.X for additional hooks |
| **Slash command** | A user-invoked or auto-invoked shortcut, single-file `.md` in `.claude/commands/` with `$ARGUMENTS` substitution. Pipelines work but not packaged. | autoproduct's CLI commands (`autoproduct review`, `autoproduct deep`) are the same shape — single-entry orchestrators |
| **Plan mode / Explore mode** | Read-only reasoning before any tool side effect. Anthropic's recommended Explore → Plan → Implement → Commit workflow. | The `analyze_node` + `tools_node` + `vote_node` + `verify_node` + `leader_node` chain is the explore-then-plan phase; `adversarial_test_node` onwards is the implement phase. Mapping in §09.X.X. |
| **Verify-each-finding** | The pattern from [`/ultrareview`](https://code.claude.com/docs/en/ultrareview): every candidate finding is independently reproduced before being reported. | §09.4.6 — autoproduct's `verify_node` is a direct port of this pattern |
| **Confidence threshold** | The 0-100 score with default 80 used in [Anthropic's open-source code-review plugin](https://github.com/anthropics/claude-code/blob/main/plugins/code-review/README.md). | §09.4.7 — autoproduct uses the same shape with `thresholds.confidence_min: 80` |

The mapping is intentional. Where Claude Code has solved a coordination problem well, autoproduct adopts the convention rather than inventing a parallel one. Where autoproduct's scope diverges (deterministic control flow, heterogeneous-provider voters, persistent compounding loop), the divergence is explicit.

### 3.5 Mode taxonomy

The orchestrator selects a mode based on PR characteristics (deterministic, per Rule 1). Users can override.

| Mode | Trigger | Voters | Extras |
|---|---|---|---|
| `fast` | AST-verified cosmetic diff; <2 files; <20 lines | 1 Haiku reviewer | DoR gate only |
| `standard` (default) | All other PRs | 6 voters + Leader (+ UI Behavior voter if UI changes detected and `codebase_profile.ui.framework` set) | All 4 gates, deterministic tools, mutation testing, Playwright if UI, reverse-merge safety, per-voter log |
| `deep` | File marked `risk_class: high` OR explicit `autoproduct deep` | 6 (or 7) voters + Leader with peer review enabled | All standard extras + Playwright test generation for UI changes + extended adversarial loop |

#### 3.5.1 Auto-triage mode router (high-volume vibe coding context)

The empirical pain point this addresses: vibe-coded projects (Cursor, Lovable, Bolt) ship 50-200 PRs/day, not 5-20. At that throughput, running every PR through `standard` mode (~$0.30-0.80 per review) burns $20-50/day in LLM cost — uneconomic for solo founders. Yet running everything through `fast` mode misses the cross-file safety-removal patterns that are the highest-value reason to use `autoproduct` at all.

The auto-triage router uses a deterministic decision function (Rule 1) to pick the right mode per PR, with the goal that high-risk PRs always get `standard` or `deep` review, while low-risk PRs (renames, docstring updates, version bumps) get `fast` review:

```python
# autoproduct/orchestrator/mode_router.py — runs in dor_gate_node before voters
def select_mode(pr_diff: ParsedDiff, codebase_profile: dict, user_override: str | None) -> str:
    if user_override in ("fast", "standard", "deep"):
        return user_override

    # ESCALATE to deep — risk patterns that demand peer review
    if _touches_high_risk_paths(pr_diff, codebase_profile):
        # Auth, billing, payment, migration, IaC for prod
        return "deep"
    if pr_diff.touches_security_critical_files():
        return "deep"

    # ESCALATE to standard — patterns that need full ensemble
    if pr_diff.adds_new_dependency():
        return "standard"  # slopsquat probe (§7.3.5) must run
    if pr_diff.adds_state_changing_endpoint():
        return "standard"  # CSRF probe (§7.3.6) must run
    if pr_diff.changed_lines > 50 or len(pr_diff.changed_files) > 3:
        return "standard"
    if pr_diff.touches_files_with_risk_class("medium") or higher:
        return "standard"
    if _has_safety_removal_signature(pr_diff):
        # Decorator removal, sanitization removal, etc. — caught by ast pattern
        return "standard"

    # DOWNGRADE to fast — only if all of these hold
    if pr_diff.is_ast_verified_cosmetic() and pr_diff.changed_lines < 20 and len(pr_diff.changed_files) < 2:
        return "fast"

    # Default: standard
    return "standard"
```

The router is **conservative by design** — it errs toward `standard` mode on ambiguity. The `fast` path is reserved for PRs where the deterministic checks alone confirm no safety-relevant change. Any PR that adds a dependency, adds a state-changing endpoint, removes a decorator, or touches more than 3 files lands in `standard` mode, regardless of how few lines changed.

**Cost projection at 100 PRs/day vibe-coding throughput:**

| Distribution assumption | fast (% × $0.05) | standard (% × $0.55) | deep (% × $2.00) | Daily | Monthly |
|---|---|---|---|---|---|
| Conservative (vibe coder, real PRs) | 20% × $0.05 = $1 | 65% × $0.55 = $35.75 | 15% × $2 = $30 | $66.75 | ~$2,000 |
| Aggressive routing (mostly cosmetic) | 60% × $0.05 = $3 | 35% × $0.55 = $19.25 | 5% × $2 = $10 | $32.25 | ~$970 |

For a solo-founder budget ($100-200/month target per the AgentHire context), 100 PR/day is structurally too high — `autoproduct`'s value proposition depends on PR volume being review-worthy, not flood-volume. The router makes this trade-off explicit: it routes optimally given a volume, but does not magically make 100 PR/day affordable. The honest framing in the README and the v1.0.0 launch is "review tool for projects shipping 5-30 PR/day"; high-volume use cases use `fast`-only mode and accept reduced coverage.

**Two execution surfaces, same voters.** All three modes can run via either:

- **Batch (LangGraph)** — webhook or `autoproduct review <PR-URL>` from the CLI. Deterministic, fully automated, results posted as PR comment + ledger artifacts. This is the primary surface and what the rest of the docs default to describing.
- **Interactive (Claude Code Agent Teams)** — `autoproduct deep <PR-URL> --interactive` opens a tmux/terminal session where the same voter skills run as Claude Code Agent Teams. The user can watch each voter's reasoning in a separate pane, ask follow-up questions, and intervene mid-review. Useful for the 1-2 PRs/week where deeper investigation pays off. Both surfaces share the same voter skill files in `skills/` — the only difference is orchestration layer (LangGraph vs Agent Teams). Output artifacts (final.yaml, evidence ledger) are the same shape in both surfaces.

The interactive surface is a thin wrapper, not a separate codebase. It's documented in §09.4 voter skills (which work in both contexts) and §10 Day 35 (Week 6) ships the wrapper.

### 3.6 Not in Part 3

Specifics live in `09-system-design.md`:

- Voter skill definitions and prompts (§09.4)
- State schema and node contracts (§09.5)
- Gates: Definition of Ready, Test Gate, Review Gate, Rollback (§09.5)
- Git worktree and reverse-merge safety (§09.5 and §09.7)
- Dual state representation details (§09.6)
- Tool interfaces and contracts including `run_playwright_tests` (§09.7)
- HITL flow mechanics and compounding loop (§09.8)
- Per-voter log format (§09.8)
- Structured test report format (§09.9)
- Observability, YAML mirror format, replay CLI, benchmark runner (§09.9)
- Project integration (CLAUDE.md, .claude/, codebase_profile with UI config) (§09.10)

Daily implementation plan and code snippets live in `10-implementation-plan.md`.

---

*End of 08-foundation.md. Continue to `09-system-design.md` for the concrete system specification.*
