# Contributing

This repository is a design-documentation set for a full-lifecycle multi-agent development system. Contributions are welcome; the bar is the same one the docs hold themselves to: verified claims, structural fixes, honest limitations.

## How the docs evolve

All changes follow the change-control protocol in `10-implementation-plan.md` (Part 11): the newest **accepted** decision wins, and it must be recorded — as an ADR entry (docs 09 §14 / 13 §36 pattern), an errata note (the §12.24.4 pattern), or a delta section. Do not silently rewrite a superseded position; record why it changed. Documents 08–11 are canonical for the downstream stages, 12–15 for the upstream stages; cross-document conflicts are resolved by an explicit change-control entry, never by editing one side to match the other without a record.

## What's most useful to contribute

1. **Field reports.** You built some slice of this (a voter, the ears_lint gate, the coding loop) — what matched the design, what didn't, and the numbers (action rate, first-pass gate rate, cost). Open an issue with the doc-15 metric definitions; real calibration data beats any review comment.
2. **Fixtures.** A false positive or a miss you hit in practice, written in the fixture format (`13 §33.2` / `09 §9.11`): input slice, expected behavior, rationale. Fixtures are the repo's regression memory.
3. **Findings against the docs.** A contradiction between sections, a claim that drifted from its source, a gate that can be bypassed — anchored the way the system's own voters anchor: quote both locations, name the mechanism.
4. **Research updates.** New results that confirm, refine, or overturn an indexed finding (doc 15 §6). Follow the calibration rule below; overturning evidence is especially welcome — the watch list exists to be resolved.

## The citation calibration rule (non-negotiable)

Only verified sources are cited, with inline links to primary material. Industry-consensus claims are phrased as consensus, not attributed to a fabricated source. Numbers that are engineering defaults are labeled as defaults. A PR that adds an unverifiable citation will be asked to remove or reframe it — this is the documentation-level form of the system's own anti-hallucination charter (§08.1.7).

## Style

English throughout; practitioner tone; code is Python 3.11+ and runnable where shown; cross-references use the `§doc.part` convention. Keep additions delta-shaped — the spec-as-bureaucracy failure mode (§12.23.1) applies to this repo too.
