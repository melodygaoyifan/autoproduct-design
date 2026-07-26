# 20 — The Product Loop: Foundation, Opportunity Sensing, Market Analysis, PRD

Parts 52–56. Docs 08–19 build an **inner loop**: given a decided feature, take it from Discovery through Production Maintenance with bounded autonomy. This document opens an **outer loop** around it — *what should we build, is there a market, what is the product, and after launch, was any of it true.* The prior editions listed "Pricing, GTM, launch marketing" as out of scope (README). That exclusion is reversed here under **ADR-U19**, and reversed narrowly: the outer loop prepares evidence and options; humans still choose (§13.26.7 charter is extended, never weakened).

The whole design rests on one problem. In the inner loop, a hallucination is caught by something that fails: a test, a type checker, `ears_lint`, `slopsquat_check`. In the outer loop, an agent can invent a market size, a competitor's pricing, a "user complaint," or a channel's conversion rate, and **nothing fails**. Every gate goes green. Parts 52–53 exist to build the missing floor; Parts 54–56 are the stages that stand on it.

(Citation convention as everywhere: `§20.53` = Part 53 of this document. Marketing-side research lands in doc 21; feedback, attribution, and the loop closure in doc 22; the build plan in doc 23. **Naming disambiguation:** the outer-loop *stages* are P0–P5 and their gates are **Gate PL0–PL5**; `Gate P1` without the L is the pre-existing external-platform-review gate class of §17.41.3, unchanged and unrelated.)

---

## Part 52 — Why an outer loop, and why it is a separate loop

### 52.1 What the existing stages are not

Two existing mechanisms look like they already cover this. Neither does.

| Looks like it covers | Actually is | Gap |
|---|---|---|
| **Stage 1 Discovery** (§13.26) | Given a decided feature, research the codebase and solution space; emit a ProductBrief + hypothesis ledger | Its input is *a feature someone chose*. It never asks whether the feature should exist, or whether anyone will pay |
| **The compounding loop** (§09.8.4, §16.40.1) | Improves **the agents** — skills, fixtures, constraint files — weekly | Iterates the machine, not the product. A perfectly compounding system can spend a year shipping features nobody wants |
| **Stage 8 Maintenance** (§09.12) | Sentry/Datadog/PagerDuty signals → triage → root cause → fix PR | System health, not product health. A product with 100% uptime and 4% activation looks perfect to Stage 8 |
| **Hypothesis ledger reconciliation** (§13.34.3) | Discovery's assumptions become post-launch telemetry checks | The closest existing thing, and the correct seam to build on — but it reconciles *feature* hypotheses, not *product* or *market* hypotheses, and it has no channel or demand side |

### 52.2 Two loops, one spine

```
OUTER (weeks–months, WIP 1–2)                    INNER (hours–days, WIP per §16.38)
P0 Opportunity ─▶ P1 Market ─▶ P2 PRD ──────────▶ Stage 1..8 (docs 08–19, unchanged)
      ▲                                                      │
      │                                                      ▼  release
P5 Portfolio ◀── P4 Product Evidence ◀── P3 Launch & Growth ─┘
   │  kill / pivot / continue (human, Gate PL5)
   └──▶ back to P0 (pivot) or P2 (iterate) — never straight to Stage 4
```

**ADR-U19 — the product loop is a second loop, not six more stages on the spine.** Grounds: cadence mismatch of one to two orders of magnitude. Splicing P0–P5 into the eight-stage state machine would force one WIP budget, one gate-latency metric, and one checkpointer over processes that tick weekly and processes that tick hourly; §16.38's WIP limits assume a single characteristic time. *Rejected:* a 14-stage linear spine (breaks every `§13.x` cross-reference and every existing gate-latency baseline); *rejected:* running the outer loop as an unstructured human activity outside the framework (the fabrication problem in §20.53 is exactly what a framework is for).

The two loops meet at exactly two contracts, both machine-checked (§20.56.3, §22.65.4). Nothing else crosses.

### 52.3 What carries over unchanged

