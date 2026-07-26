# Gap-Closure Index (docs 26–28)

Closes all five gaps from `capability-evaluation-complex-systems.md`. Canon numbering continues: Parts 77–83, ADR-U30..U35, invariants 14.24–14.28, FMEA F-26.x–F-28.x. No spine change anywhere — everything lands via the existing lane (§19), profile-delta (ADR-U12), and SCR mechanisms, which was the evaluation's own prediction.

| # | Gap (from evaluation) | Solution doc | Core mechanism | Scorecard flip |
|---|---|---|---|---|
| 1 | Performance & load lane — the largest hole | **26-performance-and-load-lane.md** | Lintable perf ACs (EARS extension); k6-first det slots (smoke/regression/soak/spike); ADR-U30 VALID/INVALID run typing with 5 validity preconditions; `capacity.yaml` checked arithmetically at Gate 5; seeded perf-defect manifest (N+1, missing index, unbounded pool, sync-in-async, O(n²) serializer) | high-traffic ❌ → review-level ✅ (empirical after P22 calibration) |
| 2 | Realtime / netcode | **27-realtime-and-streaming-deltas.md** Part 79 | Declared `net_model` + tick budget; `det_sim_scan` for determinism leaks; replay-identity fixtures (same inputs ⇒ same state hashes, the §18 idempotency pattern aimed at simulation); desync = incident (invariant 14.26); netem condition fixtures; WS reconnect-stampede spike check | multiplayer ❌ → ✅ (design) |
| 3 | Streaming data | **27-…** Part 80 | ADR-U32 declared-never-defaulted compatibility + CI contract gate (registry defaults disagree: BACKWARD/DISABLED/NONE); enforcement-boundary honesty (SDK-side is bypassable); ODCS-class contracts with PII tags → `user_data_taint`; exactly-once typed by mechanism + replay verification; backpressure probe | streaming D → ✅ (design) |
| 4 | Architecture evolution | **28-architecture-evolution-and-delivery.md** Part 81 | `arch_contract_check` compiled from `design.md` (import-linter / dependency-cruiser / ArchUnit per lane), run in the agent's verify loop; `.mas/deps.yaml` module graph mutated only via SCR-class channel (ADR-U34, invariant 14.27); Shopify-style checkpoint baseline for brownfield; product API SemVer (§74.2 turned outward) | B+ → A− (what layers *should* exist stays human) |
| 5 | Delivery hardening | **28-…** Part 82 | `.mas/environments.yaml` promotion DAG (perf runs must cite prod_mirror); ADR-U35 flag registry with category/owner/expiry, removal scheduled at creation, combination testing; expand–contract + `migration_rehearsal` (lock profile, reversibility round-trip) as Gate 5 precondition (invariant 14.28) | all ❌ rows → ✅ |

Alongside this edition: the README reading order and `15-validation-and-traceability.md` gained the corresponding rows (+3 completeness, +7 research-index). The originating capability evaluation is summarized in the table above; its scorecard column is the traceability record. Implementation track: P21–P26 in doc 28 §83.

Standing rule unchanged: every ✅ is a design-coverage grade until its seeded manifest or fixture run converts it to `primary_measured`.
