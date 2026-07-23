# 17 — Domain Profiles: Web, Mini-Program, Mobile App, Game

Parts 41–45. The core framework (08–16) is domain-generic but its worked examples skew backend. This document makes four client-side domains first-class — **web frontend, WeChat mini-programs (小程序), mobile apps, and games** — as **profiles**: composable deltas that plug domain-specific tools, voters, artifacts, budgets, and gates into the unchanged eight-stage spine. Profiles are not forks (ADR-U12); a monorepo may activate several at once. Citation calibration as everywhere: verified sources inline; platform limits are marked with a verify-at-release-time note where platforms have historically changed them. (Disambiguation: `§17.x` citations inside docs 09–10 refer to Part 17 of `11-ultimate-architecture.md`; this document is cited as `§17.41`–`§17.45`.)

---

## Part 41 — The domain profile mechanism

### 41.1 What a profile may add (and what it may not touch)

```yaml
# .mas/domain-profile.yaml — one entry per active profile
profiles:
  - id: web            # web | miniprogram | mobile | game (extensible)
    paths: ["apps/web/**"]              # profile applies where its globs match
    det_tools_add: [...]                # extra deterministic checks in det_tools/build_gate
    voter_deltas: [...]                 # new voter skills or target-additions to existing ones
    artifact_add: [...]                 # extra design.md sections, token files, baselines, manifests
    done_vocabulary: [...]              # legal machine_checkable_done commands for plan tasks
    nfr_vocabulary: [...]               # budget names + units the Spec stage may cite
    test_harness: {...}                 # how EARS ACs template into this domain's skeletons
    gates_add: [...]                    # e.g. external platform review (Part 41.3)
    forbidden_autonomous_add: [...]     # e.g. store submission
    fmea_refs: [...]
```

A profile may **add** checks, voters, artifacts, vocabulary, and gates. It may **not** remove or weaken anything in the core: gate preconditions, the verdict taxonomies, `forbidden_autonomous`, and the charter are floor, not default. The policy loader validates this structurally, the same way it enforces trust-tier ceilings (§13.32.2).

### 41.2 The one insight all four profiles share

