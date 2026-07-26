# PUBLISHING.md — publication status & remaining owner decisions

> **Status (2026-07-23): PUBLISHED** at
> [melodygaoyifan/autoproduct-design](https://github.com/melodygaoyifan/autoproduct-design),
> tagged `v2.0-docs`. Decisions resolved with the shipped defaults: MIT with
> the neutral holder "the autoproduct authors"; personal names kept
> (attribution). Both remain reversible per the notes below. The reference
> implementation lives at
> [melodygaoyifan/autoproduct-ai](https://github.com/melodygaoyifan/autoproduct-ai).

The bundle is publication-ready as shipped: `LICENSE` (MIT), `CONTRIBUTING.md`, `SECURITY.md` (OWASP LLM Top 10 : 2025 mapping), architecture diagram in the README (GitHub-native mermaid), the cited methodology reference included at `archive/external-reference-ai-mas-methodology.md` (all internal citations now resolve), and the validation/research-index doc (15). Two decisions remain yours; both are reversible and neither blocks publishing.

## Remaining decisions

**1. License holder / choice.** Shipped as MIT with the neutral holder "the autoproduct authors." Keep it, put your name in the copyright line, or swap the license entirely (Apache-2.0 adds a patent grant; CC-BY-4.0 if you view this strictly as documentation). One-file change.

**2. Personal names.** Currently kept (attribution is legitimate). If you prefer anonymity:

| String | Occurrences | Files |
|---|---|---|
| `Melody` / `melody` | 16 | 09, 10, 11, archive/day-0-v1 |
| `yifangao` | 1 | archive/day-0-calibration-v1.md |
| `M1 Max` | 1 | archive/day-0-calibration-v1.md |

```bash
sed -i 's/Melody/the maintainer/g; s/melody/the maintainer/g; s/yifangao/<user>/g' \
  09-system-design.md 10-implementation-plan.md 11-ultimate-architecture.md \
  archive/day-0-calibration-v1.md
```

`AgentHire` (~95×) is the running example project, kept deliberately and explained in the README — replace consistently only if it's a real product you'd rather not name. Note: the methodology reference in `archive/` is the original consolidated note in Chinese; that is authentic provenance, not a defect — mention it in the repo description if you like ("design distilled from a Chinese-language methodology note, fully translated into the numbered docs").

## Repo setup (copy-paste ready)

- **Name:** `autoproduct` (or your choice)
- **Description:** Design docs for a full-lifecycle multi-agent software development system: discovery → planning → spec → coding → review → test → deploy → maintenance. Spec-driven, harness-enforced, vote-don't-debate.
- **Topics:** `multi-agent-systems` `ai-agents` `spec-driven-development` `llm` `code-review` `software-engineering` `agentic-coding` `langgraph` `mcp` `frontend` `mobile` `gamedev` `wechat-miniprogram` `product-management` `growth` `experimentation` `generative-engine-optimization`
- **First release tag:** `v2.0-docs` — freezes a citable state; the change-control protocol (10 Part 11) governs evolution from there, linked from CONTRIBUTING.
- **Positioning line for the repo/social post:** independent 2026 production pipelines (CodeRabbit, Qodo Merge) converged on the same review shape this design specifies — trigger → context → adversarial verification → dedupe → policy engine → feedback loop (doc 15 §6).

## What was checked (so you don't re-check)

Currency (searches 2026-07-18): Anthropic 2026 Agentic Coding Trends Report, June–July 2026 production review-pipeline surveys, Jan-2026 agent-PR effort/abandonment research, plus verified technique adoptions — CaMeL (arXiv:2503.18813), GEPA (ICLR 2026 Oral, arXiv:2507.19457) with its MAS extension (arXiv:2606.23664) — all corroborate, none contradict; the live watch list is doc 16 §40.6. Findings audit: 45/45 session findings present, plus 3 corroborations, 6 technique-radar entries, and 7 domain-profile research entries covering web/小程序/mobile/game (doc 15 §6). Domain coverage check (查漏补缺) recorded at the end of doc 17: desktop = composition of existing profiles; data/ML and embedded named as future profiles, not silent gaps. Cross-references: all §12–§15 references resolve; Parts 22–37 contiguous after 08–11's Parts 0–21; the methodology-reference citations resolve to the included file.
