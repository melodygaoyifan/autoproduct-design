# autoproduct — Design Documentation

`autoproduct` is a multi-agent system that covers four stages of the software development cycle: **code review, test, deployment review, and production maintenance**. It runs heterogeneous specialist agents over pull requests and production signals, runs deterministic analysis tools alongside, surfaces escalations through human-in-the-loop gates, and accumulates structured learning over time.

**Architectural posture (per `11-ultimate-architecture.md`):** spec-driven (every voter has a machine-checked YAML frontmatter contract; modules being reviewed have `.mas/specs/*.spec.yaml` invariants), MCP-transport (tools live in MCP servers as subprocesses for OS-level sandboxing + dynamic discovery + per-tool RBAC), harness-enforced (voter cannot register without passing fixture gate; contract violations are unrecoverable, not warnings).

This directory holds the authoritative design documentation.

## Reading order

```
08-foundation.md          → Problem statement, research foundation, architecture overview, scope (4 stages)
09-system-design.md       → Agent rosters, state machine, gates, tools, HITL, deployment MAS, maintenance MAS, observability
10-implementation-plan.md → 24-30 week day-by-day plan with code snippets and success criteria (4 milestones: v0.1.0 → v0.5.0 → v0.8.0 → v1.0.0)
11-ultimate-architecture.md → Architectural keystone: how spec-driven design, MCP transport, and harness enforcement fit together as one coherent posture
```

Four documents, read in order. First read 08 cover-to-cover; 09 cover-to-cover; 10 as reference; **11 as the architectural integration that ties everything together.**

## Scope

`autoproduct` covers four stages of the SDLC:

| Stage | What the MAS does | Customer-facing motivation |
|---|---|---|
| **Code Review** | 6+ heterogeneous voters review the diff, deterministic tools run alongside, every finding independently verified | Catch bugs before merge |
| **Test** | Adversarial mutation testing, UI test generation, structured test report | Ensure tests cover the change |
| **Deployment Review** | Voters review CI/CD config, infrastructure-as-code, migration scripts, canary analysis policies; integrates with Argo Rollouts / Flagger for metric-driven auto-rollback decisions | Catch deploy-time risks before production exposure |
| **Production Maintenance** | Triage agents process Sentry/Datadog/PagerDuty signals, root-cause investigators correlate with recent PRs, fix-PR generators propose patches; learned-skill pattern accelerates recurring incidents | Resolve customer-impacting issues quickly |

The system is **autonomous within bounded autonomy**: every stage operates on the same 3-fail-then-escalate pattern (§08.1.5). Production-mutating actions (auto-merge, auto-deploy to prod, auto-hotfix) are gated by structural tool risk-level enforcement and human approval — autonomy is bounded by what the trust tier and the human have explicitly permitted.

### What's covered

