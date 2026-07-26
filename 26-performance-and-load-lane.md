# 26 — The Performance & Load Lane: Making "High Traffic" a Checkable Claim

Parts 77–78. Closes **gap 1** of `capability-evaluation-complex-systems.md` — the largest hole in the canon: no load-test machinery, no lintable performance vocabulary, no capacity review, no perf regression baseline. After this doc, "survives load" becomes a claim with the same epistemics as every other claim in the framework: typed, measured, falsifiable, and impossible to assert without a run that reproduces.

Why it was absent until now is worth stating honestly: the canon was built around *correctness* gates, and under claim discipline an unmeasured perf property simply wasn't claimable — so nothing claimed it. That was consistent, but it made "high traffic" targets unreachable. This doc doesn't relax the discipline; it builds the measurement machinery the discipline requires.

Numbering: ADR-U30/U31, invariant 14.24, FMEA F-26.x. The lane follows the §19 lane pattern verbatim: det_tools slots, seeded-defect manifests, PROVISIONAL until calibrated.

---

## Part 77 — The lane

### 77.1 Performance requirements become lintable (EARS NFR extension)

§12's EARS grammar killed "the system should be fast" for functional requirements; this extends the same kill to performance. New AC pattern, machine-parseable:

```
UNDER <load-shape> THE SYSTEM SHALL <metric> <op> <value> [AT p<50|95|99>] [FOR <duration>]
```

