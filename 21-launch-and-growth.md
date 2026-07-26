# 21 — P3: Launch & Growth MAS

Parts 57–61. This is the stage the prior editions explicitly excluded, and it is excluded no longer (ADR-U19). It is also the most dangerous stage in the framework, for a reason worth stating up front: **every other stage's worst failure is internal, and this stage's worst failure is external and irreversible.** A bad spec produces a bad PR that a gate catches. A bad marketing action produces a published false claim, a burned sending domain, a banned community account, or an FTC exposure — none of which a rollback fixes.

So the design is inverted relative to every prior stage. Elsewhere the question is "how much can we safely automate." Here the question is "what is the *most* the system may do without a human pressing the button," and the answer is: everything except pressing the button.

Research calibration: this document leans on primary sources where they exist (the KDD GEO paper, the FDR literature, FTC and Google's own policy pages) and on convergent practitioner reporting where the subject is platform behavior that no one publishes rigorously (deliverability thresholds, platform enforcement posture). Practitioner-sourced numbers are marked and are **config values with a verify-at-adoption note**, never constants in code — same discipline as the 小程序 platform limits in §17.43.

---

## Part 57 — The autonomy ceiling

### 57.1 Why publishing is never autonomous

Four independent lines of evidence converge on the same operating model, which is the strongest reason to adopt it:

1. **Platform terms.** LinkedIn's User Agreement prohibits automated access outside authorized interfaces and the official API; the prohibition has not loosened and enforcement has tightened. Reddit permits API-based interaction and prohibits browser automation, vote manipulation, and repeated unwanted promotion regardless of who or what clicks the button; community norms add subreddit-level self-promotion ratios that no API check will tell you about. Across the tooling ecosystem the recommended pattern converges on **draft-and-approve** — the tool finds the moment, drafts the post, a human approves before it publishes — with fully automated posting named as the fastest route to a ban ([Reddit-automation field guidance, 2026](https://okara.ai/blog/best-reddit-post-automation-tools); [LinkedIn ToS analysis, 2026](https://northlight.ai/blog/is-linkedin-automation-against-the-rules)).
2. **Regulator posture.** The FTC applies Section 5 and the amended Endorsement Guides (16 CFR Part 255) to AI-generated advertising content with no AI exemption; it has charged a vendor for *supplying* review-generation capability ([FTC, Operation AI Comply](https://www.ftc.gov/news-events/news/press-releases/2024/09/ftc-announces-crackdown-deceptive-ai-claims-schemes)). Sector regulators are explicit about agents specifically: FINRA's 2026 oversight report names AI agents as a distinct risk area because they act autonomously, can exceed intended authority, and create auditability problems when actions are not logged and reviewed.
3. **Search platform policy.** Google's spam policies define scaled content abuse method-agnostically — *generating many pages primarily to manipulate rankings, with little value to users* — and name generative AI as an example mechanism ([Google Search spam policies](https://developers.google.com/search/docs/essentials/spam-policies)). An agent optimizing a publish-rate metric is a scaled-content-abuse generator by construction unless something stops it.
4. **The framework's own precedent.** ADR-U14 already models external platform review (app stores, mini-program review) as an external gate with submission `forbidden_autonomous`. Publishing to a channel is the same class of act: irreversible, externally judged, reputationally cumulative.

### 57.2 `forbidden_autonomous` additions

Appended to the hardcoded ceiling in the policy loader (§13.32.2). As always, config may only *narrow* autonomy relative to this list; a config that tries to widen it fails startup.

```yaml
# .mas/authoring-policy.yaml — P-stage additions (loader-enforced floor)
forbidden_autonomous_add:
  - publish_external            # any post, article, page, or reply on any external surface
  - send_outbound               # any email/DM to a person, including one message
  - modify_public_property      # site copy, pricing page, app-store listing, docs marketing pages
  - respond_as_brand            # replies to reviews, support-visible community threads
  - create_or_authenticate_account   # already global; restated because growth tooling invites it
  - spend_money                 # paid acquisition and all budget actions — §57.3
  - contact_list_construction   # assembling person-level outreach lists — §22.64
  - platform_submission         # inherited unchanged from ADR-U14
```

### 57.3 Paid acquisition is out of scope, on purpose

**ADR-U20 — the framework does not spend money.** No bid management, no budget allocation, no campaign spend of any kind, in any tier, ever. Grounds: (a) spend is the one action class where an agent error compounds continuously and silently — an unattended loop with a bidding tool is an unbounded-loss device, and the framework's circuit breakers are designed around *review* cost, not *cash* burn; (b) the framework's whole safety posture is "the worst case is a wasted review cycle," which spend authority breaks; (c) organic and owned channels are where a small team's leverage actually is. *Rejected:* spend with a hard cap (a cap bounds the loss but not the mechanism, and every incident report in this class begins with a cap that was configured wrongly). Teams that want paid acquisition should run it outside this system; the framework will happily *measure* it (§22.63) and refuses to *operate* it.

### 57.4 The inner→outer handoff

```yaml
# handoff/release_to_p3.yaml — emitted at Stage 7 deployment review approval
release:
  prd_ref: PRD-2026-014
  changelog_refs: [product/changelog/*.md]     # per-task fragments, §13.34.4 — already exist
  outcomes_ref: product/outcomes.yaml
  instrumentation_verified: true               # ← Gate PL3 precondition; false = BLOCKED
  claims_available:                            # what marketing is permitted to say, and no more
    - {id: C-101, text: "exports 12k rows in under 4s", source_type: primary_measured,
       evidence: [{method: benchmark_run, locator: "…", artifact_hash: "…"}]}
  rollout: {kind: canary, stage: 10pct}        # §09.11 canary state — copy must not outrun exposure
```

`claims_available` is the substantiation register. **P3 may not assert a product capability that is not in it.** This single field converts "don't make unsubstantiated claims" from an instruction into a lookup, which is the difference between a guideline and a gate.

---

## Part 58 — Deterministic marketing backstops

Per ADR-U05, deterministic checks run before any voter. In code review that layer is Semgrep, Bandit, `slopsquat_check`, `csrf_ssrf_probe`. Here it is seven checks, each aimed at a specific, documented, expensive failure. They run in `marketing_server` (MCP, T1 subprocess sandbox per §11.17) and their union is the P3 build gate.

### 58.1 `claim_substantiation_check`

Every product-capability assertion in a draft must resolve to a `claims_available` entry, and every quantitative assertion must match the registered value within a stated tolerance. Unresolvable assertion = build-gate failure with the sentence quoted.

```python
def check_substantiation(draft_text: str, register: dict, tol: float = 0.0) -> list[dict]:
    """Every capability/quantitative sentence must map to a registered, evidenced claim.
    Unmapped assertions fail closed — the register is the whitelist, not a hint."""
    findings = []
    for sent in split_sentences(draft_text):
        if not asserts_capability(sent) and not QUANT.search(sent):
            continue
        hit = match_register(sent, register)          # entity+predicate match, not fuzzy string
        if hit is None:
            findings.append({"rule": "unsubstantiated", "sentence": sent,
                             "msg": "no claims_available entry supports this assertion"})
            continue
        for n_draft, n_reg in paired_numbers(sent, hit):
            if abs(n_draft - n_reg) > tol * max(abs(n_reg), 1e-9):
                findings.append({"rule": "number_drift", "sentence": sent,
                                 "msg": f"draft says {n_draft}, register says {n_reg}"})
        if superlative(sent) and hit.get("source_type") != "primary_measured":
            findings.append({"rule": "unmeasured_superlative", "sentence": sent,
                             "msg": "comparative/superlative requires primary_measured evidence"})
    return findings
```

`unmeasured_superlative` deserves its own rule because "fastest," "most accurate," and "the only tool that…" are comparative claims about *third parties*, requiring evidence about products we do not control. In practice the correct output is almost always to delete the superlative.

### 58.2 `disclosure_lint`

Checks that required disclosures are present, in the content itself rather than a link, and in the channel's required form. The rule set is config-driven per jurisdiction and channel because this area is moving fast; the check is what makes it enforceable.

| Trigger | Required | Basis |
|---|---|---|
| Content is substantially AI-generated and is advertising | AI-involvement disclosure per configured jurisdiction ruleset | FTC Section 5 deception analysis; state disclosure statutes; EU AI Act transparency duties for synthetic content |
| Any endorsement, testimonial, review, or first-person experience claim | **Hard fail** unless the artifact resolves to a real, identified endorser with a recorded material-connection disclosure | 16 CFR Part 255 as amended (2024) reaches AI-generated reviews and virtual endorsers; fabricated reviews are per-se deceptive |
| Affiliate or paid relationship | Material-connection disclosure in caption *and* in content | Endorsement Guides — link-in-bio placement is not disclosure |
| Results/outcome claim ("teams save 6 hours/week") | Typical-results basis in register, or a typical-results qualifier | Endorsement Guides on atypical results |
| Regulated vertical flagged at Gate PL1 | Jurisdiction ruleset from `.mas/compliance-profile.yaml`; approval routed to the named human reviewer | FINRA 2210 / SEC marketing rule / sector equivalents |

The second row is the one the framework enforces hardest, and it is enforced as a **structural impossibility rather than a caution**: §20.53.4 forbids synthetic user artifacts at the source, so there is no path by which a testimonial can reach a draft. `disclosure_lint` is the second line, catching first-person experience prose that the writer generated directly.

*Verify-at-adoption:* per-violation penalty figures, state statutes, and the EU AI Act's applicable dates circulate widely in secondary sources with inconsistent details. `.mas/compliance-profile.yaml` carries the ruleset with a `verified_on` date and a review cadence; nothing in code hardcodes a legal threshold. Treat this table as the *shape* of the obligation and confirm the specifics with counsel for the operator's jurisdiction — the framework's job is to make the check runnable, not to give legal advice.

### 58.3 `deliverability_preflight`

For any email artifact, before a human is even asked to approve. Every threshold is a config value; the checks are structural.

| Check | Fails when | Note |
|---|---|---|
| Authentication | SPF, DKIM, DMARC not all present and aligned for the sending domain | Bulk-sender requirements at the major mailbox providers have moved from advisory to enforced since Feb 2024; non-compliant mail is increasingly rejected rather than filtered |
| One-click unsubscribe | `List-Unsubscribe` + `List-Unsubscribe-Post` (RFC 8058) absent on any marketing-class message | Required for bulk marketing mail |
| Complaint-rate headroom | Trailing complaint rate above the configured operating ceiling | Provider ceiling widely reported at 0.30% with a practical operating target near 0.10%; configured, not hardcoded |
| Bounce rate | Above configured ceiling (commonly 2%) | Same |
| Domain warmth | Sending domain age/volume ramp below configured schedule | An unwarmed domain at agent volume degrades placement within weeks |
| Per-mailbox volume | Above configured daily cap | Practitioner consensus clusters at 50–100/mailbox/day for cold classes |
| List provenance | Any recipient lacking a recorded lawful basis and provenance record | §22.64; this check is a **hard fail with no override**, unlike the tunable ones above |
| Suppression | Any recipient on the unsubscribe/complaint suppression list | Hard fail |

The last two rows are categorically different from the rest. Placement thresholds are operational hygiene; consent and suppression are legal obligations (CAN-SPAM, GDPR/PECR, CASL depending on jurisdiction) and are not tunable.

### 58.4 `spam_policy_check`

Aimed at Google's scaled-content-abuse definition rather than at "AI content," because that is what the policy actually says: the violation is *volume plus manipulation intent plus low added value*, method-agnostic, and it now governs AI Overviews and AI Mode surfaces as well as blue links.

| Signal | Fails when |
|---|---|
| Publish rate | Pages/period above the configured ceiling for the property, or any burst pattern |
| Template similarity | Pairwise near-duplication above threshold across the batch (shingling + embedding, both deterministic given fixed models) |
| Original-contribution floor | Draft contains no `primary_measured` claim, no original data, no first-party artifact — i.e. it is a restatement of retrieved material |
| Query-variant fan-out | Multiple pages differing only in a targeted phrase |
| Thin-page ratio | Share of the property below a configured substance threshold |
| Editorial attestation | No named human reviewer recorded for the page |

The **original-contribution floor** is the interesting one, and it is where the framework's structure pays off unexpectedly: a system that already types every claim by source can mechanically require that a published page contain at least one thing we measured ourselves. That is a check almost nobody can run, and it is nearly free here.

### 58.5 `brand_and_safety_scan`

Deterministic pattern layer, LLM voter second (ADR-U05 ordering): banned-claim phrases from the compliance profile; competitor-name mentions (routed to a review flag — comparative advertising has its own substantiation duty); token/voice violations against `brand/tokens.yaml`; PII in outbound copy; unresolved template variables (`{{first_name}}` shipping literally is the canonical embarrassment); dead or unrouted links; UTM well-formedness (§58.7).

### 58.6 `geo_extractability_check`

Structural preconditions for being *retrievable and citable* by generative engines, all of them mechanical (the strategy layer is §60):

- Crawler access: `robots.txt` and CDN bot rules actually permit the AI crawlers the operator intends to allow — a check that exists because the default-deny direction of some CDN configurations silently removes a property from the corpus.
- Structured data validity; canonical correctness; passage-level extractability (question-shaped headings, short factual statements, self-contained passages rather than claims that depend on three paragraphs of context).
- Every statistic on the page carries an inline source; the page names an author with a resolvable identity.
- Freshness metadata present and truthful.

### 58.7 `utm_and_instrumentation_lint`

Boring, and the reason P4 has data at all: UTM grammar against a fixed taxonomy; no PII in URL parameters ever (this is also the standing privacy rule, §22.64); every asset's conversion event exists in the analytics schema before publish; every experiment arm carries its assignment parameter. A campaign that ships without instrumentation cannot be evaluated, and an outer loop that cannot evaluate is not a loop.

---

## Part 59 — Channel profiles

Channels reuse the domain-profile mechanism verbatim (ADR-U12): a profile may **add** checks, voters, artifacts, gates, and forbidden actions; it may never remove or weaken. Same loader, same structural validation.

```yaml
# .mas/channel-profile.yaml
channels:
  - id: content_geo
    surfaces: ["site/blog/**", "site/docs/**"]
    det_tools_add: [spam_policy_check, geo_extractability_check, claim_substantiation_check]
    voter_deltas: [Extractability, OriginalContribution]
    cadence: {max_publishes_per_week: 2}        # a ceiling, never a target — §59.5
    gates_add: [PL3-editorial]
    forbidden_autonomous_add: [publish_external]
```

| Profile | Deterministic adds | Voter adds | Human gate | Distinctive rule |
|---|---|---|---|---|
| **content_geo** | `spam_policy_check`, `geo_extractability_check` | Extractability, OriginalContribution | Editorial approval, named reviewer recorded | Original-contribution floor; publish-rate ceiling |
| **email** | `deliverability_preflight`, suppression + consent checks | Consent-Basis, Relevance | Send approval per campaign, batch-scoped | Consent and suppression are hard fails; §22.64 governs list construction |
| **community** (Reddit/HN/Discourse/forums) | Subreddit-rule fetch, self-promo ratio tracker, account-history check | Norm-Fit, Value-First | Post approval, per post | Official API only; browser automation forbidden; a community account that is mostly self-promotion is a policy violation *and* a strategy failure |
| **social** | Rate/burst limits, disclosure lint, no-persona check | Voice, Disclosure | Post approval, per post or per batch | No synthetic persona accounts, ever — an AI account presenting as a person is deceptive under the Endorsement Guides and is impersonation under most platform rules |
| **product_surface** (in-app copy, onboarding, changelog, docs) | Same as content plus i18n key checks | Clarity, Accuracy | Rides the normal PR gates | **The only channel where an agent may write and merge through the normal inner loop** — it is code, reviewed as code |
| **paid** | — | — | — | **Not implemented.** ADR-U20 |

### 59.5 Cadence ceilings are ceilings

Every channel profile carries a maximum, and none carries a minimum. This is deliberate and structural: a publish-rate *target* handed to an optimizing agent is a scaled-content-abuse generator with a KPI. The framework's compounding loop already defends against reward gaming with a three-layer defense (§09.8.4); here the defense is simpler — there is no rate reward to game, and quality gates are the only thing an agent can pass.

---

## Part 60 — The GEO sub-profile

### 60.1 Why this gets its own Part

Search intermediation changed, and the framework's own users are exactly the people who will otherwise write a "SEO agent" that violates §58.4 on day one. The discipline named by [Aggarwal et al., *GEO: Generative Engine Optimization*, KDD 2024 (arXiv:2311.09735)](https://arxiv.org/abs/2311.09735) is now the mainstream framing, and its central experimental result is unusually well-aligned with this framework's values: across a 10k-query benchmark, the interventions that raised visibility in generative-engine responses were **adding statistics, citing sources, and including quotations** — up to roughly 40% relative improvement — while classical keyword-density signals showed minimal influence.

That finding is why GEO is admissible here at all. The tactics that work are the tactics that make a page more verifiable. A framework that types every claim by source and requires an original measurement per page is, incidentally, a GEO-optimized content generator — and the same discipline is what keeps it on the right side of §58.4.

### 60.2 What the profile does

- **Passage-level structure.** Optimize for *selection during synthesis*, not page ranking: question-shaped headings, direct answers in the first sentences, short self-contained factual statements, tables that survive extraction.
- **Statistics and citations as a build requirement.** `geo_extractability_check` already fails a page whose statistics lack inline sources — the GEO tactic and the honesty gate are the same check.
- **Entity clarity.** Consistent naming, structured data, resolvable author identity.
- **Retrievability hygiene.** Crawler permissions verified as a check, not assumed.

### 60.3 Measurement, and its instability

The correct posture toward GEO measurement is unusual and worth encoding, because the naive version produces exactly the false confidence §20.53 exists to prevent. Generative-engine answers are stochastic, personalized, and time-varying; the literature on measuring visibility in AI search is explicit that single-shot measurement is not a measurement ([arXiv:2604.07585](https://arxiv.org/abs/2604.07585)). The profile therefore requires:

- **Repeated sampling** over a fixed prompt set, on a schedule, with n recorded on every reading.
- **Interval reporting.** A citation-share figure without an interval fails `claim_lint`'s `no_denominator` rule.
- **`source_type: primary_measured` only for our own sampling harness**; any vendor's "AI visibility score" is `third_party_report`.
- **No causal attribution from correlation.** "Our GEO work drove the citation lift" is a `causal_without_experiment` failure unless it came from a holdout (§22.63).

### 60.4 Forbidden tactics — and why they are in the code, not the style guide

The adversarial branch of this literature is real, effective, and squarely out of bounds: prompt-injection-style content designed to manipulate LLM product visibility ([arXiv:2404.07981](https://arxiv.org/abs/2404.07981)) and the demonstration that a single polluted page can shift generative recommender output ([arXiv:2606.13610](https://arxiv.org/abs/2606.13610)). Google's spam policies now explicitly cover AI Overviews and AI Mode, extending cloaking, doorway, scraping, and scaled-content rules onto the generative surface.

**ADR-U21 — retrieval manipulation is forbidden by construction, not by policy text.** The banned set: text targeted at model retrieval rather than readers (hidden, cloaked, or off-screen); instruction-shaped content aimed at the reading model; fabricated entity associations via structured data; synthetic authorship or fake expert profiles manufactured for E-E-A-T signals; mass query-variant page generation; planting claims in third-party sources for retrieval. Enforcement is mechanical: `geo_extractability_check` fails on visibility-mismatched text, `injection_scan` (§20.55.4) runs on *our own* drafts as well as retrieved content, and `spam_policy_check` catches the fan-out patterns.

The self-referential argument is the one that should persuade a skeptical operator: this framework's own P1 stage is a retrieval agent whose integrity depends on the corpus not being poisoned (§20.55.4). A system that pollutes the corpus for its own product while depending on a clean corpus for its own research has an incoherent design, not merely an unethical one.

---

## Part 61 — The experiment MAS: launch as a set of tests

### 61.1 The problem, in numbers

Marketing is where an agent's ability to generate variation meets a statistical trap, and the trap is quantified. Analyzing 4,964 effects across 2,766 experiments on a large commercial A/B platform, Berman and Van den Bulte find the **false discovery rate is 18–25% at 5% significance and 28–37% at 10%**, driven mainly by the fact that roughly **70% of tested effects are true nulls** rather than by low power — so about **one in five interventions that reach significance at 5% is ineffective when deployed** ([*False Discovery in A/B Testing*, Management Science](https://pubsonline.informs.org/doi/10.1287/mnsc.2021.4207)). The companion work finds roughly 57% of experimenters p-hack by stopping at the moment of significance, pushing FDR from about 33% to 42%.

Now add an agent that generates twenty subject lines. Multiple comparisons and continuous monitoring both inflate error rates in well-understood ways; peeking at accumulating data without a sequential design invalidates fixed-horizon inference ([Johari et al., *Peeking at A/B Tests*, KDD 2017](https://doi.org/10.1145/3097983.3097992)). An unconstrained generate-and-pick-the-winner agent is a machine for manufacturing false discoveries at scale — and, because it then *writes those discoveries into the compounding loop*, for poisoning the system's own learned priors.

### 61.2 The design response

The remedy Berman and Van den Bulte recommend — **two-stage designs: many variants screened, then the leading candidate validated in a second stage** — is structurally identical to the framework's existing `vote → verify → leader` pattern. That correspondence is the reason this stage fits at all.

```
ExperimentWriter (single writer) → experiment.yaml (PRE-REGISTERED, hash-pinned before exposure)
  ├── det_tools: power_calc · fdr_plan_check · preregistration_lock · instrumentation_lint
  ├── voters: Validity · Metric-Integrity · Ethics · Sample-Feasibility
  ├── verify pass
  ├── Gate PL3-exp (deterministic): pre-registration hash written, MDE reachable, arms instrumented
  ├── STAGE 1 — screening: k variants, FDR-controlled (Benjamini-Hochberg), sequential-safe monitoring
  ├── STAGE 2 — validation: top candidate vs control, fresh sample, pre-registered stopping rule
  └── Leader → decision record: adopt | reject | inconclusive(→ nothing enters the compounding loop)
```

```yaml
# experiments/EXP-2026-031.yaml — hash-pinned at Gate PL3-exp; post-hoc edits are gate failures
experiment:
  id: EXP-2026-031
  hypothesis: "Outcome-led headline raises signup-start rate among organic landing traffic"
  primary_metric: signup_start_rate        # exactly one; §61.3
  guardrail_metrics: [activation_rate, unsubscribe_rate, refund_rate]
  secondary_metrics: [scroll_depth]        # reported, never decisive, always FDR-corrected
  design:
    stage1: {arms: 6, allocation: equal, correction: benjamini_hochberg, q: 0.10}
    stage2: {arms: 2, allocation: equal, fresh_sample: true}
  power: {baseline: 0.062, mde_relative: 0.15, alpha: 0.05, power: 0.80,
          n_per_arm: 4914, expected_days: 23}
  monitoring: {method: sequential, spending: obrien_fleming, peeks: weekly}
  stopping_rule: "Stop at planned horizon or sequential boundary. No other stop is legal."
  decision_rule: "Adopt only if stage2 primary is significant AND no guardrail degrades beyond its bound."
  preregistered_at: 2026-08-03T09:12:00Z
  preregistration_hash: sha256:…
```

### 61.3 The rules that do the work

- **One primary metric.** Everything else is a guardrail or a secondary, and secondaries are never decisive. This single rule removes the largest source of agent-driven multiplicity.
- **Pre-registration is hash-pinned before exposure.** `preregistration_lock` compares the analysis-time hash to the registered one; a mismatch is a gate failure, not a warning. This is what makes p-hacking structurally impossible rather than discouraged.
- **Sequential-safe monitoring or no monitoring.** If the agent will look at results before the horizon — and it will, because that is what continuous operation means — the design must use a sequential method with a pre-specified spending function.
- **Underpowered tests are not run.** If `power_calc` shows the required n is unreachable within the window given current traffic, the honest output is `BLOCKED(INSUFFICIENT_POWER)`, and the correct next action is usually a qualitative test rather than a smaller quantitative one. A small team's traffic makes this the *common* case, and pretending otherwise is how the outer loop starts lying to itself.
- **Inconclusive results enter nothing.** A non-result does not become a "learning" in the compounding loop. It updates the priors ledger's n and nothing else. This closes the path by which false discoveries would otherwise become permanent institutional knowledge.
- **Guardrails can veto a win.** A subject line that lifts opens and raises complaint rate is a loss, and `deliverability_preflight` thresholds are guardrails on every email experiment.

### 61.4 The Ethics voter

Small roster, narrow charter, hard vetoes: dark patterns in copy or flow; manufactured urgency that is not true (a countdown that resets is a false statement); pricing or offer discrimination across protected characteristics or proxies for them; experiments on populations who cannot meaningfully consent; anything the compliance profile flags for the operator's vertical. A veto here is not a finding to weigh — it stops the experiment, on the same footing as `forbidden_autonomous`.

### 61.5 Gate PL3 — human, per artifact class

```
Gate PL3 (human):
  entry:  all channel-profile det_tools green · claim_substantiation clean
          · disclosure_lint clean · Ethics voter no-veto · experiment pre-registered if applicable
          · release.instrumentation_verified == true
  presents: the exact artifact as it will appear · the substantiation map, sentence → claim → evidence
          · the disclosure block · deliverability/spam preflight summary · the diff vs last approved
  rubric: [1] Is every capability sentence backed by a claim I can open?
          [2] Would I be comfortable if this were quoted back in a complaint?
          [3] Does this respect the community/channel I'm about to enter?
          [4] Is the cadence a ceiling I'm approaching, or a target I'm chasing?
  outcome: approve(scoped: one artifact, one channel, one window) | revise | reject
  scope:  approvals never generalize. Approving one post is not approving a campaign.
```

The scoping rule is the operational heart of the stage: batch approval is where draft-and-approve degrades into publish-and-hope. A batch may be approved as a batch only when the artifacts are homogeneous and the whole batch is presented; the human-attention budget (§16.38.2) is what forces cadence honesty — if approving the queue costs more attention than the team has, the correct response is to publish less, not to approve blind.

### 61.6 What P3 emits

`p3_to_p4.yaml`: the published artifact inventory with hashes, live experiment registrations, channel-health baselines (complaint rate, placement, account standing), and the instrumentation map. P4 (§22.62) consumes exactly this; nothing else crosses.
