# 27 — Realtime & Streaming Deltas: Multiplayer Backends and Event Pipelines

Parts 79–80. Closes **gaps 2 and 3**: the game profile's missing netcode story, and the data profile's missing streaming story. Both land as ADR-U12 profile deltas — `realtime` composes onto the game or web profile; `streaming` composes onto the data-pipeline profile — reusing doc 26's perf slots, §17's bot machinery, and §18's idempotency pattern. Numbering: ADR-U32/U33, invariants 14.25–14.26, FMEA F-27.x.

---

## Part 79 — The realtime delta (games and realtime web)

### 79.1 The network model is declared, not discovered

`design.md` gains a mandatory field for realtime workspaces:

```yaml
net_model: server_authoritative | rollback | lockstep | relay_lockstep
tick_rate: 30            # simulation Hz
snapshot_policy: {full_every_n_ticks: 300, hash_every_n_ticks: 30}
```

The choice is a genuine architecture decision with well-mapped tradeoffs — lockstep for unit-count-heavy RTS, rollback where players expect it (fighting-class), server-authoritative for most everything else, relay variants to kill NAT pain and lag-switch abuse ([network-model selection guide](https://mas-bandwidth.com/choosing-the-right-network-model-for-your-multiplayer-game/)) — and the Spec voter treats a realtime FDR without a declared model as `ESCALATE_REQUIREMENT_CONFLICT`, because every downstream check below keys off it.

### 79.2 Determinism, extended to where it actually breaks

§17's determinism-first gate covered the test suite; rollback/lockstep models need *simulation* determinism, and the known leak sources are enumerable: floating-point divergence across platforms, unseeded or shared RNG, iteration-order dependence, inconsistent trig/math library results, mid-frame wall-clock reads ([Easel's netcode docs enumerate the same list](https://easel.games/docs/learn/multiplayer/rollback-netcode)). The delta adds `det_sim_scan` (deterministic): flags float equality/accumulation in simulation paths (fixed-point or integer math expected for rollback), non-injected RNG, `dict`/hash iteration in tick code, wall-clock reads inside the simulation. For `rollback|lockstep`, findings here are gate failures, not notes.

### 79.3 Input-record/replay is the first-class test primitive

The testable core of any deterministic netcode is: **same input stream ⇒ same state hash, every time, on every platform.** The delta makes that the fixture format — recorded input streams (plus, for prediction testing, recorded network-event timings replayed at *exactly* the same offsets, the technique the DelayNoMore projects use to make fluctuating-network behavior mockable ([DelayNoMoreUnity](https://github.com/genxium/DelayNoMoreUnity))) — and three checks over it:

| Check | What it proves |
|---|---|
| `replay_identity` | N replays of the same input stream produce byte-identical state-hash sequences (the §18 backfill-idempotency pattern, pointed at simulation) |
| `cross_build_replay` | the same stream on two consecutive builds diverges only where the diff says it should — silent behavior change is a finding |
| `desync_probe` | with `snapshot_policy.hash_every_n_ticks` enabled, a deliberately corrupted client is detected within the declared window |

**Invariant 14.26: a desync in any environment is an incident, never a nuisance** — the F-17.5 rule (flaky determinism = incident) extended to netcode, because the alternative is the desync bug that ships.

### 79.4 Load, latency, and the ugly parts of real networks

- **Connection-storm check:** reconnect logic must implement exponential backoff with jitter; `det_sim_scan` flags tight reconnect loops. The load scenario for it is a mass-disconnect/reconnect spike (server restart simulation) using doc 26's `perf_spike` slot over **fortio/ghz** for WS/gRPC.
- **Network-condition fixtures:** latency/jitter/loss profiles (e.g., `wifi_poor`, `mobile_4g`, `intercontinental`) applied via netem-class emulation ([standard tooling per the multiplayer networking resource list](https://multiplayernetworking.com/)); bot playtests (§17) run under each declared profile, and the FDR's playability AC states which profiles must remain playable.
- **Load-bot swarms:** §17's bot-playtest machinery scaled through doc 26's lane — N scripted bots per simulated room, rooms scaled until the capacity model's saturation point is found; `capacity.yaml` for realtime declares `concurrent_sessions` and `tick_budget` (p99 per-tick simulation cost × tick_rate < 1000ms, checked arithmetically from a VALID run).

**FMEA:** **F-27.1** prediction thrash under jitter (constant rollback-resimulate) → replay fixtures include jitter profiles; resimulation-depth p99 is a measured output with an AC ceiling (M×M). **F-27.2** reconnect stampede after server blip (H×M) → backoff check + spike scenario above. **F-27.3** state-hash check itself costs too much per tick → hash cadence is configurable and its cost is inside the tick budget measurement (L×M).

---

## Part 80 — The streaming delta (event pipelines)

### 80.1 ADR-U32 — Compatibility mode is declared, never defaulted; the contract check is a CI gate

**Decision.** Every schema-bearing topic in a streaming workspace appears in `.mas/stream-contracts.yaml` with an **explicit** compatibility mode; the word "default" is illegal in that file. Rationale is empirical: registry defaults disagree — Confluent defaults BACKWARD, AWS Glue defaults **DISABLED**, Apicurio defaults **NONE** — so an undeclared mode means an unknown guarantee ([Factor House, Kafka observability practices](https://factorhouse.io/articles/best-practices-kafka-data-observability)). The deterministic gate, `stream_contract_check`, runs in CI on any schema diff: compatibility test against the registered version (the `test-compatibility` pattern, ibid.), plus config lints — `auto.register.schemas=false` required for production configs (rogue-producer prevention), and **upgrade order derived from the declared mode** written into the deploy-review record: BACKWARD ⇒ consumers deploy first; FORWARD ⇒ producers first ([Confluent SR practices](https://www.confluent.io/blog/best-practices-for-confluent-schema-registry/)). *Rejected:* trusting the registry's default (see above); treating compatibility as a producer-team concern (the consumer six months from now, per the canonical 3 a.m. incident, is the party the gate protects).

**Enforcement-boundary honesty**, stated in the doc because pretending otherwise would be exactly the vice this repo exists to avoid: community Schema Registry enforces in the producer SDK only — anything speaking the wire protocol directly bypasses it. Broker-side validation is a paid feature (Confluent) or Redpanda's open-source Wasm transforms; where neither is available, the delta's compensating control is audit-tier message counting on contract topics (ibid.). The check declares which enforcement tier the workspace actually has; claiming a guarantee the tier can't provide is a finding.

### 80.2 Contracts beyond structure

Structure compatibility is necessary, not sufficient. For topics marked `contract: true`, the delta adopts the data-contract layer: semantics, quality rules, SLAs, and ownership per the Open Data Contract Standard (ODCS, PayPal-originated, now the Bitol project), with field-level validation rules (CEL-class, `isEmail`/`isUuid` style) and dead-letter routing on rule failure where the platform supports it ([Factor House](https://factorhouse.io/articles/best-practices-kafka-data-observability); [Confluent data-contracts docs](https://docs.confluent.io/platform/current/schema-registry/fundamentals/data-contracts.html)). Sensitive-field tags in the schema map directly onto §22.64's `user_data_taint` classes — the contract file is where the product's own PII lineage becomes machine-visible, extending the taint system from the framework's analytics to the built product's pipelines.

### 80.3 Delivery semantics and backpressure, reviewed not vibed

- **Exactly-once claims are typed:** an FDR/AC saying "exactly once" triggers a review checklist keyed to mechanism — transactional producer + read-committed consumer, or idempotent-consumer-with-dedupe-key — and a **replay verification**: reprocessing a bounded fixture slice must be byte-identical in effect (the §18 backfill-idempotency check, pointed at the consumer). No mechanism named ⇒ the claim downgrades to at-least-once in the spec, visibly.
- **Backpressure probe:** consumer-lag SLO declared per contract topic (`max_lag_seconds`); the probe runs producer-burst fixtures (doc 26 `perf_spike` shape) and checks lag recovery plus bounded-queue behavior — unbounded in-memory buffering in consumer code is a `det_sim_scan`-style static finding.
- **ADR-U33 — Streaming is a delta on the data-pipeline profile,** not a new profile: batch and streaming share the contract file, the taint mapping, and the idempotency machinery; only the checks above are additive. *Rejected:* a standalone streaming profile (it would fork the data-governance surface that most needs to stay single).

| Invariant | Statement | Enforced by |
|---|---|---|
| 14.25 | No schema change merges without a compatibility check against the registered version under an explicitly declared mode | `stream_contract_check` in CI; "default" is lexically rejected in `stream-contracts.yaml` |
| 14.26 | A desync (realtime) is an incident class, never a warning | §79.3; incident template pre-wired |

**FMEA:** **F-27.4** contract file drifts from actual registry state → nightly reconciliation job diffs registry vs file; drift = finding (M×M). **F-27.5** DLQ becomes a silent landfill → DLQ depth has its own lag SLO and shows in the Gate 6 health signals (M×H).

---
*Cross-references: §17 (bot playtests, determinism gate), §18 (idempotency, data-pipeline profile), §22.64 (taint), doc 26 (perf slots, capacity, VALID runs), doc 28 (environments for netem tiers). Research index rows land in doc 15 §6.*