Everything structural. The outer loop is built from the same parts, which is the point of building it inside this framework rather than beside it:

- **generate → tools → critique-vote → verify → leader → gate** (§12.24.1) is the template for every P-stage. Single writer, parallel independent critique, no debate.
- **Deterministic before probabilistic** (ADR-U05). Parts 53 and 21.58 are the deterministic layer that makes this rule meaningful outside code.
- **Fixture gate at registration** (§11.19): 8 fixtures, ≥87.5%, no agent registers without passing. P-stage voters are held to it identically; §23 Appendix M lists the seed fixtures.
- **Trust tiers + `forbidden_autonomous` as a hardcoded floor** (§13.32). The outer loop *adds* to the forbidden list (§21.57.2) and removes nothing.
- **Research-session taint isolation** (§16.40.2, CaMeL-pattern). The outer loop reads far more untrusted web content than the inner loop ever did, and §21.60.4 shows the web is now actively adversarial toward retrieval agents. Taint is load-bearing here, not precautionary.
- **Profiles as deltas, never forks** (ADR-U12). Channel profiles (§21.59) reuse the mechanism verbatim.

---

## Part 53 — The evidence substrate: making product claims falsifiable

### 53.1 The problem, stated precisely

A code agent that writes `authClient.refreshToken()` when no such method exists gets a red test. A market agent that writes "the ATS-integration segment is roughly $2.4B growing 22% CAGR" gets nothing. Both are the same failure — **factual hallucination** (§01 taxonomy) — but only one has a detector. Worse, the market claim is *load-bearing*: it flows into the PRD, into scope-tier lock at Gate U2, into six weeks of Stage 4 coding.

The framework's answer is the same shape as `ears_lint`: make the artifact **machine-checkable**, then gate on the check. An unfalsifiable claim is the product-layer equivalent of an EARS criterion that says "fast."

### 53.2 The claim schema

Every quantitative or comparative assertion in a P-stage artifact is a typed record. Prose that is not a claim is prose; a claim that is not typed fails the lint.

```yaml
# claims/*.claim.yaml — one file per artifact, appended to, never rewritten
claims:
  - id: C-014
    text: "Mid-market ATS vendors expose bulk-export APIs in 3 of 5 cases"
    kind: market_structure          # market_size | market_structure | competitor_fact
                                    # | pricing | demand | channel_performance | user_need
    source_type: primary_measured   # ← the load-bearing field, enum below
    evidence:
      - method: api_doc_probe       # reproducible action, not a memory
        locator: "https://<vendor>/docs/api/exports"
        retrieved_at: 2026-07-24T11:04:22Z
        artifact_hash: sha256:9f21…      # snapshot in .mas/evidence/ (see §53.5)
    n: 5                            # required for any claim of form "k of n" or a rate
    confidence: 0.6                 # voter-assigned, not writer-asserted
    falsifier: "A 4th vendor without bulk export moves this to 3/6 — restate, don't defend"
    expires: 2026-10-24             # market facts rot; §53.6
```

`source_type` enum, strictly ordered:

| Value | Means | Admissible where |
|---|---|---|
| `primary_measured` | We ran the measurement. Our analytics, our holdout test, our instrumented probe | Anywhere. The only type that may ground a **causal** claim |
| `primary_cited` | A named first party stated it about itself, with a locator: a vendor's own pricing page, an SEC filing, a platform's own docs | Anywhere, subject to `expires` |
| `third_party_report` | An analyst, survey, or press figure, with locator and publication date | Context and sizing only. **Never** the sole ground for a scope-tier decision |
| `user_reported` | A real, identified artifact authored by a real user: a review, a support ticket, an interview transcript the human recorded | Need claims — and only from real artifacts (§53.4) |
| `model_inference` | The model reasoned it out | Permitted, must be labeled, capped by ratio (§53.3) |

### 53.3 `claim_lint.py` — the deterministic gate

Runs before any voter sees the artifact, per ADR-U05. Exit non-zero blocks the stage gate; there is no degraded mode (ADR-U09 spirit, §11.19).

