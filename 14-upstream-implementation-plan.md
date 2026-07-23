# 14 — Upstream Implementation Plan

Part 37 + Appendices E–H. The upstream track (U1–U12) extends the shipped downstream system (v1.0.0, doc 10) to the full lifecycle. Same conventions as doc 10: day-by-day granularity while the ground is new (U1–U3), week-level once patterns repeat; every week ends with checkable success criteria; the change-control protocol and 20% week-buffer policy of §10 Part 11 apply verbatim. Time budget: **12 weeks, 60–96 hours** (solo, part-time), calibrated by Day-0 Track B before Week U1 starts.

Build order rationale: **Spec first** (its deterministic tools are the cheapest wins and its outputs feed everything), **Coding second** (closes the loop into the existing §09 pipeline immediately), Plan third, Discovery fourth (most novel, least deterministic — benefits from the machinery existing first).

---

## Milestones

| Version | Weeks | Contains | Release gate |
|---|---|---|---|
| **v1.1.0** upstream-core | U1–U4 | spec toolset + SpecWriter + Testability/Ambiguity voters + coding loop (router/assembler/implementer/build-gate/PR) + SCR round-trip | Both stages e2e on a real feature; 6 voters' fixtures ≥87.5%; SCR trail in YAML mirror |
| **v1.2.0** planning | U5–U6 | dag/lane/budget checks + Planner + 5 Plan voters + Gate U2 lock enforcement | Plan e2e; lock breach test proves filesystem hook; fixtures merged |
| **v1.3.0** discovery+loops | U7–U9 | research/analytics servers + BriefWriter + 4 voters + hypothesis ledger + feedback loops (34.1–34.3) + Preflight A/B | Idea→PR full traverse; tainted-session lockout test passes; reconciliation job runs against a shipped feature |
| **v1.4.0** full-lifecycle GA | U10–U12 | metrics, policies hardened, FMEA drills, docs public | All §12.22.5 completion criteria; eight-stage traversal logged |

---

## Week U1 — Spec toolset (deterministic first)

**Day 1 — ears_lint.** `tools/spec/ears_lint.py`: PEG/regex over the five patterns; violations typed (no-pattern-match, multi-SHALL, missing-id, missing-FR-link). 20 unit fixtures (10 valid across all five patterns, 10 violations). *Done:* `pytest tests/tools/test_ears_lint.py` green; lints the hand-written EARS file for this week's own work.

**Day 2 — coverage_matrix + schema_compile.** Set-arithmetic over (FR, AC, skeleton) links parsed from front-matter; emits `coverage-matrix.yaml`. schema_compile = import-and-validate for jsonschema/pydantic contracts. *Done:* orphan in either direction detected on synthetic bundles.

**Day 3 — quantifier_scan + invariant_diff + artifact schemas.** Banned-term list in `.mas/spec-lint.yaml` (project-extendable); structured diff of module-delta vs current `.mas/specs`. JSON-schemas for brief/plan/spec-bundle/SCR checked in; harness validates on write. *Done:* schemas reject a malformed bundle with a useful error.

**Day 4 — spec toolset registered on code_intel_server.** Tools appear via `tools/list`; allowlists added to (not-yet-written) voter spec stubs; MCP audit logging confirmed for the new tools. *Done:* an MCPClient smoke test calls all five.

**Day 5 — det_tools_node + generative-subgraph skeleton.** `orchestrator/upstream/spec_graph.py` with assemble/generate/det_tools stubs wired to the dispatcher (`stage: "spec"` routes). *Done:* a fake artifact traverses assemble→det_tools with violations short-circuiting per §13.25.4.

## Week U2 — SpecWriter + first voters + verify

**Day 6-7 — ArtifactWriter base + SpecWriter (incl. design.md).** Base class per §13.25.2 with sources_read receipts (harness-checked). SpecWriter skill (§13.28.3) + frontmatter; generates a full bundle — design.md (§13.28.2 sections), EARS ACs, one contract, skeletons — for one real backlog feature. *Done:* bundle passes ears_lint + schema_compile + design section-presence check on ≤2 revisions.

**Day 8 — Testability voter + fixtures.** Skill + 8 fixtures (4-2-2); registration blocked below 87.5% (reuses §11.18.2 FixtureGate untouched — the gate is stage-agnostic by design). *Done:* voter registers.

