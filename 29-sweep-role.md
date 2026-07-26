# 29 — The Sweep Role: Scheduled Janitorial Work Over Queues the Framework Already Keeps

Parts 84–85. Adds a **Sweep role** — a scheduled, attention-capped background pass that executes well-defined maintenance chores and reports everything else. It is a *role*, not a ninth stage: Sweep harvests work from ledgers the canon already maintains, and every patch it produces flows through the unchanged Stage 1–4 gates. Numbering: ADR-U36/U37, invariants 14.29–14.30, FMEA F-29.x.

---

## Part 84 — What the research says, and what it means here

### 84.1 The pattern and its production record

The "Sweep" name comes from Sweep AI, the Apache-2.0 issue→PR junior developer: label an issue, the agent plans (posting the plan as a comment *before* coding, so a human can redirect pre-execution), implements, validates with the repo's own tests and formatters, and iterates on PR comments; alongside reactive issues it applies standing "Sweep Rules" — repo conventions stacked proactively as small fixes ([project docs](https://github.com/mcoolidge/sweep); [architecture review](https://www.onegen.ai/project/sweep-ai-automated-github-issue-resolution-and-pull-request-generation/)).

The production evidence for the *category* is more instructive than the product. Organizations adopting background agents did **not** start with feature work — they started with migrations, upgrades, and chores, because the output is well-defined, easily verified, and low-risk: Stripe/Spotify/Uber all entered there, Spotify reporting 60–90% time savings on code transformations; the second wave was maintenance proper — flaky-test fixes, **feature-flag cleanup**, doc fixes, debt — with Uber generating 5,000+ unit tests monthly and Ramp's security sweep finding ~100 vulnerabilities in a week including IDORs that pen testing missed ([Ona, engineering leader's guide to background agents, 2026](https://ona.com/guides/background-agents)). The recommended rollout is phased: dry-run/report-only first, then a single low-risk chore class, then expansion — trust is built, not assumed ([Kinde, nightly tech-debt burners](https://www.kinde.com/learn/ai-for-software-engineering/ai-devops/nightly-tech-debt-burners-scheduling-agents-to-clean-your-repo/)). And the sharpest recent research finding is a warning: as maintenance delegation becomes continuous and event-driven, the critical judgment is knowing when **not** to act — over-action is a first-class failure mode of autonomous maintenance agents ([arXiv:2605.07769](https://arxiv.org/pdf/2605.07769)).

### 84.2 The integration insight: the chore queue already exists

Most teams bolting on a janitor agent must first invent its worklist. This framework doesn't — **docs 20–28 already emit machine-readable maintenance obligations with owners, dates, and falsifiers.** Sweep's inbox is the union of ledgers the canon keeps:

| Queue (existing artifact) | Chore it implies |
|---|---|
| `.mas/flags.yaml` past-expiry entries (ADR-U35) | execute the removal task that was scheduled at flag creation |
| `deprecated_references` checkpoint counts (§81.1) | whittle brownfield architecture-violation debt, N items per pass |
| `debt_server` metrics — vulture dead code, jscpd clones | deletion/consolidation candidates |
| Claim ledger `expiry` fields (§20.53) | re-snapshot evidence, or retire the claim visibly |
| Watch-items ledger review dates (§75.2) | re-verify, update `verified_on`, or escalate the falsifier |
| Stale `capacity.yaml` (`measured.at` older than last perf-relevant merge, §77.4) | schedule a re-run; mark entry stale meanwhile |
| Baseline environment-fingerprint drift (F-26.2), registry/contract drift (F-27.4, F-28.3) | reconciliation PRs or findings |
| Dependency updates | upgrade PRs — gated by the existing `slopsquat_check` before anything else |
| Fixture/template/doc-link rot | refresh PRs (product-bench templates already fail CI when rotten, §73.2) |
| Periodic security pass (the Ramp pattern) | re-run `csrf_ssrf_probe` + `slopsquat_check` repo-wide; findings route to the normal pipeline, never self-fixed |

This is the design argument for Sweep being cheap here: the hard problem (a trustworthy, prioritized, falsifiable chore backlog) was solved as a side effect of claim discipline. Sweep is the executor the ledgers were waiting for.

---

## Part 85 — The role, specified

### 85.1 ADR-U36 — Sweep is a scheduled role over existing queues, allowlisted and behavior-preserving

**Decision.** Sweep runs on the compound-loop cadence (weekly default; nightly at higher substrate rungs). Per pass it: (1) snapshots the queues above; (2) ranks by debt-trend impact; (3) for items in an **allowlisted chore class**, produces a plan-first patch; (4) for everything else, produces a report line. The allowlist at introduction, deliberately matching the production-proven entry points (§84.1): dependency upgrades · flag removals already past expiry · dead-code deletion · doc/link/fixture refresh · `deprecated_references` whittling · ledger reconciliations. Every patch carries the **behavior-preservation contract**, checked deterministically before the PR opens: declared `api_surface` unchanged · hermetic suite green · coverage non-decreasing · replay-identity and eval-gate baselines untouched · no diff outside the chore's declared file scope. A change that cannot satisfy the contract **is not a sweep task** — it exits to the normal pipeline as a proposed brief, where Planning and humans see it. Sweep PRs then ride the ordinary Stage 1–4 gates (fast mode where `mode_router` allows); Sweep has no merge authority, no new trust ceiling, and consults the shared-file registry to skip anything an active feature lane owns. *Rejected:* a ninth Sweep stage (chores are not a lifecycle phase; they are deferred obligations of every phase); letting Sweep edit specs, gates, `deps.yaml`, or its own allowlist (each is SCR-class or harness-owned by prior ADRs — a janitor that renovates is the erosion mechanism wearing a uniform).

### 85.2 ADR-U37 — No-action is a first-class outcome, and attention is the budget

**Decision.** A Sweep pass that finds nothing actionable emits a signed "clean pass" record with the queue snapshot it checked — silence and success are distinguishable. Sweep may hold at most `sweep.max_open_prs` concurrently (default 2; **E2 solo edition: 1**), ranked, the rest reported; sweep PRs are lowest priority in the merge queue and can never starve feature review. The E2 weekly founder review (§70.2) gains a fixed agenda line — the sweep digest — so chore review lands inside the attention budget rather than around it. The measured failure mode is **over-action**, per the when-not-to-act finding (§84.1): the pass records an action-rate metric (patches proposed / items inspected), and a rising rate with a flat debt trend is itself a compounding-loop finding — a janitor generating churn instead of cleanliness. *Rejected:* unbounded nightly PR streams (Uber-scale output needs Uber-scale review attention; ours is budgeted by doc 16 and, in E2, is one person); auto-merge for "trivial" sweeps (trivial is a judgment the 88%-pilot graveyard is full of).

### 85.3 Rollout ladder (SW0–SW2) and edition defaults

Per the phased-trust practice (§84.1): **SW0** report-only — Sweep runs for two full cadences producing digests and zero patches, establishing the baseline action-rate; **SW1** one chore class enabled (recommended first: flag removals — smallest blast radius, and the removal tasks were already scheduled at creation by ADR-U35); **SW2** full allowlist. Promotion between rungs is a human decision recorded like a trust-tier promotion (§11.5.1), demotion is automatic on any behavior-preservation violation. Edition defaults: E1 starts at SW0 with the digest wired into existing review forums; E2 starts at SW0 with `max_open_prs: 1`; E3 gets the ladder as a config surface and the contract as an extension point.

### 85.4 Bookkeeping

| Invariant | Statement | Enforced by |
|---|---|---|
| 14.29 | Sweep patches only allowlisted chore classes under the behavior-preservation contract; any out-of-scope diff aborts the PR | contract check pre-PR; harness rejects sweep-labeled PRs with foreign diffs |
| 14.30 | Sweep's open-PR count never exceeds the configured attention cap; a clean pass is recorded, not silent | scheduler; signed clean-pass records in the attestation chain |

**FMEA:** **F-29.1** sweep churn floods review attention (H×M) → caps + ranking + lowest merge-queue priority + action-rate alarm. **F-29.2** "cleanup" changes behavior — dead-code deletion removes dynamically-referenced code (H×M) → vulture-confidence threshold + string-reference grep + the checkpoint pattern (delete in one PR, easy revert) + contract's suite/coverage floor. **F-29.3** sweep collides with an in-flight feature (M×M) → shared-file registry consult is mandatory, skip-and-report. **F-29.4** dependency upgrade passes tests but shifts runtime behavior (M×M) → upgrades attach changelog diff + ride full (not fast) review mode for majors; `slopsquat_check` precedes everything. **F-29.5** clean passes rubber-stamped into meaninglessness (M×L) → clean-pass records include the queue snapshot hash; an unchanged snapshot across passes with growing debt metrics contradicts itself visibly.

**Metrics:** action rate per pass · debt-trend deltas attributable to sweep (flags removed, deprecated_references count, dead-code LOC) · sweep-PR revert rate (the honesty metric — a rising revert rate demotes the rung) · median sweep-PR review dwell.

---
*Cross-references: §09.8 (compound loop cadence), §11.5.1 (trust promotions), §16 (WIP/attention, shared-file registry, merge queue), §20.53 (claim expiry), §70.2 (E2 weekly review), §75.2 (watch items), ADR-U35 (flag registry), §81.1 (checkpoint), §77.4 (capacity staleness). Research rows land in doc 15 §6.*