```python
#!/usr/bin/env python3
"""claim_lint.py — structural validation of P-stage claim ledgers.
Deterministic. No model calls. Mirrors ears_lint's contract (§13.28.4):
exit 0 = clean, exit 1 = findings on stdout as JSONL, exit 2 = malformed input.
"""
from __future__ import annotations
import json, re, sys, datetime as dt, pathlib, hashlib

SOURCE_TYPES = {"primary_measured", "primary_cited", "third_party_report",
                "user_reported", "model_inference"}
CAUSAL = re.compile(r"\b(drove|caused|because of|led to|resulted in|due to)\b", re.I)
QUANT  = re.compile(r"(\d+(?:\.\d+)?\s*%|\$\s?\d|\b\d+(?:\.\d+)?\s*(?:x|×)\b|\bCAGR\b|\bTAM\b|\bSAM\b|\bSOM\b)")
VAGUE  = re.compile(r"\b(most|many|significant|substantial|leading|rapidly|huge|massive)\b", re.I)

# Ratio ceilings by artifact kind. Tunable in .mas/product-policy.yaml; these are the defaults.
MAX_INFERENCE = {"opportunity": 0.50, "market": 0.30, "prd": 0.20, "launch": 0.20}

def check(doc: dict, kind: str, today: dt.date) -> list[dict]:
    out, claims = [], doc.get("claims", [])
    if not claims:
        return [{"rule": "empty_ledger", "msg": "artifact has no claim ledger"}]
    infer = 0
    for c in claims:
        cid = c.get("id", "?")
        st = c.get("source_type")
        if st not in SOURCE_TYPES:
            out.append({"id": cid, "rule": "bad_source_type", "msg": f"{st!r} not in enum"})
            continue
        if st == "model_inference":
            infer += 1
        else:
            ev = c.get("evidence") or []
            if not ev:
                out.append({"id": cid, "rule": "unsourced", "msg": f"{st} requires >=1 evidence entry"})
            for e in ev:
                if not e.get("locator"):
                    out.append({"id": cid, "rule": "no_locator", "msg": "evidence lacks locator"})
                if not e.get("retrieved_at"):
                    out.append({"id": cid, "rule": "no_retrieval_time", "msg": "evidence lacks retrieved_at"})
                if st in ("primary_cited", "third_party_report") and not e.get("artifact_hash"):
                    out.append({"id": cid, "rule": "no_snapshot",
                                "msg": "cited external evidence must be snapshotted (§20.53.5)"})
        text = c.get("text", "")
        if QUANT.search(text) and st == "model_inference":
            out.append({"id": cid, "rule": "unsourced_number",
                        "msg": "quantitative claim may not be model_inference"})
        if CAUSAL.search(text) and st != "primary_measured":
            out.append({"id": cid, "rule": "causal_without_experiment",
                        "msg": "causal language requires primary_measured (holdout/experiment) — §22.63"})
        if VAGUE.search(text) and not QUANT.search(text):
            out.append({"id": cid, "rule": "unquantified",
                        "msg": "vague quantifier with no number — the claim-layer 'fast'"})
        if re.search(r"\b\d+\s+of\s+\d+\b|\brate\b|\bshare\b", text, re.I) and not c.get("n"):
            out.append({"id": cid, "rule": "no_denominator", "msg": "proportion claim without n"})
        if not c.get("falsifier"):
            out.append({"id": cid, "rule": "no_falsifier", "msg": "claim states no disconfirming observation"})
        exp = c.get("expires")
        if exp and dt.date.fromisoformat(str(exp)) < today:
            out.append({"id": cid, "rule": "stale", "msg": f"evidence expired {exp}; re-probe or downgrade"})
    ratio = infer / len(claims)
    ceiling = MAX_INFERENCE.get(kind, 0.30)
    if ratio > ceiling:
        out.append({"rule": "inference_ratio",
                    "msg": f"model_inference {ratio:.0%} > ceiling {ceiling:.0%} for kind={kind}"})
    return out

def main() -> int:
    try:
        path, kind = sys.argv[1], sys.argv[2]
        doc = json.loads(pathlib.Path(path).read_text()) if path.endswith(".json") else _yaml(path)
    except Exception as e:                                   # noqa: BLE001
        print(json.dumps({"rule": "malformed", "msg": str(e)}), file=sys.stderr); return 2
    findings = check(doc, kind, dt.date.today())
    for f in findings:
        print(json.dumps(f))
    return 1 if findings else 0

def _yaml(path: str) -> dict:
    import yaml                                              # pinned in §23 Appendix N
    return yaml.safe_load(pathlib.Path(path).read_text())

if __name__ == "__main__":
    raise SystemExit(main())
```