**Day 9 — Ambiguity voter (heterogeneous family) + fixtures.** Consumes quantifier_scan hits; family ≠ SpecWriter's. *Done:* registers; the §13.33.2 example fixture is among its positives.

**Day 10 — verify_node upstream semantics + leader_node reuse.** NEEDS_PROBE branch wired to schema_compile/repo probes; Leader verdict set = §13.28.5. *Done:* injected fake finding ("AC-3 contradicts AC-9" where it doesn't) dies as NOT_REPRODUCIBLE; e2e spec run produces a verdict + STAR-L in the YAML mirror.

## Week U3 — Coding loop core

**Day 11 — task_router + context_assembler.** Topo-next with circuit breaker; manifest with hashes + token cap; overflow → TASK_BLOCKED_CONTEXT_OVERFLOW. *Done:* unit tests incl. overflow path.

**Day 12-13 — Implementer + hooks + write-locks.** Skill per §13.29.4; worktree lane creation (reuses §09.7.2.8 ops); test-path read-only mounts except declared skeletons; format/lint/typecheck hooks on write. *Done:* implementer turns one skeleton red→green on a toy task; a scripted attempt to edit a locked test file fails at the filesystem.

**Day 14 — assertion_delta + scope_check on integrity_server.** AST diff (libcst) flags removed/weakened/skipped assertions; scope_check vs frozen plan. *Done:* a deliberately weakened assertion fails the (stub) build gate with the node cited.

**Day 15 — build_gate + pr_opener → §09 pipeline.** Gate per §13.29.7 including the changelog-fragment requirement; PR body from the handoff template with mode-router hints and AC/design links; opened PR triggers the existing Code Review webhook. *Done:* **first upstream-authored PR reviewed by the downstream system end-to-end**, changelog fragment in the feature tree.

## Week U4 — SCR round-trip + v1.1.0

SCR schema + scr_router (mini spec-cycle: SpecWriter delta-revise, Consistency+Testability re-run, coverage re-check); human-approval routing per authoring-policy; implementer resume with updated slice; 3-SCR escalation. Consistency + Completeness (reverse-interrogation) + InterfaceImpact voters + fixtures. Dogfood: the feature specced in U2 implemented via the loop; at least one genuine SCR expected (if none occurs naturally, inject one via a deliberately ambiguous AC to test the plumbing — mark it synthetic in the trail). **Release v1.1.0** on the milestone gate.

## Week U5–U6 — Planning MAS → v1.2.0

U5: dag_check/lane_check/budget_check/blast_radius/estimate_calibrator (reads per-agent logs; cold-start returns `uncalibrated`); Planner writer + schema; the U3 plan re-check wiring (dag/lane re-run against final acceptance_refs, ADR-U07). U6: five Plan voters + fixtures; Gate U2 lock (plan file write-hook + coding-side frozen-plan reads); ESCALATE_ARCH_DECISION_NEEDED renders two candidate plans side-by-side in the HITL Issue. Lock-breach test: direct plan edit post-U2 must block the next task with the unratified-fork notice (§13.35.5 analog). **v1.2.0.**

## Week U7–U9 — Discovery + loops → v1.3.0

U7: research_server (credential-free, wrapped output, tainted-session lockout in harness — test: tainted run's L1 call rejected) + analytics_server + backlog_dedupe (reuses the §09.12.12 FAISS pattern over brief/spec embeddings). BriefWriter two-invocation flow (research → authoring). Preflight A/B harness on real PRs (advisory findings logged, never blocking; decision at U9 by acted-on-rate). U8: four Discovery voters + fixtures; hypothesis ledger + Gate U1 (interrupt for problem/tier/owner). U9: feedback loops — root_cause_stage labeling in the Stage-5 Leader (heuristic + weekly human spot-check queue), hypothesis-reconciliation weekly job wired into Maintenance, upstream STAR-L landing in the compounding PR. Reconcile one *already-shipped* feature's retro-written ledger as the live test. **v1.3.0.**

## Week U10–U12 — Hardening → v1.4.0 GA

U10: five upstream metrics computed from logs; authoring-policy loader ceilings + violation tests; cost lines in the weekly PR. U11: FMEA drills — scripted injections for §13.35.1/.2/.5/.6 verifying detection+recovery paths; replay CLI extended to upstream runs; benchmark: 10-artifact spec-quality set (hand-labeled) + first-pass-gate-rate baseline committed. U12: eight-stage traversal of one feature, docs public, retrospective; buffer absorbs overrun per the 20% policy. **v1.4.0** on §12.22.5 all-green.

---

## Appendix E — File tree delta (extends §10 Appendix C)

```
autoproduct/
├── agents/writer.py                      # §13.25.2
├── agents/upstream/{brief,planner,spec,implementer}*.py
├── orchestrator/upstream/{discovery,planning,spec,coding}_graph.py
├── orchestrator/conditionals_upstream.py
├── tools/spec/{ears_lint,coverage_matrix,schema_compile,quantifier_scan,invariant_diff}.py
├── tools/planning/{dag_check,lane_check,blast_radius,estimate_calibrator,budget_check,deploy_impact_probe}.py
├── tools/integrity/{assertion_delta,scope_check}.py
├── mcp_servers/{research_server,analytics_server,authoring_server}.py
├── harness/taint.py                      # tainted-session lockout §13.31.5
skills/upstream/*.md                      # 3 writers + 15 voters + implementer + preflight
features/{id}/...                         # §13.25.5 artifact layout
tests/integration/voters/fixtures/upstream/{voter}/*.yaml    # 120 at v1.4.0
tests/tools/{test_ears_lint,test_dag_check,test_assertion_delta,...}.py
.mas/{authoring-policy.yaml,spec-lint.yaml}
```

## Appendix F — Dependencies delta (extends §10 Appendix B)

`libcst` (assertion_delta AST diffs) · `jsonschema` (artifact schemas) — both pinned. design.md needs no new deps (section-presence check is markdown parsing). DAG/topo is hand-rolled (no networkx; ~40 lines, zero deps). Embeddings/FAISS, LangGraph, Celery, tree-sitter, pyright: already present, versions unchanged.

## Appendix G — Risk register delta (extends §10 Appendix D)

| ID | Risk | L×I | Mitigation |
|---|---|---|---|
| R-U1 | Upstream voters generate plausible-but-wrong critiques of prose faster than humans can audit | M×H | 80-threshold + verify pass + action-rate metric; fixtures from every human-marked-wrong finding |
| R-U2 | SCR friction pushes users to edit specs directly | M×M | Make the SCR path *faster* than the workaround (leader-approvable classes); §13.35.5 fork-refusal keeps the honest path the only working path |
| R-U3 | Estimate calibrator cold start misleads Gate U2 | H×M | `uncalibrated` labeling + widened human scrutiny flag; no invented numbers |
| R-U4 | Research server becomes an exfil/injection vector | L×H | Credential-free, no mounts, wrap, tainted lockout, verify-from-artifact |
| R-U5 | Lane model too rigid for hot shared files (schemas, routes) | M×M | Declared shared-file serialization lane (single lane owns hot files); revisit lanes_max |
| R-U6 | Upstream adds latency that pushes users back to vibe-coding for small changes | M×H | fast mode skips Discovery/thins Plan+Spec by design (§12.24.3); measure adoption |
| R-U7 | root_cause_stage labeling too noisy to trust metric 4 | M×M | Weekly human spot-check queue; report label-audit agreement alongside the metric |
| R-U8 | Two-track versioning (v1.0.0 core + v1.x upstream) confuses users | L×L | Single version line post-v1.1.0; README reading-order is authoritative |

## Appendix H — Glossary delta

**SCR** Spec Change Request — the only legal mutation of locked scope/spec/plan (§13.29.6) · **design.md** the Spec-stage architecture-delta artifact, human-acked at Gate U3 (§13.28.2, ADR-U07) · **Changelog fragment** per-task user-visible-change paragraph, rolled into release notes (§13.34.4) · **Lane** a worktree with an exclusive file-glob set, proven disjoint at Gate U2 · **Hypothesis ledger** append-only assumptions file, machine-reconciled post-launch (§13.26.5) · **Reverse interrogation** boundary-question probing inside the Spec Completeness voter (methodology reference) · **Tainted session** a run that consumed research output; L1+ tools locked (§13.31.5) · **NEEDS_PROBE** verify-pass branch resolved by a deterministic tool (§13.25.6) · **First-pass gate rate / SCR rate / estimate error / upstream-attributable findings / cost-per-artifact** the five upstream metrics (§13.33.1) · **U1–U4** the upstream gates (§13.32.1).