Client-side quality splits into a **machine-checkable core** and an **irreducibly human remainder** — and the 2026 field data is unambiguous about where the line sits: AI agents excel at regression, smoke, cross-browser/device, visual-diff, and contract testing, and do **not** yet match human judgment on usability, exploratory evaluation, or "does this feel right" ([2026 QA-agent landscape](https://pctechmag.com/2026/04/best-ai-agents-for-software-testing-in-2026/)). The framework's response is the same in every profile: mechanize the core (lints, budgets, baselines, flows — all deterministic, all in `det_tools`/build gate), and give the remainder a **named human gate with a structured rubric** — the manual-UAT flag (§13.28.5) generalized. For games this is the playtest gate; for UI it is the visual acknowledgment at Gate U3 and pre-release. "Tests pass" never implies "ship" in any profile.

### 41.3 External platform reviews are gates the system doesn't control

Mini-program review, App Store review, and Play review are **external human gates with multi-day latency and opaque criteria**. Profiles model them as a first-class gate class:

```
Gate P1 (external platform review):
  entry: release-candidate artifact + platform preflight checklist 100% green
  latency: days (budgeted in the plan; a release train, not a merge queue)
  outcome: approved | rejected(reasons)
  on rejection: reasons are STRUCTURED INPUT — each becomes (a) a fixture for the
    preflight checklist where mechanizable, (b) a compounding-loop entry where not.
  forbidden_autonomous: submission itself (a human presses the button — always)
```

The preflight checklist is the mechanizable shadow of the platform's rules (permission prompts declared, privacy strings present, domain whitelist registered, package under limits); every historical rejection reason the team accumulates makes the shadow sharper. This is the incident→fixture loop (§09.12) pointed at a bureaucracy. **ADR-U14.**

---

## Part 42 — Web profile

### 42.1 Deterministic additions (det_tools + build gate)

| Check | Tool | Gate behavior |
|---|---|---|
| Lint/type | eslint + tsc (strict) | existing hook pattern |
| E2E flows | [Playwright](https://percy.io/blog/ai-visual-testing-tools) — the 2026 default; EARS ACs template to Playwright skeletons (`WHEN <trigger>` → actions, `SHALL <response>` → assertions) | task-scoped flows green |
| Visual regression | screenshot baselines: component-level via Storybook/Chromatic-class snapshotting for the design system; page-level Playwright `toHaveScreenshot` with thresholds + masked regions | diff over threshold = build-gate fail; **baseline updates are fixture updates** — they ride the compounding PR with before/after images, never silent re-baselines |
| Accessibility | axe-core scan (WCAG rules that are mechanizable) | serious/critical violations = fail; judgment-level a11y stays human (§41.2) |
| Performance budget | Lighthouse CI against Core Web Vitals budgets in spec | over budget = fail with the trace attached |
| Bundle budget | size-limit per entrypoint | over budget = fail |

Coverage discipline from the field: visual regression concentrated where risk is real — design-system components (high reuse, stable baselines), marketing/landing pages (layout *is* the product), checkout/payment flows — not sprinkled product-wide, which yields a noisy suite teams distrust within a quarter ([visual-testing field guidance, 2026](https://qtrl.ai/blog/visual-regression-testing-with-ai-2026)). The 2026 shift worth adopting as flows mature: visual checks as **mid-flow assertions** ("does this step look like a coherent checkout page") rather than only a post-hoc suite — the reviewer-agent form of this already exists in Stage 5's UI test generation; the profile makes it a build-gate option.

### 42.2 Voter deltas

**DesignFidelity voter** (new): judges the diff's rendered output against `spec/design.md`'s UI section + design tokens — token violations (hardcoded colors/spacing where tokens exist), component misuse (bespoke button beside the design-system button), breakpoint behavior contradicting the spec. NOT to flag: pixel taste beyond stated tokens/breakpoints. **A11ySemantics voter** (new): what axe cannot mechanize — focus order sanity, meaningful alt text, aria misuse that passes the scanner. **Performance voter** (delta to existing): N+1 render patterns, unmemoized hot paths, layout-thrash idioms — flags mechanism, cites the code, never restates the Lighthouse number the tool already caught.

### 42.3 Spec/NFR vocabulary

`design.md` gains a **UI section**: design-token file reference, breakpoints, component inventory (design-system components used vs newly introduced — new ones need a decision record), interaction states (loading/empty/error per view — the classic gap), and the visual-baseline list. NFR vocabulary: Core Web Vitals at p75 (LCP/INP/CLS with numbers), bundle KB per entrypoint, a11y level (WCAG 2.x AA mechanizable subset). An EARS AC citing "fast" still dies at quantifier_scan; this vocabulary is what it must use instead.

---

## Part 43 — Mini-program profile (小程序)

### 43.1 Platform constraints as deterministic checks

The platform's hard limits become build-gate checks, because review rejection or runtime termination is the alternative ([platform constraints](https://developer.tuya.com/en/docs/iot/development-and-publishment?id=Kabbsipvgmhxu), [practitioner constraint set](https://github.com/msitarzewski/agency-agents/blob/main/engineering/engineering-wechat-mini-program-developer.md); limits have shifted historically — the check reads current values from profile config, verified at release time):

| Constraint | Check |
|---|---|
| Package size: main and each subpackage ≤ 2MB; total commonly ~10MB with subpackage loading | `mp_size_check` on the compiled dist; over = fail with the treemap attached |
| Domain whitelist: every `wx.request`/upload/download/socket endpoint must be pre-registered; HTTPS mandatory | `mp_domain_check`: static scan of request targets vs the registered whitelist in profile config — an unregistered endpoint fails at build, not at review |
| Dual-thread architecture: no DOM; `setData` is the render bridge | `mp_setdata_lint`: oversized payloads, high-frequency calls in loops, full-object updates where diff-paths exist |
| Runtime memory 40–100MB by device/container; startup overhead 100–300ms before app code | perf budget vocabulary below; soak scenario in flows |
| Privacy APIs: user authorization before sensitive access; privacy declarations complete | `mp_privacy_check`: API-usage scan vs declared authorizations — the single most mechanizable class of review rejection |

E2E harness: WeChat DevTools' official automation SDK drives flows headlessly (miniprogram-automator-class control of the devtools instance); ACs template to flow scripts the same way as Playwright skeletons. Cross-platform note: teams compiling via Taro/uni-app run the same gate against **each compiled target's dist** — the framework treats each target as a lane-level build artifact, not a single build.

### 43.2 Voter deltas and gates

**PlatformFit voter** (new): capabilities assumed but absent in the container (no-DOM idioms leaking in from web code, forbidden/restricted APIs, share-surface assumptions like Moments-sharing that the platform disallows), subpackage-boundary sanity (a hot first-screen path importing a lazy subpackage). Gate P1 per §41.3: submission is human-only (`forbidden_autonomous_add: [platform_submission]`), rejection reasons feed the preflight fixtures — review-rejection patterns are exactly the accumulated-knowledge asset the compounding loop exists for. Release cadence is a **train** (review latency is days), so the plan's deploy_impact gains `platform_review: true` tasks that RiskSequencing places before consumer-visible deadlines.

---

## Part 44 — Mobile app profile

### 44.1 Deterministic additions

E2E default: [Maestro](https://qaskills.sh/blog/maestro-mobile-testing-guide-2026) — declarative YAML flows, drives the release build through the accessibility layer, built-in settle-and-retry (the largest single flakiness source removed by design); mature teams tier it with Espresso/XCUITest for platform-specific regression and Appium for cross-cutting hybrid coverage ([2026 framework guidance](https://www.vervali.com/blog/complete-guide-to-mobile-app-testing-2026-functional-performance-security-and-ai-assisted-testing/)). ACs template to Maestro flows. Device matrix as budget: a profile-configured tier list (e.g., 2 iOS + 3 Android spanning low/mid/high) run via device farm on release candidates; emulator-only green is not release-green — real-device gaps are the documented norm.

Performance budgets adopt the 2026 industry benchmarks as the NFR vocabulary defaults (spec may tighten, not vague-ify): cold start < 2s on mid-range (platform vitals flag ≥5s), iOS first frame < 400ms, battery < 5%/hr active, no unbounded memory growth in a 4-hour soak, p95 network < 2s on 4G critical paths. Crash-free-users SLO wires into the Maintenance stage's health gates like any §09.11 metric.

### 44.2 Voters, gates, and the signing wall

**DeviceReality voter** (new): notch/safe-area and foldable layout hazards, offline/poor-network behavior per AC, permission-prompt flows matching the declared manifest, background/lifecycle handling (the "works on emulator" class). Store review = Gate P1 twice (App Store, Play), each with its own preflight checklist (permission strings, privacy manifests/data-safety forms, screenshot/metadata completeness — a missing permission prompt is a documented single-point rejection). **Signing keys and store credentials sit behind the wall**: L3-class, never agent-readable, submission human-only. Rollout maps to the existing canary machinery: internal track → staged percentage rollout **is** §09.11's progressive delivery with the store as the delivery controller; halt criteria are the same health-gate metrics.

---

## Part 45 — Game profile

### 45.1 The split, at its sharpest

Games maximize §41.2's split: **"fun" is not machine-checkable, and everything around it is.** The May-2026 practitioner synthesis independently lands on this framework's exact posture — receipt-heavy supervised automation, agents on internal branches, kill switches and file limits, and *"human playtest gate always"*, naming the failure pattern this profile exists to prevent: *agent merges because tests pass; game is unfun* ([2026 game-agent field guide](https://gamineai.com/blog/future-of-ai-agents-and-autonomous-tools-2026)). The playtest gate is therefore a core gate here, not a manual-UAT footnote: a structured rubric (feel, difficulty, clarity, session intent), human-run, with agent-prepared builds, telemetry, and session summaries around it.

### 45.2 Machine-checkable core (deterministic additions)

| Check | What it catches |
|---|---|
| Headless simulation tests (engine test-runner; e.g. Unity Test Framework EditMode/PlayMode) | logic, systems, save/load round-trip |
| Determinism/replay check: fixed-seed replay produces identical state hashes | the nondeterminism that makes every other test flaky (F-17.5) |
| Frame budget: p95 frame time per target platform on benchmark scenes | perf regressions with the profile trace attached |
| Asset pipeline validation | missing references, texture/audio budget breaches, import-setting drift — asset bloat is the package-size problem at 100× scale |
| Bot playtests: scripted + agent-driven sessions overnight | crashes, softlocks, unreachable states, collision/clipping anomalies — the class 2026 tooling simulates at thousands-of-sessions scale ([AI playtesting landscape](https://aiconjured.com/ai-game-dev-tools/playtesting-qa/)) |
| Balance simulation | economy/difficulty curves vs design targets; deviations are *findings for the designer*, never auto-tuned |

Engine-native agent tooling (Unity AI open beta, May 2026 — state validation, scene snapshots, console reads) slots in as tools under the same MCP risk ladder; the field's early verdict that a custom MCP-based agent pipeline outperforms the built-in assistant for serious work is, conveniently, a description of this framework ([hands-on report](https://vindler.solutions/blog/unity-ai-open-beta)).

### 45.3 Voters, artifacts, loops

**GameplayIntegrity voter** (new): design-doc contradictions in mechanics code (design says 3 retries, code hardcodes 5), feel-critical constants changed without a design decision record, input-latency hazards on the hot path. **ContentPipeline voter** (new): asset-referencing code vs the asset manifest, localization keys, platform-variant completeness. `design.md` gains a **game design section** (core loop, feel targets as measurable proxies where possible — input latency ms, time-to-first-action — plus explicitly-human feel criteria for the rubric). The hypothesis ledger shines here: difficulty/retention hypotheses reconcile against playtest telemetry through the exact §13.34.3 machinery — balance learning becomes scheduled, not anecdotal. `forbidden_autonomous_add`: `balance_constant_changes` without a design decision record, `retail_branch_promotion`.

---

## 查漏补缺 — Coverage check after this document

| Surface | Status |
|---|---|
| Backend/services | Core framework's native ground (08–16 examples) — ✅ |
| Web frontend | Part 42 — ✅ |
| 小程序 | Part 43 — ✅ (Alipay/other super-app containers: same profile shape, different limit values — config, not new design) |
| Mobile apps (native/Flutter/RN) | Part 44 — ✅ |
| Games | Part 45 — ✅ |
| Desktop apps (Electron/Tauri) | **Composition, not a new profile**: web profile + packaging/signing deltas from the mobile profile (installer artifacts, auto-update as staged rollout). Named here so it isn't a silent gap. |
| Data/ML pipelines, embedded/firmware | **Explicitly future profiles** — each has a machine-checkable core (data contracts/eval sets; HIL test rigs) that fits the mechanism, but neither is researched to this document's standard yet. Listed as out-of-scope-with-a-path rather than covered-by-implication. |
| Design authorship | Still out of scope (README): profiles *consume* design specs and tokens and can verify fidelity against them ("product review" paradigm — agents diffing live UI against design files is production practice in 2026); *authoring* the design remains human/designer work. |

FMEA additions: **F-17.1** visual-baseline noise → suite distrust (thresholds+masks, coverage discipline, baselines-as-fixtures via PR); **F-17.2** platform rejection late in a train (preflight fixtures from every historical rejection; P1 latency budgeted in plan); **F-17.3** emulator-green/device-red (device-tier gate on RCs); **F-17.4** design-token drift (DesignFidelity voter + token lint); **F-17.5** nondeterminism poisoning the game test suite (determinism check is the *first* gate; a flaky game suite is treated as an incident, not a nuisance); **F-17.6** compiled-target divergence (per-target dist gating, §43.1).

**ADR-U12 — Domains are profiles, not forks.** One spine, delta configs; a profile may add, never weaken. *Rejected:* per-domain framework variants (divergence tax, quadruple maintenance). **ADR-U13 — Subjective quality gets a named human gate with a structured rubric; agents automate the harness around it, never the judgment.** Grounds: §41.2 field consensus; the game profile's "tests pass, game unfun" pattern. **ADR-U14 — External platform reviews are modeled as external gates feeding the compounding loop; submission is never autonomous.** Rejection reasons are structured learning input; the preflight checklist is their mechanized accumulation.