Five of these rules are worth naming because each kills a specific observed failure mode:

- `unsourced_number` — the invented TAM. The single most common outer-loop hallucination.
- `causal_without_experiment` — "our launch post drove 40% of signups." Attribution is not causation and rarely even correlation; §22.63 makes this rule empirical rather than pedantic.
- `no_denominator` — "3 of 5 vendors" with no n, or a "22% conversion rate" over 9 sessions.
- `no_falsifier` — forces the writer to state what would disconfirm the claim. A claim with no falsifier is a slogan.
- `stale` — a competitor's pricing page from four months ago is not evidence about today.

### 53.4 The synthetic-user prohibition

**Agents may not generate user needs.** They may only quote, cluster, and count real artifacts: app-store reviews, support tickets, community posts, sales-call notes, session recordings, interview transcripts a human actually recorded. The `user_reported` source type requires a locator that resolves to a stored artifact.

This is not squeamishness. Three converging reasons:

1. **It is the framework's existing charter.** §13.26.7 already forbids fabricating user evidence in Discovery; the outer loop is where the temptation is strongest, so the rule needs an enforcement mechanism, not just a sentence.
2. **The downstream consumer is a scope decision.** A synthetic persona quote is indistinguishable in form from a real one and will be read as evidence at Gate U2.
3. **In the marketing direction it is per-se illegal in the US.** The FTC's Operation AI Comply charged a *tool vendor* — Rytr — for supplying a service that generated consumer reviews and testimonials, on the theory that offering it was itself an unfair practice likely to pollute the market with fake reviews ([FTC, Sept 2024](https://www.ftc.gov/news-events/news/press-releases/2024/09/ftc-announces-crackdown-deceptive-ai-claims-schemes)). The 2024 amendments to the Endorsement Guides (16 CFR Part 255) reach AI-generated reviews and virtual endorsers directly. §21.58.2 carries this into a deterministic check; here it is a charter clause.

`synthetic_persona_scan` (a `claim_lint` companion, §23 Appendix M) flags first-person-singular quoted strings in P-stage artifacts whose locator does not resolve into `.mas/evidence/`. Voters are separately instructed that a persona is a *summary of counted artifacts*, always carrying its n, never a character.

### 53.5 Evidence snapshots, and why they are hashed

Every external citation is snapshotted into `.mas/evidence/<sha256>.{html,json,png}` at retrieval time, with the hash recorded in the claim. Three purposes, one of them not obvious:

- **Reproducibility.** A gate that cannot be re-run against the same inputs is theater.
- **Rot detection.** `expires` plus re-probe compares hashes; a silently-changed competitor pricing page is a finding, not a surprise.
- **Injection forensics.** The outer loop retrieves adversarial content by design (§21.60.4). When a claim turns out to have been planted, the snapshot is what lets the incident→fixture loop (§09.12) learn the pattern rather than just the instance.

Snapshots inherit `research_taint` (§16.40.2): content retrieved in a research session may enter claim ledgers as **quoted, hashed data** and may never reach a context that writes code or executes tools.

### 53.6 Evidence classes map to the existing ledger

The hypothesis ledger (§13.26.5) already carries measured/sourced/assumed. The claim schema is its refinement, not a replacement, and the mapping is fixed so §22.65.3 reconciliation can walk both:

| Ledger class | Claim `source_type` |
|---|---|
| measured | `primary_measured` |
| sourced | `primary_cited`, `third_party_report`, `user_reported` |
| assumed | `model_inference` |