- Heterogeneous parallel review (Correctness, Security, Performance, Context, Repo Graph, Style; optional UI Behavior)
- Deployment review voters (DeployConfig, CanaryAnalysis, Rollback, Migration)
- Production maintenance voters (Triage, RootCause, FixPR, LearnedSkill)
- Trust-tier framework — insight → assistive → autonomous-within-guardrails ([arXiv:2508.11867](https://arxiv.org/abs/2508.11867))
- Policy-as-Prompt guardrails — runtime classifiers compiled from `.mas/deploy-policy.yaml` ([arXiv:2509.23994](https://arxiv.org/abs/2509.23994))
- BLOCKED voter status — voters that lack context return `BLOCKED_*` rather than guessing
- Twelve-outcome verdict taxonomy (APPROVE / APPROVE_WITH_NOTES / REQUEST_CHANGES / 9× ESCALATE_*)
- Independent verification of every candidate finding (the `/ultrareview` pattern) before reporting
- Numeric confidence scoring (0-100) with threshold filter (default 80) for PR comments
- Adaptive fleet sizing — scale voters up to 8+ on large diffs, down to 1 on cosmetic changes
- Six explicit gates: Definition of Ready, Test, Review (HITL), Rollback, Deploy Review, Production Health
- Deterministic tool stack: SAST, secret scan, dependency CVE audit, **slopsquatting detection (registry-presence + age + typosquat-distance per §07.3.5)**, **CSRF/SSRF deterministic probes (§07.3.6)**, symbol graph, type checking, UI test runner, Terraform/K8s linting, Argo Rollouts/Flagger CRDs, Sentry/Datadog/PagerDuty/Prometheus clients
- Auto-triage mode router (§08.3.5.1) — deterministic per-PR routing to fast/standard/deep based on diff characteristics; conservative-by-default (any state-changing endpoint, any new dependency, or any safety-removal signature lands in standard mode regardless of line count)
- Tool risk-level enforcement (L0-L4); deploy/prod-mutating tools at L3-L4 are structurally gated
- Hooks for deterministic enforcement
- Edit isolation via git worktrees; reverse-merge safety
- Per-voter log and weekly `CLAUDE.md` compounding loop
- Learned-skill registry — recurring incident classes generate reusable fast-paths
- Evidence ledger and tool audit log for every review and incident
- Cost / token / retry observability per voter and per stage

### Explicitly out of scope (still)

`autoproduct` does **not** do any of the following; pair it with other tools if you need these:

- **Discovery / Plan / Spec / Coding stages of the SDLC.** Out of scope. Pair with separate tools or Claude Code's `/plan` and `/ultraplan` for those stages.
- **Product management.** User research, roadmap, prioritization, launch planning.
- **Requirements engineering.** No discovery, no user story writing, no acceptance criteria authoring.
- **Auto-merge to main.** The system never merges PRs. Human is always the final gate. (Same for compound-loop CLAUDE.md updates.)
- **Auto-deploy to production without human approval.** Deploy review can recommend; the human (or a CI/CD policy) executes. Within the trust tiers, *staging* deploys can be autonomous after consistent track record; *production* deploys require explicit human approval per deploy. See §09.11.5 trust-tier framework.
- **Auto-hotfix in production without human approval.** Maintenance can propose a fix-PR, can recommend a known-safe action (e.g., scale up) within pre-approved guardrails, but must escalate to human for any production-mutating action outside the explicit guardrail allowlist. See §09.12.6.
- **Auto-rotate secrets, run destructive migrations, modify auth/billing.** L4 tools are never exposed to any voter or maintenance agent.
- **SaaS / productization.** Personal infrastructure and an open-source reference implementation.

## Conventions

- English throughout.
- Citations are inline hyperlinks in practitioner style. Only verified sources are cited.
- Code is Python 3.11+, real and runnable where shown.
- Cross-references: `§09.4` means document 09, Part 4. Within a doc: `§4`.
- Documents 08–10 are the canonical source. When they conflict with `archive/`, 08–10 wins.

## Bootstrapping (chicken-and-egg note)

`autoproduct` reviews other code. While it is being built (Weeks 1-6 of v0.1.0), there is no `autoproduct` to review the code that becomes `autoproduct` itself. This is a real gap with a real mitigation:

During Weeks 1-6 (and ongoing for `autoproduct`'s own future PRs), use one of the following review tools as a stand-in:

- **Claude Code's `/review` and `/ultrareview`** — runs the closest-equivalent multi-agent review pattern that `autoproduct` is itself derived from. Free with a Claude Pro/Max subscription. Recommended primary stand-in.
- **GitHub Copilot Code Review** — built into the GitHub PR UI; lower-quality than `/ultrareview` but always-on.
- **Cursor's Bug Finder** — if developing in Cursor, runs alongside the editor.

When `autoproduct` v0.1.0 is operational (~Week 6), point it at its own PRs as the dogfooding test (§10 Day 36 retrospective). Any bug `autoproduct` finds in itself that the stand-in tools missed becomes a fixture in `tests/integration/voters/fixtures/` — the bootstrap is then complete and self-reinforcing.

**Caveat:** the stand-in tools have weaker safety-removal detection than `autoproduct` is designed to have (per §08.2.2.1). For Weeks 1-6 of `autoproduct`'s own development, manually re-read every PR for the safety-removal pattern as a discipline; this is the highest-risk class that stand-in tools miss most consistently.

## Archive

`archive/` contains the design evolution (seven prior iterations) plus an external methodology reference. Preserved for historical context. Superseded by 08–10.