Examples that pass the linter: `UNDER 200 rps open-model arrival THE SYSTEM SHALL http_req_duration < 300ms AT p95 FOR 10m` · `UNDER 2000 concurrent WebSocket sessions THE SYSTEM SHALL error_rate < 0.1% FOR 30m`. Examples that die at `quantifier_scan` (extended): "handles high traffic", "scales well", "low latency", "supports many users". The load-shape term is mandatory and must name an **arrival model** — open (rate-driven) or closed (VU-driven) — because the two answer different questions and conflating them is the classic way a test passes while production burns ([k6 practice guide](https://beefed.ai/en/api-load-testing-k6-guide); [2026 tools deep-dive](https://www.youngju.dev/blog/culture/2026-05-14-load-testing-tools-2026-k6-locust-vegeta-gatling-artillery-jmeter-comparison-deep-dive.en)).

Module specs (`.mas/specs/*.spec.yaml`) gain an optional `perf:` block carrying the same fields per endpoint; the Spec voter checks that any AC using the perf grammar has a corresponding spec entry, and — for profiles declaring `high_traffic: true` — that MVP-critical endpoints have perf ACs at all (absence is a finding, not a silence).

### 77.2 Tool slots (det_tools, §19 pattern)

Primary engine: **k6** — single static binary, thresholds evaluated in-script, non-zero exit on breach, which makes it a *deterministic gate with no glue* ([QAInsights 2026 comparison](https://qainsights.com/jmeter-vs-k6-vs-locust-in-2026-which-load-testing-tool-should-you-pick/); [QASkills k6-vs-Locust](https://qaskills.sh/blog/k6-vs-locust-2026)). Alternate lane: **Locust** for Python-ecosystem teams — real-Python scenarios and built-in master/worker distribution, but pass/fail must be enforced via exit-code wrapper since there is no native threshold gate (ibid.). Micro-bench niche (single hot endpoint, p99 regression on small diffs): wrk2/autocannon. Non-HTTP: **ghz** (gRPC), **fortio** (gRPC/WebSocket) — these matter for doc 27's realtime delta.

| Slot | When | Duration | Gate behavior |
|---|---|---|---|
| `perf_smoke` | on PRs touching perf-spec'd endpoints | 60–120s | k6 thresholds from the AC values; breach = REQUEST_CHANGES with the k6 summary attached |
| `perf_regression` | nightly + pre-release | 10–20m | compared against the **pinned baseline** via the existing `eval-gate` mechanism; regression beyond band = gate failure; re-pin only via PR |
| `perf_soak` | pre-release for `high_traffic` profiles | 4–8h | catches the slow-burn class — memory leaks, connection-pool drift, cache-eviction pathologies, cert refresh ([ARDURA 2026 guide](https://ardura.consulting/blog/load-testing-complete-guide-2026/)) |
| `perf_spike` | pre-release | 5–10m | burst arrival + cold cache; recovery-time-to-SLO is the measured output |

Per the §19 rule, the lane ships **PROVISIONAL** until its seeded-defect manifest is calibrated. The seeded perf defects (the analog of seeded security defects): an N+1 query, a missing index on a filtered column, an unbounded connection pool, a synchronous call inside an async handler, an O(n²) serializer on a list endpoint. A lane that cannot catch its own seeded defects has no business gating anyone's release — same bar as every other lane.

### 77.3 ADR-U30 — Perf results are typed, and validity preconditions gate whether a number exists

**Decision.** A load-test run emits a typed result: `VALID` (all preconditions met) or `INVALID_RUN` (any failed). Only `VALID` runs may update baselines, satisfy ACs, or ground claims; an `INVALID_RUN` is not a worse number — it is **not a number**. Preconditions, checked deterministically from the run's own telemetry before any metric is read:

1. **Generator not saturated:** load-generator CPU < 80%, zero `dropped_iterations`, no `http_req_blocked` spikes — generator exhaustion silently skews results toward optimism ([k6 hardware guidance via practice guide](https://beefed.ai/en/api-load-testing-k6-guide)).
2. **Measurement path matches user path:** the run declares its entry point; bypassing DNS/CDN to hit origin while the SLO includes the CDN invalidates the run ([tools deep-dive](https://www.youngju.dev/blog/culture/2026-05-14-load-testing-tools-2026-k6-locust-vegeta-gatling-artillery-jmeter-comparison-deep-dive.en)).
3. **Declared arrival model matches the AC's load-shape term** (open vs closed, §77.1).
4. **Environment parity declared:** the run names its environment from `.mas/environments.yaml` (doc 28); `perf_regression`/`perf_soak` require the production-mirror tier — localhost numbers can smoke-test scripts, never satisfy ACs.
5. **Percentile honesty:** results report p50/p95/p99, never mean-only; latency-under-coordinated-omission is measured with a rate-holding tool (wrk2-class) when the micro-bench slot is used.

*Rejected:* treating precondition failures as warnings (a warned-but-recorded number gets quoted; the only safe failure mode is nonexistence); mean-latency reporting (averages are how p99 pathologies hide).

### 77.4 The capacity model — `capacity.yaml`, reviewed at Gate 5

For `high_traffic` profiles, deploy review (§09.11) gains a required artifact:

```yaml
# .mas/capacity.yaml — per critical endpoint
- endpoint: POST /api/orders
  slo: {p95_ms: 300, error_rate: 0.001, availability: 0.999}
  traffic_model: {expected_rps: 120, peak_multiplier: 4, arrival: open}
  measured: {saturation_rps: 950, at: "2026-07-20", run: perf/runs/2026-07-20-sat.json}
  headroom_policy: "peak × 2 ≤ saturation"   # checked arithmetically
```

The check is deterministic: `expected_rps × peak_multiplier × 2 ≤ saturation_rps`, with `measured.run` resolving to a VALID run in-repo. A missing or stale (`measured.at` older than the last perf-relevant merge) entry is a Gate 5 finding. SLO + error budget framing follows current practice — p50/p95/p99 plus availability, budget governing ship speed ([ARDURA](https://ardura.consulting/blog/load-testing-complete-guide-2026/)) — but the framework only *records and checks* the budget; spending decisions stay human, consistent with every other resource in the canon.

### 77.5 ADR-U31 — The perf lane is a lane

**Decision.** Everything above lands via the §19 lane mechanism — det_tools slots, seeded manifests, PROVISIONAL rule, catch-rate publication under §74 reporting rules — and via ADR-U12 profile deltas (`high_traffic: true` is a profile flag, usable by web, game, data, or any future profile). No spine change; no new stage. *Rejected:* a ninth "performance stage" (perf is a property of existing stages' outputs, not a lifecycle phase; a separate stage would run after the decisions it should have informed).

---

## Part 78 — Bookkeeping

| Invariant | Statement | Enforced by |
|---|---|---|
| 14.24 | No performance claim — in ACs, capacity models, release notes, or the platform's own ledger — without a VALID run and in-repo baseline that reproduce it | ADR-U30 result typing; `eval-gate` baseline; ADR-U29 CI lint for the platform's own README |

**FMEA:** **F-26.1** generator saturation produces flattering numbers → precondition 1 is checked from run telemetry, not trusted from config (H×M). **F-26.2** environment drift makes baselines incomparable → baseline records environment fingerprint; mismatch = INVALID comparison, forced re-baseline via PR (M×M). **F-26.3** soak flakiness dismissed as noise → soak failures open incidents per the F-17.5 pattern (a flaky perf suite is an incident, not a nuisance) (H×M). **F-26.4** teams tune to the benchmark's load shape → seeded-defect manifest includes one *shape-shifted* scenario per calibration round (M×M).

**Metrics added:** VALID-run ratio (a low ratio means the harness environment is the problem); baseline re-pin frequency with PR links; time-from-regression-to-detection.

---
*Cross-references: §12 (EARS/quantifier_scan), §09.11 (Gate 5), §19 (lane pattern, PROVISIONAL), §74 (reporting rules), doc 27 (realtime reuses `perf_*` slots over WS/gRPC), doc 28 (`environments.yaml`). Research index rows land in doc 15 §6.*