---

## Part 54 — P0: Opportunity Sensing MAS

### 54.1 Charter and non-charter

**Does:** continuously ingest real signals from sources the operator already has standing to read, cluster them into candidate opportunities, and rank by a stated, inspectable function. **Does not:** decide what to build, scrape anything a robots policy or ToS forbids, contact anyone, or synthesize demand that no signal shows.

### 54.2 Signal sources, and the standing rule

An opportunity is only as real as its signal. Sources are declared in `.mas/signal-sources.yaml` and each carries a `standing` field — the reason we are allowed to read it. No standing, no source; the loader fails closed, matching `PolicyLoader` semantics (§11.19).

| Source class | Examples | Standing | Typed as |
|---|---|---|---|
| Owned support surface | Zendesk/Intercom tickets, in-app feedback, churn-survey free text | first-party, ours | `user_reported` |
| Owned analytics | Funnel drop-offs, feature non-adoption, search-with-no-results inside the product | first-party, ours | `primary_measured` |
| Public product feedback | App-store reviews, public issue trackers, changelogs of adjacent tools | public + official API/feed | `user_reported` / `primary_cited` |
| Community | Subreddits, forums, HN threads where the problem is discussed | public, read-only, API-respecting | `user_reported` |
| Demand proxies | Search-volume tools, job postings mentioning the workflow, integration-directory gaps | vendor API | `third_party_report` |
| Sales/CS notes | Lost-deal reasons, "can you also do X" requests | first-party, ours | `user_reported` |

The richest source is almost always the first two rows. A team running this loop against its own product and skipping owned signals in favor of web research has the ratio exactly backwards, and `claim_lint`'s inference ceiling will say so.

### 54.3 Roster and graph

Single writer, parallel critique — same template as every generative stage (§12.24.1).

```
signal_ingest (deterministic, MCP: signal_server)
   └── dedupe + cluster (embedding + deterministic near-dup) → opportunity candidates
        └── OpportunityWriter (single writer) → opportunities.md + claims/opportunity.claim.yaml
             ├── det_tools: claim_lint(kind=opportunity), synthetic_persona_scan, source_standing_check
             ├── voters (parallel, no cross-visibility):
             │     Signal-Strength · Novelty · Fit · Falsifiability · Duplication
             ├── verify pass (fresh agent, re-derives each finding from signals alone)
             ├── Leader → ranked candidate set with per-candidate evidence bundle
             └── Gate PL0 (deterministic): ranked set emitted, ledger clean, ≥3 candidates or BLOCKED
```

| Voter | Judges | Explicitly not |
|---|---|---|
| **Signal-Strength** | Volume, recency, source diversity, whether the cluster is n real artifacts or one loud thread | Whether the idea is good |
| **Novelty** | Whether this is already on the roadmap, already shipped, or already killed (reads the kill registry, §22.65.5) | Market novelty — that is P1's job |
| **Fit** | Distance from current product, stack, and stated strategy constraints in `.mas/strategy.yaml` | Desirability |
| **Falsifiability** | Whether each candidate states a testable demand hypothesis with a named cheapest test | Whether the hypothesis is true |
| **Duplication** | Cross-candidate overlap; merges near-identical framings | Ranking |

Note the deliberate absence: **there is no Desirability voter here.** Desirability is a market question and belongs to P1 with its own evidence discipline; putting it at P0 invites the model to reason its way to a conclusion before any market probe has run.

### 54.4 Gate PL0

Deterministic, no human. Passing means "a ranked candidate set exists and is well-formed," not "these are good ideas." Preconditions: `claim_lint` clean; every candidate has ≥1 non-`model_inference` claim; every candidate carries a falsifiable demand hypothesis and a named cheapest test; kill-registry checked. On repeated failure the stage escalates on the standard 3-fail pattern (§08.1.5).

---

## Part 55 — P1: Market & Viability MAS

### 55.1 What this stage refuses to do

