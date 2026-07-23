# Security

## Reporting

This is a design-documentation repository; there is no running service here. If you find a security flaw **in the design** — a bypassable gate, an injection path the taint model misses, a way an agent could exceed its ceiling — open a GitHub issue with the mechanism anchored to the relevant sections (or use private vulnerability reporting if the finding could harm implementers before a fix lands). Design-level findings are treated as severity-critical inputs per the system's own FMEA discipline (09 Part 13, 13 Part 35).

## OWASP LLM Top 10 (2025) — control mapping

Where each risk category is addressed in the design. The consistent pattern: **structural impossibility over policy** (§08.1.7) — controls are filesystem mounts, subprocess boundaries, deterministic checks, and hardcoded ceilings, not prompt instructions.

| OWASP LLM Top 10 : 2025 | Framework controls |
|---|---|
| **LLM01 Prompt Injection** | All external content wrapped as untrusted data (§09.4.2.2); research server is credential-free with no filesystem mounts and its consumers lose L1+ tools for the session (taint lockout, §13.31.2, ADR-U03); the verify pass only accepts findings reproducible from the artifact itself — an injected "finding" dies at verification (§13.25.6). The architecture implements the dual privileged/quarantined-LLM pattern that [CaMeL (arXiv:2503.18813)](https://arxiv.org/abs/2503.18813) formalizes; value-level capability enforcement is the documented upgrade path (§16.40.2) |
| **LLM02 Sensitive Information Disclosure** | Per-tool RBAC via MCP allowlists (§11.17); analytics access is read-only with a query allowlist; no agent context ever contains credentials (servers hold their own scoped credentials); full audit logging of tool calls (§11.17.4) |
| **LLM03 Supply Chain** | `slopsquat_check` blocks hallucinated/typosquatted packages at write time (§09.7, §13.29.5); MCP servers are pinned and subprocess-isolated — the CVE-2025-6514 lesson (§11.17); dependency pins in the implementation plans (10 App. B, 14 App. F) |
| **LLM04 Data & Model Poisoning** | The compounding loop is the only learning channel: constraint-files-only scope, weekly human-reviewed PR, benchmark-gated rollback, append-mostly fixtures (§09.8.4, §13.32.3); learned-skill and dedupe registries are local and threshold-gated (§09.12.12) |
| **LLM05 Improper Output Handling** | Every agent output is schema-checked before anything consumes it: YAML finding contracts, artifact JSON Schemas (the fourth spec layer, §12.24.4-7, §13.25.5); deterministic gates sit between any generation and any effect |
| **LLM06 Excessive Agency** | Trust tiers with a hardcoded `forbidden_autonomous` ceiling the config cannot exceed (§09.11.5, §13.32.2); tool risk levels L0–L3 with L3 human-gated and L4 structurally absent from every server (§11.17); never auto-merge, never auto-deploy; per-task and per-file circuit breakers |
| **LLM07 System Prompt Leakage** | Low-stakes by architecture: skills and policies are public design documents by intent; no secret prompt material exists to leak — secrets live in servers, never in prompts |
| **LLM08 Vector & Embedding Weaknesses** | Retrieval stores (FAISS skill registry, backlog dedupe) are local, write-controlled through the governed learning channel, similarity-thresholded; retrieved content is data, never instruction (charter rule 13) |
| **LLM09 Misinformation** | Evidence classes on every factual claim (measured/sourced/assumed, §13.26.2); per-finding independent verification with NEEDS_PROBE routing opinions to tools (§13.25.6); charter rules 11–13 make fabricated evidence a strike-level violation, not a quality note |
| **LLM10 Unbounded Consumption** | Fail-soft budgets per stage and per task (§09.9.10, §13.32.2); per-agent call budgets and timeouts in every frontmatter contract; circuit breakers; weekly cost metrics with targets (§09.9.4, §13.33.1/.3) |

Dual-use posture (per Anthropic's 2026 trends report, trend 8): the same review/probe machinery that hardens code could be pointed offensively; this design constrains it by the ceilings above — the probes run only inside the review pipeline, against the team's own artifacts, under audit.

Execution surfaces (implementer worktree hooks, `test_exec`) run under OS-level sandbox isolation at scale — container minimum, microVM-class where available (§16.40.4). See also the multi-agent security survey ([arXiv:2505.02077](https://arxiv.org/abs/2505.02077)) for the threat landscape this mapping addresses.