Produce a market size by multiplying three numbers it made up. The top-down TAM is the outer loop's `authClient.refreshToken()`.

**Sizing discipline (enforced by `claim_lint` plus a Sizing voter):** every size claim must be bottom-up and decomposed into named, individually-sourced factors, each with its own `source_type`. A top-down figure may appear **only** as a `third_party_report` cross-check, labeled as such, and may never be the sole ground for scope-tier lock. If the bottom-up build requires a factor nobody can source, the correct output is `BLOCKED(MISSING_CONTEXT)` naming the unsourceable factor — the existing BLOCKED taxonomy (§09) carries over unchanged.

```yaml
# market/sizing.yaml — the shape claim_lint enforces for kind=market
sizing:
  approach: bottom_up
  factors:
    - name: addressable_orgs
      value: 4200
      source_type: primary_cited
      evidence: [{method: registry_query, locator: "…", retrieved_at: "…", artifact_hash: "…"}]
    - name: share_with_qualifying_workflow
      value: 0.35
      source_type: third_party_report        # allowed as a factor, flagged in the assumption list
      sensitivity: [0.20, 0.50]              # required whenever source_type != primary_measured
    - name: annual_contract_value
      value: 3600
      source_type: primary_measured          # our own closed deals
      n: 27
  result_range: [1.06e6, 2.65e6]             # computed from sensitivities, never a point estimate
  top_down_crosscheck:
    value: 8.0e6
    source_type: third_party_report
    note: "6x our bottom-up midpoint — divergence recorded, not reconciled by narrative"
```

Two structural rules: **the output is a range, never a point** (the sensitivity sweep is mechanical, `sizing_calc.py`), and **an unexplained divergence between bottom-up and top-down is a finding**, not something the writer smooths over in prose. The Sizing voter's job is to catch smoothing.

### 55.2 Roster

```
MarketWriter (single writer) → market.md + claims/market.claim.yaml + market/sizing.yaml
  ├── det_tools: claim_lint(kind=market), sizing_calc, competitor_probe, snapshot_differ
  ├── voters: Sizing · Competitive · Willingness-to-Pay · Regulatory · Distribution · Disconfirmation
  ├── verify pass (fresh agent; re-derives each finding from the snapshot bundle only)
  ├── Leader → viability assessment with explicit unknowns
  └── Gate PL1 (HUMAN) — see §55.5
```

| Voter | Judges | Named failure it exists to catch |
|---|---|---|
| **Sizing** | Bottom-up integrity, sensitivity presence, divergence handling | The invented TAM |
| **Competitive** | Whether each competitor fact is probe-derived and current; whether "no competitors" is a finding of absence or an absence of finding | The comforting empty quadrant |
| **Willingness-to-Pay** | Whether pricing claims come from published prices or observed transactions, never from a model's sense of what feels reasonable | Confusing "would be valuable" with "would be paid for" |
| **Regulatory** | Whether the product class touches regimes with hard gates (health data, financial advice, minors, employment decisions, cross-border transfer) | Discovering a compliance regime during Stage 7 |
| **Distribution** | Whether a plausible channel exists at all, and whether channel assumptions are `model_inference` (they usually are, at this stage — labeling is the deliverable) | A great product with no reachable buyer |
| **Disconfirmation** | Runs adversarially: given the same snapshot bundle, build the strongest case that this opportunity is *not* viable | Confirmation cascade across five agreeable voters |

**The Disconfirmation voter is the outer loop's answer to a specific structural risk.** Downstream voters critique an artifact that is already grounded in a diff; upstream market voters critique an artifact grounded in retrieved text, and retrieved text is selected by the same writer whose thesis it supports. A dedicated red-team seat with the same evidence and the opposite instruction is the cheapest available correction. It votes like any other voter — independently, no debate (P3, §08.2) — and its findings pass through the same verify pass.

### 55.3 Competitor facts are probes, not recollections

`competitor_probe` (MCP tool, T1 sandbox per §11.17) fetches and snapshots: public pricing pages, public changelogs/release notes, public API docs, public status pages, app-store listings. Every competitor claim in `market.md` must cite a probe artifact hash. A competitor claim with no probe is `model_inference` by definition and counts against the ratio ceiling — which, at 30% for `kind=market`, is deliberately tight.

Hard boundary, inherited from the browsing rules the framework already operates under: the probe reads what is public and API-permitted. It does not create accounts, defeat access controls, evade rate limits, or scrape where a robots policy or ToS forbids. `source_standing_check` fails the build if a source lacks declared standing.

### 55.4 Prompt injection is now the normal case

Docs 16 §40.2 adopted CaMeL-staged injection defense as a design posture. In the outer loop it is an operational necessity, because the retrieved corpus is being actively optimized *against retrieval agents* — the GEO industry described in §21.60 is that optimization, and its adversarial tail is documented in the literature: content crafted to manipulate LLM product visibility ([arXiv:2404.07981](https://arxiv.org/abs/2404.07981)) and single-page pollution sufficient to shift generative recommender output ([arXiv:2606.13610](https://arxiv.org/abs/2606.13610)).

Concretely, in P1:

- Retrieval runs in a **quarantined session** with no tool access beyond fetch+snapshot. Its output is data.
- The privileged session reads snapshots as **quoted values**, never as instructions, and cannot re-fetch.
- `injection_scan` flags imperative-mood and instruction-shaped content inside snapshots and marks the claim `contaminated`; contaminated claims may be quoted with the flag but may not ground a gate decision.
- A single source appearing across ≥3 unrelated claims triggers a **source-concentration finding** — the polluted-page failure mode in a form a deterministic check can see.

### 55.5 Gate PL1 — human, with a rubric

The first human gate in the outer loop, and it is human for the same reason Gate U2 is: this is a strategy decision with a compliance tail, and §41.2's rule holds — mechanize the core, name a human gate for the remainder.

```
Gate PL1 (human, structured rubric):
  entry:  claim_lint clean · sizing range with sensitivities · ≥1 probe per competitor claim
          · Disconfirmation findings verified and answered (answered ≠ dismissed)
          · regulatory findings triaged
  rubric: [1] Is the size range built bottom-up from factors I can each check?
          [2] What is the strongest disconfirming finding, and is the answer evidence or narrative?
          [3] Which factors are model_inference, and does the decision survive their sensitivity range?
          [4] Does any regulatory finding change the shape of what we'd build?
          [5] What is the cheapest test that would move me, and why aren't we running it first?
  outcome: pursue(scope_tier) | test_first(named cheapest test) | park(reason → kill registry) | reject
  forbidden_autonomous: this gate. Always. (§21.57.2 list)
```

Question [5] is the one that earns the gate. The framework's own posture — measure before you build — means the most common correct answer at Gate PL1 is `test_first`, which routes to a landing-page or concierge test through P3's experiment machinery (§21.61) *without* entering the inner loop at all.

---

## Part 56 — P2: Product Definition (the PRD)

### 56.1 PRD ≠ spec, and the boundary is enforced

The existing Specification stage (§13.28) emits `design.md`, EARS acceptance criteria, contracts, and module-spec deltas — *engineering* artifacts. A PRD answers different questions and must not answer Spec's questions, or the two drift and Gate U2's scope lock loses meaning.

| Question | Owner | Artifact |
|---|---|---|
| Who is this for, what problem, why now, why us | **P2** | `product/prd.md` |
| What does success look like numerically, by when | **P2** | `product/outcomes.yaml` |
| What we are deliberately not doing | **P2** | PRD non-goals |
| Which architecture, which modules, which interfaces | Stage 3 Spec | `spec/design.md` |
| `WHEN <trigger> the system SHALL <response>` | Stage 3 Spec | EARS ACs |
| Which tasks, which lanes, what estimate | Stage 2 Plan | task DAG |

`prd_lint` fails the gate if the PRD contains EARS-shaped sentences or names modules and interfaces — the PRD stating implementation is exactly how scope lock gets pre-empted before Gate U2 ever runs.

### 56.2 PRD schema

```yaml
# product/prd.yaml — machine-checked companion to prd.md (same pattern as spec.yaml/spec.md)
prd:
  id: PRD-2026-014
  problem:
    statement: "…"
    evidence_refs: [C-003, C-014, C-021]        # must resolve into the claim ledger
    affected_segment: {name: "…", size_claim: C-007}
  non_goals: ["…", "…"]                          # ≥2 required; a PRD with no non-goals is a wish
  outcomes:                                       # ≥1 required, each machine-checkable post-launch
    - id: O-1
      metric: activation_rate                     # must be in the metric vocabulary (§22.62.3)
      definition_ref: metrics/activation.md       # a metric with no written definition is not a metric
      baseline: {value: 0.11, source_type: primary_measured, n: 1840}
      target: {value: 0.18, by: 2026-11-30}
      instrumentation: {event: "workspace.first_export", exists: false}  # false ⇒ becomes a Plan task
  demand_hypotheses:                              # feed the hypothesis ledger (§13.26.5) verbatim
    - id: H-1
      statement: "…"
      falsifier: "…"
      check: {stage: P4, method: cohort, window_days: 30}
  scope_tier: standard                            # thin | standard | deep — sets the inner-loop budget
  kill_criteria:                                  # ← required; §22.65.2
    - "O-1 misses 50% of target lift after 2 full P-loops ⇒ mandatory Gate PL5 kill/pivot review"
  open_questions: ["…"]                           # explicit unknowns, not hidden in prose
```

Two fields carry unusual weight. **`instrumentation.exists: false`** mechanically converts an unmeasurable outcome into a Planning task — the framework's structural answer to shipping a feature whose success metric was never wired up, which is the single most common way a product loop silently stops being a loop. **`kill_criteria`** is required at definition time, before anyone is attached to the feature; §22.65.2 explains why authoring it later never works.

### 56.3 The outer→inner handoff contract

The first of the two contracts between loops (§52.2). Machine-checked at Stage 1 Discovery entry; a malformed handoff fails Discovery's DoR gate rather than being interpreted.

```yaml
# handoff/p2_to_stage1.yaml
handoff:
  prd_ref: PRD-2026-014
  prd_hash: sha256:…                    # Discovery pins the exact PRD it read
  claim_ledger_ref: claims/prd.claim.yaml
  hypothesis_seed:                      # merged into the Discovery hypothesis ledger, class-mapped per §53.6
    - {id: H-1, statement: "…", class: assumed, falsifier: "…"}
  scope_tier: standard
  outcomes_ref: product/outcomes.yaml   # Stage 8 + P4 both read this; single source
  constraints_inherited:                # from Gate PL1 regulatory findings — Spec may not weaken these
    - {kind: regulatory, rule: "…", ref: C-031}
```

The inverse contract — inner loop back to outer — is `release_to_p3.yaml` (§21.57.4), and the loop-closing one is `p4_to_p5.yaml` (§22.65.4).

### 56.4 Roster and Gate PL2

```
PRDWriter (single writer) → prd.md + prd.yaml
  ├── det_tools: claim_lint(kind=prd), prd_lint (EARS/module leakage, non-goals present,
  │              kill_criteria present, every outcome metric defined + instrumented-or-tasked)
  ├── voters: Outcome-Measurability · Evidence-Traceability · Scope-Discipline
  │           · Non-Goal-Adequacy · Hypothesis-Falsifiability
  ├── verify pass
  ├── Leader → PRD + open-question list
  └── Gate PL2 (HUMAN, brief): scope tier + kill criteria acknowledged; handoff emitted
```

Gate PL2 is human but deliberately *cheap* — the expensive human judgment was spent at Gate PL1. Its rubric is three questions: do the kill criteria bite (would this feature actually be killed if they fired), is every outcome measurable with instrumentation that exists or is now a task, and is the scope tier honest given the size range. The human-attention budget (§16.38.2) counts P1 and P2 against the same weekly ceiling as inner-loop gates; a product loop that consumes the whole budget starves the inner loop, and §22.66 tracks this as a first-class metric.
