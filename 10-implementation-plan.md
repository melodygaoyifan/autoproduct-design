# 10 — Implementation Plan

*Day-by-day build plan for `autoproduct`. Part C of three authoritative design documents.*

Prerequisites: `08-foundation.md` and `09-system-design.md`. This document assumes the architecture and agent/state/tool specifications are settled.

---

## Part 11 — Day-by-day plan

**Time horizon — read this carefully.** Earlier drafts of this plan compressed all 4 stages into 18 weeks at 3-5 hr/week (54-90 hours). After validation against actual voter-build hours observed in Anthropic's own internal multi-agent system work and against the realistic skill-prompt + calibration time per voter, that estimate was wrong by 2-3×. The honest plan is:

| Phase | Stage scope | Duration at 3-5 hr/week | Hours total |
|---|---|---|---|
| **v0.1.0** | Code Review + Test (6 voters + Leader) | Weeks 1-6 (unchanged) | 18-30 |
| **v0.5.0** | + Deploy Review (4 voters + policy compiler + trust-tier framework) | Weeks 7-13 | 21-35 |
| **v0.8.0** | + Maintenance (4 voters + auto-action shim + learned-skill registry + threat model) | Weeks 14-20 | 21-35 |
| **v1.0.0** | + Cross-stage integration + dashboards + production usage + release | Weeks 21-28 | 24-40 |
| **Total** | 4-stage MAS | **24-30 weeks** | **84-140 hours** |

Why the original 18 weeks was wrong:

- **Voter build time** is ~7-12 hours per voter (skill prompt design, fixture set, calibration, integration tests). 8 new voters = 56-96 hours just for voters, before any harness work.
- **Policy compiler** (§11.6 Policy-as-Prompt) is roughly 2 weeks of focused work on its own — earlier draft put it inside 1 day.
- **Threat model + secrets management** (§11.12) was a "TBD" earlier, now scoped at 1 week per Path B Gap 3.
- **Real production usage** for calibration (Weeks 13-14 in the old plan) typically takes 4 weeks for meaningful signal at AgentHire's PR cadence (~5-10 PRs/week, ~10-20 production signals/week).
- **Replay framework** (§12.10 SOTA gap) is a 2-3 day item that was completely absent from the old plan.

**The 6-week v0.1.0 milestone (Weeks 1-6) is unchanged from prior drafts.** What changes is the 12-week deploy+maintenance extension becoming an 18-22 week extension. Weeks 1-6 are detailed below as before; Weeks 7+ have been redistributed to honestly fit the work.

The plan assumes a solo developer working in short focused sessions. Skip days are fine; the criteria carry over. What matters is the sequence.

### Change-control protocol

When reality diverges from this plan (it will), apply these rules rather than quietly re-scoping:

1. **Slip within a week → defer, don't compress.** If a Week runs more than 20% over its time budget, defer the lowest-priority tasks in Week N+1 rather than cutting quality gates, skipping tests, or skipping observability work in the current week. Quality gates (DoR, Test Gate, HITL) are non-negotiable deliverables.
2. **Slip across a week → update Appendix D risk register.** Add a new entry describing what slipped, why, and what was deferred. This keeps the change visible to a future reader (or future Melody).
3. **New requirement appears mid-build → triage explicitly.** Categorize as: (a) *must have for current milestone*, (b) *next-milestone backlog*, (c) *reject*. Only (a) gets added to the current plan, and (a) additions must be paired with an explicit removal or deferral of something equivalent in effort.
4. **Architecture change (not tweak) → write a short ADR.** If a core decision from §08 or §09 is being revised mid-build, write a 1-page Architecture Decision Record in `docs/adr/NNN-title.md` capturing: what changed, why, what was considered, what the trade-offs are. This is the record that future-you relies on when the same question comes up again.

Rules 1 and 4 are the ones most often skipped in solo projects. Following them is cheap and compounds over months.

### Day 0 calibration experiment (the real time check)

The 24-30 week / 84-140 hour estimate is itself an estimate. To convert it from estimate to *empirically grounded plan*, do this BEFORE Week 1:

**Day 0 (~3-5 hours, before "real" Day 1):**

1. Pick the easiest voter (Correctness) and build ONE end-to-end through-line: skill prompt + base Voter class + one tool wrapper (`read_file`) + one fixture + a runnable invocation that prints findings to stdout.
2. Stop the clock. How long did this take?
3. Multiply: the easiest voter took N hours → the 8 new voters in Weeks 7-20 will take roughly 8 × N × 1.4 hours (1.4 difficulty multiplier — Code Review voters are easier than Deploy/Maintenance).
4. Compare against the §10 honest-time-estimate budget for those weeks.
5. If your Day 0 result implies > 30% over budget for those weeks, EITHER cut scope (which voter is least essential?) OR allocate more weeks NOW, before starting.

This isn't padding; it's calibration. The 24-30 week number was reasoned from external benchmarks; Day 0 grounds it in your actual pace on this codebase.

The Day 0 deliverables (one voter, one fixture, one tool wrapper) are not throwaway — they become the first work items for Day 1 (see "Day 1 incorporates Day 0 deliverables" note below).

### 20% week-buffer policy

Each week's plan as written assumes nominal 3-5 hour days and 5-7 working days. That's tight. Apply a 20% buffer at the week level:

- If the week's tasks are reaching the end of nominal time and items are not yet done, cut the LOWEST priority item (typically benchmark calibration, observability tweaks, README polish — never gates, voters, tests, or architecture).
- The cut item moves to next week with a tag `[carried-from-WeekN]`.
- If three consecutive weeks have carried items, the milestone date slips. Update RETRO.md AND the risk register (R-time-estimate) AND the README's milestone target with a comment noting the slip.

This buffer policy is the operational complement to Bug 8's honest time estimate. Together they replace the 18-week false-precision plan with: *24-30 weeks at nominal pace, with a structural buffer that absorbs typical slippage without pretending nothing happened*.

### Bootstrapping — reviewing autoproduct's own code before v0.1.0

The chicken-and-egg: `autoproduct` is a code-review tool, but during Weeks 1-6 (before v0.1.0 ships) there's no `autoproduct` to review the PRs that build `autoproduct` itself. The same vibe-coding pain points (safety removal, hardcoded secrets, hallucinated dependencies, missing CSRF, cross-file inconsistency) apply to `autoproduct`'s own development, with the additional irony that this is the tool meant to catch those.

**The bootstrap protocol (Weeks 1-6):**

1. **Use Claude Code's `/review` for every PR.** Claude Code ships a multi-agent code review system (`claude-code-review`); it's the closest available substitute and was a primary reference design (§09.4 voter ensemble). Run `claude /review <branch>` before merging any PR to `main`. Treat its findings with the same severity discipline as `autoproduct`'s own outputs would be treated.
2. **Run the deterministic stack manually.** Even before the harness exists, run Semgrep (`semgrep --config auto`), Bandit, TruffleHog, and pip-audit on every Python PR. These are subprocess-friendly tools — wire them into `.git/hooks/pre-push` from Day 1 so every push runs them. This catches ~40-60% of what `autoproduct`'s Security Voter would catch, with zero LLM cost.
3. **Apply slopsquatting check immediately.** §07.3.5 is the highest-leverage deterministic check for the bootstrap window. Implement it as a standalone script (~30 LOC) on Day 1; run it before every dependency add. Even before the rest of the harness exists, this single check catches the failure mode that has the highest base rate (20% of AI-generated code references nonexistent packages per CSA 2026).
4. **Treat your own PRs as adversarial.** When you write `autoproduct` code with Claude/Cursor, do not trust it without `/review` + deterministic-stack-clean. The codebase being shipped is itself the specification of "what good review looks like" — shipping `autoproduct` v0.1.0 with safety-removal patterns in its own diff would be hilariously wrong.
5. **From Day 36 onward (Week 6, v0.1.0 ships): point `autoproduct` at its own PRs.** Self-review unlocks compounding immediately — every false positive `autoproduct` emits on its own diff is a calibration signal; every miss is a regression test fixture for Day 90+. The §09.8 "meta-test" note already covers this. From Week 7 onward the bootstrap protocol is retired in favor of `autoproduct` itself.

**What this protocol does NOT do.** It does not provide cross-file consistency review (no Repo Graph Voter equivalent in Claude Code's stock review), does not provide mutation testing (Day 25), does not provide reverse-merge safety (Day 22). Those gaps are real during the bootstrap window. Mitigate by:

- Keeping autoproduct's own dependencies minimal (the file tree in Appendix C is intentionally lean — every dependency is one more bootstrap-window vulnerability surface).
- Doing manual cross-file reviews on PRs that touch `state/`, `orchestrator/`, or `policy/` (the load-bearing modules where cross-file bugs would compound).
- Using `git worktree` from Day 22 onward for adversarial mutation testing on `autoproduct`'s own code. This brings reverse-merge-safety equivalent online before v0.1.0 ships.

The bootstrap protocol is not a permanent process — it exists for ~6 weeks, then `autoproduct` self-reviews and the protocol is documented in `docs/bootstrap-retrospective.md` for future maintainers (or future versions of `autoproduct` that need to bootstrap a similar tool).

### Week 1 — Skeleton

**Goal by end of week:** `autoproduct review <PR-URL>` invokes Correctness voter on a real PR, prints structured findings to stdout.

**Day 1 incorporates Day 0 deliverables.** If you completed Day 0 calibration, the Correctness voter, base class, `read_file` tool, and first fixture are already done. Day 1 then becomes: integrate them into the project skeleton (next section).

#### Day 1 — Repository and scaffolding

Tasks:
- Create `autoproduct` GitHub repo, set license MIT, add `.gitignore` for Python
- Initialize with Poetry or PDM
- Add `pyproject.toml` with initial dependencies (see §Appendix B)
- Create the skeleton directory structure (see §Appendix C)
- Create `tests/` with `conftest.py`, `tests/unit/`, `tests/integration/`, `tests/fixtures/`. This matters from Day 1: every subsequent day's tasks include unit tests, and having the scaffolding up front prevents "I'll add tests later" drift.

```toml
# pyproject.toml (starting state)
[project]
name = "autoproduct"
version = "0.1.0-dev"
requires-python = ">=3.11"
dependencies = [
    "langgraph>=1.0",
    "langgraph-checkpoint-sqlite>=2.0",
    "anthropic>=0.40",
    "pydantic>=2.8",
    "pyyaml>=6.0",
    "typer>=0.12",
    "httpx>=0.27",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-httpx>=0.35",
    "pytest-cov>=5.0",
    "ruff>=0.6",
    "pyright>=1.1.380",
]

[project.scripts]
autoproduct = "autoproduct.cli:app"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

Success criterion: `python -m autoproduct --help` prints usage without error. `pytest tests/` returns 0 tests collected (scaffolding in place but no tests yet — that's correct for Day 1).

#### Day 2 — State schema

Tasks:
- Write `autoproduct/state/review_state.py` with the full `ReviewState` TypedDict
- Write `autoproduct/state/finding.py` with `VoterFinding` dataclass
- Write Pydantic validator mirror in `autoproduct/state/validators.py`
- Unit tests for state construction and validation

```python
# autoproduct/state/review_state.py — stub for Day 2
# (Full schema in §09.5.1)
from typing import TypedDict, Literal, NotRequired

class ReviewState(TypedDict):
    review_id: str
    pr_url: str
    pr_number: int
    diff: str
    changed_files: list[str]
    mode: Literal["fast", "standard", "deep"]
    voter_findings: dict[str, list]
    # ... (rest per §09.5.1)
```

Success criterion: `pytest tests/test_state.py` passes; Pydantic validator rejects malformed state.

#### Day 3 — Orchestrator skeleton

Tasks:
- Write `autoproduct/orchestrator/graph.py` with minimal StateGraph (INIT, VOTE, POST nodes only)
- Write `autoproduct/orchestrator/nodes/init.py` — fetches PR from GitHub API, populates state
- Use `SqliteSaver` as checkpointer for local dev (swap for Postgres in webhook mode later)
- CLI stub: `autoproduct review <URL>` that compiles the graph and calls `.ainvoke`

```python
# autoproduct/orchestrator/graph.py — Day 3
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from autoproduct.state import ReviewState
from autoproduct.orchestrator.nodes.init import init_node
from autoproduct.orchestrator.nodes.vote import vote_node_stub
from autoproduct.orchestrator.nodes.post import post_node_stub


def build_graph(checkpointer: SqliteSaver):
    g = StateGraph(ReviewState)
    g.add_node("init", init_node)
    g.add_node("vote", vote_node_stub)
    g.add_node("post", post_node_stub)
    g.add_edge(START, "init")
    g.add_edge("init", "vote")
    g.add_edge("vote", "post")
    g.add_edge("post", END)
    return g.compile(checkpointer=checkpointer)
```

Success criterion: `autoproduct review https://github.com/melodygao/agenthire/pull/1` fetches diff, prints "[stub] would review X changed files" and exits cleanly.

#### Day 4 — LLM client adapter

Tasks:
- Write `autoproduct/llm/client.py` with a provider-agnostic interface
- Implement the Anthropic adapter first
- Handle streaming, tool use, timeout, retry with exponential backoff

```python
# autoproduct/llm/client.py — Day 4
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

@dataclass
class LLMResponse:
    text: str
    tool_use: Any | None
    raw: dict
    model: str
    tokens_in: int
    tokens_out: int


class LLMClient(ABC):
    @abstractmethod
    async def complete(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.2,
        timeout: int = 120,
        max_tokens: int = 4096,
    ) -> LLMResponse: ...


class AnthropicClient(LLMClient):
    def __init__(self, api_key: str):
        from anthropic import AsyncAnthropic
        self._client = AsyncAnthropic(api_key=api_key)

    async def complete(self, model, messages, tools=None, temperature=0.2,
                       timeout=120, max_tokens=4096) -> LLMResponse:
        for attempt in range(3):
            try:
                response = await self._client.messages.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                )
                return _adapt_anthropic_response(response)
            except Exception as e:
                if attempt == 2:
                    raise
                await asyncio.sleep(2 ** attempt)
```

Success criterion: a test script invokes the client against Claude Opus, gets a text response, tokens are counted.

#### Day 4.5 — Harness skeleton with SpecValidator (per `11-ultimate-architecture.md` Part 18)

Tasks (~2-3 hours):

- Create `autoproduct/harness/` directory with `__init__.py`, `spec_validator.py`, `schemas/`
- Write `autoproduct/harness/schemas/voter_spec.schema.json` — JSON Schema for voter frontmatter (per §16.2 in `11-ultimate-architecture.md`)
- Implement `autoproduct/harness/spec_validator.py` — `SpecValidator(project_root)` class with `validate_all()` method that scans `skills/*.md`, parses frontmatter via `python-frontmatter`, validates against schema, raises `VoterSpecValidationError` on any failure
- Stub `autoproduct/harness/__init__.py` — `Harness` class skeleton (will gain MCPHost on Day 7.5, FixtureGate on Day 13, ContractChecker on Day 13)
- Write the first voter spec frontmatter for Correctness skill (will be added to `skills/correctness.md` on Day 5)

```python
# autoproduct/harness/spec_validator.py
import frontmatter
import jsonschema
from pathlib import Path


class VoterSpecValidationError(Exception):
    pass


class SpecValidator:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        schema_path = Path(__file__).parent / "schemas" / "voter_spec.schema.json"
        self.schema = json.loads(schema_path.read_text())

    def validate_all(self) -> dict[str, dict]:
        """Returns {voter_name: spec_dict} for all valid skills.

        Raises VoterSpecValidationError on any malformed spec.
        """
        specs = {}
        skills_dir = self.project_root / "skills"
        for skill_path in skills_dir.glob("*.md"):
            post = frontmatter.load(skill_path)
            spec = post.metadata
            try:
                jsonschema.validate(spec, self.schema)
            except jsonschema.ValidationError as e:
                raise VoterSpecValidationError(
                    f"{skill_path.name}: {e.message}"
                ) from e
            specs[spec["voter_name"]] = spec
        return specs
```

Add `python-frontmatter>=1.1` and `jsonschema>=4.21` to Appendix B core deps. Update Day 5's task to add frontmatter to `skills/correctness.md`.

Success criterion: `python -c "from autoproduct.harness.spec_validator import SpecValidator; SpecValidator(Path('.')).validate_all()"` runs cleanly when no skills exist yet (empty dict returned), and raises clearly on a deliberately-malformed test skill (e.g., missing `voter_name`).

#### Day 5 — Correctness voter + skill

Tasks:
- Write `autoproduct/agents/voter.py` with the uniform `Voter` base class from §09.4.2
- Write `skills/correctness.md` with the full content from §09.4.4.1
- Wire `vote_node` (still stubbed) to actually invoke the Correctness voter
- Basic YAML parsing of findings

```python
# autoproduct/orchestrator/nodes/vote.py — Day 5 version (single voter)
from autoproduct.agents.voter import Voter, VoterConfig
from autoproduct.state import ReviewState


async def vote_node(state: ReviewState) -> dict:
    # Day 5: just Correctness voter
    config = VoterConfig(
        name="correctness",
        model="claude-opus-4.7",
        skill_path=Path("skills/correctness.md"),
    )
    voter = Voter(config, llm=..., tools=...)
    findings = await voter.run(state)
    return {
        "voter_findings": {"correctness": [f.__dict__ for f in findings]},
        "voter_durations": {"correctness": ...},
    }
```

Success criterion: `autoproduct review <real-PR>` runs end to end, prints real Correctness voter findings in structured form.

#### Day 6 — CLI polish + calibration on known bugs

Tasks:
- Flesh out CLI with `--mode`, `--verbose`, `--json` flags
- Basic logging setup
- Test on 3 different real PRs from AgentHire history
- Write unit tests for voter base class and state transitions
- **Calibration on known-buggy commits.** Before pointing at AgentHire for daily use, run the Correctness voter on a small set of known-buggy commits to establish a recall floor. Two options:
  - **Option A (preferred for Python):** pick 10-15 [Defects4J](https://github.com/rjust/defects4j)-style commits from open-source Python projects (e.g., requests, flask, pandas) where the bug-fix commit message identifies the bug clearly. The pre-fix commit is the "buggy" version; run autoproduct on the diff that introduced the bug (or on a synthesized PR that reverts the fix).
  - **Option B (faster):** pick 5-10 fixed bugs from AgentHire's own git history (PRs that fixed real bugs). Replay each as if the bug were being introduced — autoproduct should flag each one.
- Record the recall (bugs caught / bugs total) and a per-bug notes file: which voter caught it, what the finding said, where it failed.
- If recall < 60% on this small set, the system is not ready for AgentHire daily use — tune the Correctness skill's "primary targets" and "what NOT to flag" sections, then re-run.

Success criterion (end of Week 1): (1) Can invoke CLI on any real PR and get Correctness findings in under 2 minutes. (2) Recall ≥ 60% on the 10-15 known-buggy commit calibration set. The recall number is committed to `benchmarks/calibration-week1.md` for later comparison.

---

### Week 2 — Core voters + Leader + heterogeneous providers

**Goal by end of week:** All 6 voters run in parallel on a real PR; Leader synthesizes; verdict is emitted.

#### Day 7 — OpenAI and Google providers

Tasks:
- Implement `OpenAIClient` in `autoproduct/llm/openai_client.py`
- Implement `GoogleClient` for Gemini
- Adapter interface handles differences (OpenAI tool format ≠ Anthropic tool format)
- Environment variable configuration: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `XAI_API_KEY`

```python
# autoproduct/llm/factory.py
from autoproduct.llm.client import LLMClient
from autoproduct.llm.anthropic_client import AnthropicClient
from autoproduct.llm.openai_client import OpenAIClient
from autoproduct.llm.google_client import GoogleClient
from autoproduct.llm.xai_client import XAIClient


def get_client_for_model(model: str) -> LLMClient:
    if model.startswith("claude-"):
        return AnthropicClient(os.environ["ANTHROPIC_API_KEY"])
    if model.startswith("gpt-") or model.startswith("o3"):
        return OpenAIClient(os.environ["OPENAI_API_KEY"])
    if model.startswith("gemini-"):
        return GoogleClient(os.environ["GOOGLE_API_KEY"])
    if model.startswith("grok-"):
        return XAIClient(os.environ["XAI_API_KEY"])
    raise ValueError(f"Unknown model: {model}")
```

Success criterion: a test script invokes GPT-5.4 and Gemini 3.1 Pro successfully.

#### Day 7.5 — MCP host + first internal MCP server (per `11-ultimate-architecture.md` Part 17)

Tasks (~3-4 hours; this is a half-day insertion to keep Days 7 → 8 contiguous):

- Install MCP Python SDK: `pip install "mcp>=1.25,<2"` (Anthropic-published, MIT-licensed). Pin to v1.x line — v2 is in planning per SDK maintainers and introduces breaking transport-layer changes; migration to v2 is deliberately deferred to autoproduct v1.2.
- Implement `autoproduct/mcp_servers/read_only_server.py` exposing 4 tools: `read_file`, `grep`, `git_log`, `git_blame`. Use `mcp.server.Server` + `mcp.server.stdio.stdio_server`
- Implement `autoproduct/harness/mcp_host.py` per §17.4 — `MCPHost` class with `start_for_stage()` and `shutdown()`; spawn server as stdio subprocess; per-server scoped `env`, `cwd`, `rlimit`
- Implement `autoproduct/harness/mcp_client.py` — thin wrapper over `mcp.client.session.ClientSession` for connection lifecycle
- Per-stage server config: `REQUIRED_SERVERS_PER_STAGE = {"code_review": ["read_only_server"]}` (will grow as more servers are added in Days 13/26)
- Wire `dor_gate_node` (Gate 1) to also spawn MCP servers via `MCPHost.start_for_stage("code_review")` before voters run
- Wire `post_node` to call `MCPHost.shutdown()` after voters complete

Success criterion: Correctness voter from Day 5 calls `read_only_server.read_file(...)` via MCP protocol on a real AgentHire PR. The audit log at `.mas/reviews/{review_id}/mcp-audit.yaml` shows the JSON-RPC tools/call message with method, tool, args summary, duration, outcome.

```python
# autoproduct/mcp_servers/read_only_server.py — minimal first server
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import asyncio

server = Server("read_only_server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="read_file",
            description="Read a file from the repo. Returns text content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "lines": {"type": "string", "description": "Optional 'start-end' range"},
                },
                "required": ["path"],
            },
        ),
        # ... grep, git_log, git_blame tools follow same pattern
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "read_file":
        return [TextContent(type="text", text=_read_file_impl(arguments["path"]))]
    # ... other tools dispatch
    raise ValueError(f"Unknown tool: {name}")


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
```

This replaces Round 5's same-process Python tool registry. After Day 7.5, voters call tools via MCP protocol exclusively — even though it's still single-machine, we get subprocess isolation, dynamic `tools/list` discovery, and the architecture for v1.1.0 expose-as-server.

If Day 7.5 runs over 4 hours, it's a calibration signal — note in RETRO and accept that MCP-related days (7.5, 13, 26) may all come in over budget; adjust plan to 28-30 weeks accordingly per §10's slip protocol.

#### Day 8 — Security and Performance voters

Tasks:
- Write `skills/security.md` (full content from §09.4.4.2)
- Write `skills/performance.md` (full content from §09.4.4.3)
- Register these in `vote_node`
- Update parallelization: use `asyncio.gather` to run voters concurrently

```python
# autoproduct/orchestrator/nodes/vote.py — Day 8
async def vote_node(state: ReviewState) -> dict:
    configs = [
        VoterConfig(name="correctness", model="claude-opus-4.7",
                    skill_path=Path("skills/correctness.md")),
        VoterConfig(name="security", model="gpt-5.4",
                    skill_path=Path("skills/security.md")),
        VoterConfig(name="performance", model="gemini-3.1-pro-preview",
                    skill_path=Path("skills/performance.md")),
    ]
    voters = [Voter(c, llm=get_client_for_model(c.model), tools=tools) for c in configs]

    results = await asyncio.gather(
        *[v.run(state) for v in voters],
        return_exceptions=True,
    )

    findings, failures = {}, {}
    for config, result in zip(configs, results):
        if isinstance(result, Exception):
            failures[config.name] = str(result)
        else:
            findings[config.name] = [f.__dict__ for f in result]

    return {"voter_findings": findings, "voter_failures": failures}
```

Success criterion: 3 voters run concurrently in <120 seconds total on a typical PR.

#### Day 9 — Context and Style voters

Tasks:
- Write `skills/context.md` (full content from §09.4.4.4)
- Write `skills/style.md` (full content from §09.4.4.6)
- Register in `vote_node`
- Now 5 voters running; Repo Graph deferred to Week 3

Success criterion: 5 voters run concurrently on a real PR; each produces structured YAML findings.

#### Day 10 — Leader synthesis

Tasks:
- Write `skills/leader.md` (full content from §09.4.4.7)
- Add `leader_node` to the graph
- Edge: `vote → leader → post`
- Leader parses voter findings, produces verdict + taxonomy signals

```python
# autoproduct/orchestrator/nodes/leader.py
async def leader_node(state: ReviewState) -> dict:
    skill = Path("skills/leader.md").read_text()
    prompt = f"""{skill}

---
# Review Context

## PR
{state['pr_description']}

## Voter findings (aggregated)
{yaml.safe_dump(state['voter_findings'])}

## Deterministic tool output summary
{_summarize_tools(state)}

---
Produce final verdict and taxonomy signals per schema.
"""
    llm = get_client_for_model("claude-opus-4.7")
    response = await llm.complete(
        model="claude-opus-4.7",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        timeout=180,
    )
    parsed = _parse_leader_output(response.text)
    return {
        "verdict": parsed["verdict"],
        "final_findings": parsed["findings"],
        "taxonomy_signals": parsed["signals"],
    }
```

Success criterion: On a real PR, Leader produces a verdict, a deduped list of findings, and STAR-L signals.

#### Day 11 — PR comment formatting + POST node

Tasks:
- Implement `post_node`: formats verdict + findings into markdown, posts to PR via GitHub API
- Comment format includes severity icons, clickable file:line links
- Write YAML mirror at POST stage

```python
# autoproduct/orchestrator/nodes/post.py
async def post_node(state: ReviewState) -> dict:
    comment = _format_pr_comment(state)
    await post_github_comment(state["pr_url"], comment)

    yaml_mirror = YAMLMirror(repo_root, state["review_id"])
    final_path = yaml_mirror.finalize(state)

    return {
        "pr_comment_posted": True,
        "yaml_mirror_paths": [str(final_path)],
    }


def _format_pr_comment(state: ReviewState) -> str:
    verdict = state["verdict"]
    icon = {"APPROVE": "✅", "REQUEST_CHANGES": "⚠️", "ESCALATE": "🚨"}[verdict]

    lines = [f"## {icon} autoproduct review: {verdict}"]
    lines.append("")

    critical = [f for f in state["final_findings"] if f["severity"] == "critical"]
    high = [f for f in state["final_findings"] if f["severity"] == "high"]

    if critical:
        lines.append("### Critical")
        for f in critical:
            lines.append(f"- **{f['file_path']}:{f['line_start']}** — {f['claim']}")
            lines.append(f"  > {f['evidence'].splitlines()[0]}")

    if high:
        lines.append("### High")
        for f in high:
            lines.append(f"- **{f['file_path']}:{f['line_start']}** — {f['claim']}")

    # ... medium, low, info as collapsible sections

    return "\n".join(lines)
```

Success criterion: Real PR gets a real comment with structured findings; YAML mirror contains complete review record.

#### Day 12 — Weekend polish

Tasks:
- Run full pipeline on 5 different AgentHire PRs
- Fix issues (prompt tweaks, schema mismatches)
- Ensure voter failure handling (one failing doesn't block others)

Success criterion (end of Week 2): A single command, `autoproduct review <URL>`, runs all 5 voters + Leader + POST in <4 minutes; comment appears on PR.

---

### Week 3 — Repo Graph Voter + tool-based context

**Goal by end of week:** RepoGraphVoter correctly identifies at least one cross-file breaking change in a constructed test PR. Tool-based investigation replaces pre-computed context blobs where beneficial.

#### Day 13 — tree-sitter setup

Tasks:
- Add `tree-sitter`, `tree-sitter-python` dependencies
- Build indexer: walks repo, extracts symbols (functions, classes, imports), stores in SQLite index
- Write `autoproduct/tools/tree_sitter_index.py`

```python
# autoproduct/tools/tree_sitter_index.py
import sqlite3
from tree_sitter_language_pack import get_language, get_parser
from pathlib import Path


class SymbolIndex:
    def __init__(self, index_path: Path):
        self.conn = sqlite3.connect(index_path)
        self._init_schema()

    def _init_schema(self):
        # NOTE: table name is `symbol_references` not `references` —
        # `references` is a reserved word in standard SQL.
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY,
                name TEXT,
                kind TEXT,  -- 'function', 'class', 'constant', 'import'
                file_path TEXT,
                line_start INTEGER,
                line_end INTEGER,
                scope TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_name ON symbols(name);
            CREATE INDEX IF NOT EXISTS idx_file ON symbols(file_path);

            CREATE TABLE IF NOT EXISTS symbol_references (
                id INTEGER PRIMARY KEY,
                symbol_name TEXT,
                file_path TEXT,
                line INTEGER,
                kind TEXT  -- 'call', 'import', 'attribute_access'
            );
            CREATE INDEX IF NOT EXISTS idx_refs_name ON symbol_references(symbol_name);

            CREATE TABLE IF NOT EXISTS file_hashes (
                file_path TEXT PRIMARY KEY,
                sha256 TEXT
            );
        """)
        self.conn.commit()

    def index_file(self, path: Path, force: bool = False) -> None:
        # Compute hash, skip if unchanged
        current_hash = _sha256(path)
        existing = self.conn.execute(
            "SELECT sha256 FROM file_hashes WHERE file_path = ?", (str(path),)
        ).fetchone()
        if existing and existing[0] == current_hash and not force:
            return

        # Parse with tree-sitter, extract symbols, upsert into DB
        parser = get_parser("python")  # language pack provides pre-bound parser
        source = path.read_bytes()
        tree = parser.parse(source)

        # Clear existing entries for this file
        self.conn.execute("DELETE FROM symbols WHERE file_path = ?", (str(path),))
        self.conn.execute("DELETE FROM symbol_references WHERE file_path = ?", (str(path),))

        # Extract
        for sym in _extract_symbols(tree.root_node, path):
            self.conn.execute(
                "INSERT INTO symbols (name, kind, file_path, line_start, line_end, scope) VALUES (?, ?, ?, ?, ?, ?)",
                sym,
            )
        for ref in _extract_references(tree.root_node, path):
            self.conn.execute(
                "INSERT INTO symbol_references (symbol_name, file_path, line, kind) VALUES (?, ?, ?, ?)",
                ref,
            )

        self.conn.execute(
            "INSERT OR REPLACE INTO file_hashes (file_path, sha256) VALUES (?, ?)",
            (str(path), current_hash),
        )
        self.conn.commit()

    def find_references(self, symbol_name: str) -> list[dict]:
        rows = self.conn.execute(
            "SELECT file_path, line, kind FROM symbol_references WHERE symbol_name = ?",
            (symbol_name,),
        ).fetchall()
        return [{"file": r[0], "line": r[1], "kind": r[2]} for r in rows]
```

Success criterion: Indexer runs on AgentHire repo in <30 seconds, index file fits in <50 MB.

#### Day 13.5 — ContractChecker + FixtureGate + ModuleSpecLoader (per `11-ultimate-architecture.md` Part 18)

Tasks (~3-4 hours; harness completion):

- Implement `autoproduct/harness/contract_checker.py` per §18.3 — `ContractChecker(voter_specs, module_specs)` with `check_input()`, `check_output()`, `check_module_spec_alignment()` methods
- Implement `autoproduct/harness/fixture_gate.py` per §18.2 — `FixtureGate(project_root, voter_specs)` with `enforce()` method that runs each voter's fixtures, raises `FixtureGateRejection` if pass rate < 87.5%
- Implement `autoproduct/harness/spec_loader.py` for module specs — scans `.mas/specs/**/*.spec.yaml`, validates against schema, returns dict keyed by module path
- Wire `Voter.run()` to call `contract_checker.check_input(state)` before LLM call and `contract_checker.check_output(output)` after
- Wire `analyze_node` (Code Review) to populate `state["affected_module_specs"]` based on changed files vs. spec coverage
- Add `mas/specs/{module}.spec.yaml` schema at `harness/schemas/module_spec.schema.json`

Success criterion: harness startup runs all 7 steps from §18.1; a deliberately-broken voter (returns string instead of envelope) is caught by ContractChecker and aborts run; a voter with stale fixtures (deliberately set pass rate to 60%) refuses to register and raises `FixtureGateRejection`. Day 0's authored module specs are read by the loader and surface in `state["affected_module_specs"]` when CorrectnessVoter runs against a PR touching those modules.

This completes the harness machinery. After Day 13.5, the system has full spec-driven contract enforcement at runtime.

#### Day 14 — pyright wrapper

Tasks:
- Install pyright (`npm install -g pyright` or equivalent)
- Write `autoproduct/tools/pyright_wrapper.py` that invokes pyright, parses JSON output, extracts type errors
- Make it work incrementally (only analyze changed files + one-hop dependents)

```python
# autoproduct/tools/pyright_wrapper.py
import json
import asyncio
from pathlib import Path


async def run_pyright(files: list[str], repo_root: Path) -> dict:
    proc = await asyncio.create_subprocess_exec(
        "pyright", "--outputjson", *files,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=repo_root,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode not in (0, 1):  # 1 = errors found, still valid
        return {"error": stderr.decode(), "diagnostics": []}
    try:
        return json.loads(stdout.decode())
    except json.JSONDecodeError:
        return {"error": "invalid pyright output", "diagnostics": []}


async def lsp_references(symbol: str, file: str, line: int, repo_root: Path) -> list[dict]:
    """Get cross-file references for a symbol."""
    # pyright doesn't have a direct "find references" CLI; we use its
    # --outputjson with the full project and filter
    result = await run_pyright([file], repo_root)
    # ... extract references involving `symbol` at `file:line`
    return []
```

Success criterion: Running pyright on a known-buggy test file produces the expected type-error output as structured JSON.

#### Day 15 — Tool registry + voter tool access + git worktree helper

Tasks:
- Write `autoproduct/tools/registry.py` with the full spec from §09.7.1
- Register all core tools (`read_file`, `grep`, `tree_sitter_query`, `lsp_references`, `git_log`, `git_blame`, `run_tests`)
- Modify `Voter.run()` to pass tool schemas into LLM calls
- Tool-call budget enforcement per voter
- Write `autoproduct/tools/git_worktree.py` with `create_worktree`, `reverse_merge_main`, `remove_worktree` per §09.7.2.8 (not voter-callable; internal helpers for adversarial_test_node / test_gate_node / reverse_merge_node)
- Sanity test: create a worktree in a throwaway repo, verify it's separate from the main checkout, remove it

Success criterion: A voter can invoke `read_file("backend/parsers/workday.py", start_line=40, end_line=60)` mid-reasoning, receive output, and use it. Independently, `create_worktree` produces an isolated working directory on a new branch and `remove_worktree` cleans it up.

#### Day 16 — Repo Graph Voter

Tasks:
- Write `skills/repo_graph.md` (full content from §09.4.4.5)
- Register RepoGraphVoter in the pipeline
- It has access to tree_sitter_query and lsp_references tools
- Test: construct a test PR that changes a function signature without updating callers; verify RepoGraphVoter flags it

```python
# tests/integration/test_repo_graph_voter.py
async def test_catches_signature_change_breaking_callers(tmp_repo):
    # Construct a test repo with:
    #   - def parse_date(s: str) -> datetime in utils/dates.py
    #   - 3 callers in other files
    # Apply a diff that adds a required param: parse_date(s: str, tz: str) -> datetime
    # Run RepoGraphVoter against the diff

    voter = Voter(
        VoterConfig(name="repo_graph", model="grok-4",
                    skill_path=Path("skills/repo_graph.md")),
        llm=..., tools=...
    )
    state = _build_test_state(tmp_repo, diff=...)
    findings = await voter.run(state)

    assert any("parse_date" in f.claim for f in findings)
    assert any(f.severity in ("high", "critical") for f in findings)
```

Success criterion: Test passes. RepoGraphVoter identifies the signature-change breakage.

#### Day 17 — Integration with all voters

Tasks:
- All 6 voters running in parallel
- Voters have appropriate tool access (Style voter gets fewer tools; Repo Graph gets the LSP tools)
- End-to-end test on multiple real PRs
- Fix prompt issues, refine skill files

Success criterion: 6-voter pipeline runs on a real AgentHire PR in <5 minutes with complete findings.

#### Day 18 — Weekend polish + docs

Tasks:
- Update `09-system-design.md` if any field contracts evolved during implementation
- Run 5 different real PRs end-to-end; document gotchas in an `implementation-notes.md` (private)

Success criterion (end of Week 3): RepoGraphVoter catches at least one real cross-file issue on an AgentHire PR that other voters missed.

#### Day 18b — Verification stage + confidence scoring + hooks framework

Tasks:
- Implement `verify_node` per §09.5.4.7. One Sonnet 4.6 call per candidate finding, in parallel via `asyncio.gather`, capped by the Anthropic-provider semaphore (§09.4.2.1). Three verdicts: `VERIFIED / NOT_REPRODUCIBLE / NEEDS_RUNTIME`. NOT_REPRODUCIBLE findings dropped, logged to per-voter false-positive signal.
- Implement confidence scoring per §09.4.7: 0-100 score from voter self-confidence (40) + verification (40) + cross-voter agreement (20). Apply `thresholds.confidence_min` (default 80) at Leader output.
- Build hooks framework `autoproduct/hooks/{event}/{name}.py` per §09.7.6. Implement the four built-in hooks:
  - `pre_tool_use/block_secret_paths.py` — refuse tool calls targeting `workspace.blocked_paths`
  - `pre_tool_use/enforce_worktree_naming.py` — branch name regex check
  - `post_voter_run/enforce_voter_envelope.py` — `VoterOutput` schema validation
  - (Gate 4 Rollback already exists from Day 21 as a GitHub Actions workflow)
- Test verification: deliberately seed a voter to emit a fabricated finding (e.g., reference a line number outside the diff). Confirm `verify_node` returns NOT_REPRODUCIBLE and the finding is dropped.
- Test confidence scoring: emit a `severity: critical, confidence: possible` finding from a single voter; confirm score is below 80 and it's filtered from the PR comment but appears in the evidence ledger.
- Test hooks: attempt a `read_file` on `secrets/api-keys.txt`; confirm `block_secret_paths` denies and the voter receives an error rather than the file contents.

Success criterion: (1) On a known-fabricated finding, `verify_node` correctly drops it. (2) Sub-threshold findings appear in evidence ledger but not in PR comment. (3) Hook denial of secret-path read is recorded in tool-audit log. (4) Adding all three above adds <90s to typical-PR wall time.

---

### Week 4 — HITL + mutation testing + YAML mirror + compound loop Stage 1

**Goal by end of week:** HITL loop tested end-to-end; mutation testing runs on every PR; compound loop produces first weekly PR.

#### Day 19 — YAML mirror infrastructure

Tasks:
- Write `autoproduct/observability/yaml_mirror.py` with full implementation from §09.6.3
- Integrate mirror writes into all nodes (write after each node completes)
- `.mas/reviews/{review_id}/` layout populated correctly

Success criterion: After a review, `.mas/reviews/{review_id}/` contains: `state.yaml`, `state.history.yaml`, `inputs/`, `tools/`, `voters/`, `leader_output.yaml`, `final.yaml`.

#### Day 20 — HITL interrupt setup

Tasks:
- Add `hitl` node to graph with `interrupt_before=["hitl"]` in compile
- Write `hitl_interrupt_node` that opens a GitHub Issue on a dedicated HITL repo
- Issue body format per §09.8.3
- Webhook endpoint (or `autoproduct resume <review_id>` CLI) to feed resume payload

```python
# autoproduct/orchestrator/nodes/hitl.py
async def hitl_interrupt_node(state: ReviewState) -> dict:
    issue_body = _build_issue_body(state)
    issue_number = await create_github_issue(
        repo=os.environ["AUTOPRODUCT_HITL_REPO"],
        title=f"autoproduct review {state['review_id']} paused",
        body=issue_body,
        labels=["mas-hitl"],
    )
    await post_github_comment(
        state["pr_url"],
        f"autoproduct review paused pending human input. See Issue #{issue_number}",
    )
    return {
        "hitl_issue_number": issue_number,
        "hitl_pause_reason": state.get("hitl_pause_reason", "unknown"),
    }


# In CLI: resume command
@app.command()
def resume(review_id: str, action: str, voter: str | None = None):
    """Resume a paused review with a directive."""
    from langgraph.types import Command

    config = {"configurable": {"thread_id": review_id}}
    resume_value = {"action": action, "voter": voter}

    graph = build_graph(checkpointer)
    final_state = asyncio.run(
        graph.ainvoke(Command(resume=resume_value), config=config)
    )
    print(f"Resumed. Final verdict: {final_state['verdict']}")
```

Success criterion: Injecting a failure (force a voter to raise) causes `hitl` node to be invoked; Issue opens on HITL repo; `autoproduct resume` resumes and completes the review.

#### Day 21 — Routing logic + four gates (DoR, Test, Review, Rollback) + verdict taxonomy

Tasks:
- Implement `VoterOutput` envelope schema per §09.4.3 with `OK / BLOCKED_MISSING_CONTEXT / BLOCKED_REQUIREMENT_CONFLICT / BLOCKED_TOOL_FAILURE` statuses; update voter base class to require status field in YAML output
- Implement `route_after_vote` with 3x-failure detection (full spec §09.5.3) + BLOCKED voter counting (3+ BLOCKED → escalate; 2 BLOCKED + Leader sees → REQUEST_CHANGES; 1 BLOCKED → continue)
- Implement Leader synthesis per §09.4.4.7 verdict taxonomy: 8 verdicts (`APPROVE`, `APPROVE_WITH_NOTES`, `REQUEST_CHANGES`, plus 5 `ESCALATE_*`)
- Implement `route_after_leader` with `verdict.startswith("ESCALATE")` detection, routing to `test_gate` for non-escalate
- Implement safety-removal detection in Security Voter that produces `severity: critical, confidence: certain` finding which Leader maps to `ESCALATE_SECURITY_RISK`
- Implement `dor_gate_node` per §09.5.4.1 with configurable checks from `.mas/project.yaml` `project.dor`
- Implement `test_gate_node` per §09.5.4.10 with thresholds from `.mas/project.yaml` `thresholds.*`; on failure produces verdict `REQUEST_CHANGES`
- Implement `route_after_dor` and `route_after_test_gate` conditionals
- Stub `reverse_merge_node` (full implementation on Day 22)
- Gate 4 (Rollback) infrastructure: add a GitHub Actions workflow `.github/workflows/autoproduct-rollback-check.yml` that runs `make bench-fast` on any `main` commit tagged with label `autoproduct:compound-loop` and opens a revert PR if recall drops by more than `rollback.recall_tolerance_pp` (default 3pp)
- Implement HITL Issue body templates per §09.8.3 (one Jinja template per ESCALATE_* verdict)
- End-to-end test each of the HITL trigger types AND each gate AND each verdict outcome

Success criterion: (1) A PR with no description is rejected at Gate 1 with a "not ready" comment and never invokes voters. (2) A PR whose coverage drops below threshold causes Gate 2 to set verdict to REQUEST_CHANGES. (3) Each HITL trigger type fires Gate 3 correctly with verdict-specific Issue body. (4) A simulated compound-loop merge that drops benchmark recall triggers a rollback PR via Gate 4. (5) Inducing a voter to return BLOCKED_MISSING_CONTEXT causes the right downstream behavior (1 BLOCKED → noted in PR comment, 2 BLOCKED → REQUEST_CHANGES, 3+ BLOCKED → ESCALATE_MISSING_CONTEXT).

#### Day 22 — Mutation testing integration with worktree + reverse-merge

Tasks:
- Install mutmut, verify it runs on AgentHire in a Docker sandbox
- Write `autoproduct/tools/mutmut_runner.py` wrapper
- Write `adversarial_test_node` per §09.5.4.9 — key change: the node creates a git worktree via `create_worktree(...)` and runs mutmut inside the worktree, not the main checkout
- Implement `reverse_merge_node` per §09.5.4.11 using `reverse_merge_main(...)` from Day 15's git_worktree module
- Wire `route_after_reverse_merge` to escalate to HITL on conflict / post-merge test failure
- Route high-risk-file changes through adversarial_test → test_gate → reverse_merge → post after leader

```python
# autoproduct/tools/mutmut_runner.py
async def run_mutmut(target_files: list[str], test_path: str, repo_root: Path) -> dict:
    """Run mutmut, return surviving mutants as structured data.

    Assumes mutmut is configured via setup.cfg or pyproject.toml [tool.mutmut]
    with runner=python -m pytest. This is the documented recommended pattern.
    For ad-hoc invocation, pass --paths-to-mutate directly.
    """
    proc = await asyncio.create_subprocess_exec(
        "mutmut", "run",
        "--paths-to-mutate", ",".join(target_files),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=repo_root,
    )
    try:
        await asyncio.wait_for(proc.communicate(), timeout=600)
    except asyncio.TimeoutError:
        proc.kill()
        return {"error": "timeout", "surviving": []}

    # Use `mutmut results` to get structured surviving-mutant output;
    # avoid parsing the binary .mutmut-cache directly.
    results_proc = await asyncio.create_subprocess_exec(
        "mutmut", "results",
        stdout=asyncio.subprocess.PIPE,
        cwd=repo_root,
    )
    results_stdout, _ = await results_proc.communicate()
    surviving = _parse_mutmut_results(results_stdout.decode())
    return {"surviving": surviving, "total": len(surviving)}
```

Success criterion: Running adversarial_test on a test PR produces a list of surviving mutants; LLM Test Generator produces at least one new test; re-running mutmut shows the new test killed at least one mutant.

#### Day 22.5 — Build `test_exec_server` container image (per `11-ultimate-architecture.md` §17.4 T3 sandbox)

Tasks (~3 hours; mandatory before `test_exec_server` can spawn):

- Write `containers/test-exec/Dockerfile` — minimal Python 3.11 base + pinned tool versions (`pytest>=8`, `mutmut>=3.2`, `playwright>=1.45`, `coverage>=7`); install Playwright browsers (`playwright install --with-deps chromium`); set non-root user `autoproduct:autoproduct` (uid 10001); entrypoint is the FastMCP application
- Write `containers/test-exec/server.py` — the `test_exec_server` MCP server's main; running inside the container, exposes `run_tests`, `run_playwright_tests`, `mutmut_run` tools via stdio; tools are subprocess-bounded with 60s wall-clock per tool call
- Write `harness/setup.sh` — builds the image via `docker build -t autoproduct-test-exec:latest containers/test-exec/`; records image digest to `.mas/build-info.yaml`; verifies digest at every harness startup (mismatch → `HarnessStartupError`)
- Update `harness/mcp_host.py` `_spawn_server_for("test_exec_server")` path to use `docker run --rm --network=none --read-only --cap-drop=ALL --security-opt=no-new-privileges --memory=2g --cpus=2 --pids-limit=256 --tmpfs=/tmp:rw,size=512m -v {worktree}:/work:ro --user 10001:10001 -i autoproduct-test-exec:{digest}` with stdio attached (no docker exec; the container itself is the MCP server process). Other servers (T1) continue spawning as direct Python subprocesses
- Add `docker` to `[tool.uv.dev-dependencies]` documentation note (Docker is a system dependency, not a Python dependency; document in README that users need Docker installed and running)

Success criterion: harness starts, `test_exec_server` spawns successfully (image hash logged), Correctness's verifier-stage can call `run_tests` against the worktree which executes inside the container and returns structured pass/fail; a deliberately-malicious test file with `os.system("touch /tmp/evil; curl example.com > /dev/null")` in `setUp()` runs but has no host-visible side effects (`/tmp/evil` does not appear on host; no network egress detectable). The container image digest is verified at every startup.

This is the work that makes the T3 sandbox real for `test_exec_server`. Static-analysis servers (T1) need no container — they don't execute user code. Only `test_exec_server` does, and only it gets full container isolation.

If Day 22.5 runs over 4 hours, the calibration signal is "container build infrastructure is more setup-heavy than I budgeted." Note in retro and accept that Day 22.5 + Day 26 together may each come in over budget.

#### Day 23 — Compound loop Stage 1

Tasks:
- Write `autoproduct/compound/weekly.py` with aggregation logic from §09.8.4.1
- CLI command: `autoproduct compound-loop --dry-run` for testing
- When run against 7 days of review data, aggregates signals and produces a PR-ready diff

```python
# autoproduct/compound/weekly.py
# (Full code per §09.8.4.1)

async def run_weekly_compound_loop(project_root: Path, llm: LLMClient, dry_run: bool = False) -> None:
    signals = _aggregate_signals(project_root, days=7)
    proposals = []

    for landing, sigs in signals.items():
        if len(sigs) < 3:
            continue
        proposal = await _propose_claude_md_update(llm, landing, sigs)
        proposals.append(proposal)

    if not proposals:
        print("No proposals this week.")
        return

    pr_body = _format_compound_loop_pr(proposals)

    if dry_run:
        print(pr_body)
    else:
        await _open_compound_loop_pr(project_root, pr_body)
```

Success criterion: `autoproduct compound-loop --dry-run` against accumulated AgentHire review data produces a PR body that proposes specific, evidence-backed CLAUDE.md updates.

#### Day 23b — Per-voter log + evidence ledger + tool audit

Tasks:
- Write `autoproduct/observability/voter_log.py` that appends one entry to `.mas/voters/{voter_name}/log.yaml` per review, per §09.8.5 (with `fcntl` locking)
- Write `autoproduct/observability/evidence_ledger.py` that builds the markdown table per §09.9.5.1 from `final_findings`, gate results, and per-voter outputs. Output: `.mas/reviews/{review_id}/evidence-ledger.md`
- Write `autoproduct/observability/tool_audit.py` — a thin in-memory accumulator that the `ToolRegistry.execute` wrapper appends to on every tool invocation; flushed to `.mas/reviews/{review_id}/tool-audit.yaml` at POST per §09.7.1
- Write `autoproduct/observability/cost_calculator.py` with the per-model pricing table (sourced from each provider's pricing page; pin date in a comment); compute `cost_estimate_usd` from `voter_token_usage`
- Wire all of the above into `post_node`: per-voter log entry, evidence ledger, tool audit log flush, cost calculation. The five writes happen in this order so that a partial crash leaves the most useful artifacts present (final.yaml first, then evidence ledger, then audit, then voter logs, then cost summary in pr comment)
- Build CLI helpers:
  - `autoproduct voter-log {voter_name} --last-week` — readable summary
  - `autoproduct ledger {review_id}` — print the evidence ledger to stdout
  - `autoproduct audit {review_id}` — print the tool audit log
- Add the `/mas feedback {finding_id} {correct|incorrect} "reason"` PR-comment webhook handler that backfills the `human_feedback` field in the correct voter's log entry

Success criterion: After running several reviews:
- Each voter's `log.yaml` accumulates one YAML entry per review
- `evidence-ledger.md` is generated for every review with a row per finding/gate
- `tool-audit.yaml` shows every tool invocation, voter that called it, and risk_level
- `cost_estimate_usd` appears in the PR comment summary
- All three artifacts land in the mas-reviews branch alongside `final.yaml`

#### Day 24 — Scheduler + weekend polish

Tasks:
- Set up weekly cron (either system cron for personal use, or Celery beat if webhook mode used)
- Test end-to-end: voter failure → HITL → resume → leader → POST → mirror → (next week's) compound loop
- Fix any state contract issues discovered

Success criterion (end of Week 4): Complete round trip works. Force a voter failure, HITL interrupts, resume, full pipeline continues, artifacts all correct.

---

### Week 5 — AgentHire integration + benchmarks

**Goal by end of week:** AgentHire has working `CLAUDE.md`, `.mas/`, `.claude/`; real-PR benchmark subset run produces recall and precision; pipeline is usable for daily work.

#### Day 25 — AgentHire project integration

Tasks:
- Create `CLAUDE.md` in AgentHire repo from §09.10.2 template
- Create `.mas/project.yaml` from §09.10.3
- Create `.mas/codebase_profile.yaml` from §09.10.4
- Create `.claude/skills/ats_parser_review.md` (AgentHire-specific)

Success criterion: Running `autoproduct review <real AgentHire PR>` uses the new config correctly; findings reference the AgentHire-specific patterns.

#### Day 26 — Deterministic tools (Semgrep, Bandit, pip-audit, TruffleHog, slopsquat, CSRF/SSRF probes, Playwright) + UI Behavior voter

Tasks:
- Install Semgrep, Bandit, pip-audit, TruffleHog locally; verify they run on AgentHire
- Write wrappers in `autoproduct/tools/deterministic/` for the four security tools (semgrep.py, bandit.py, pip_audit.py, trufflehog.py)
- Write `autoproduct/tools/deterministic/slopsquat_check.py` per §09.7.3.5 — parses dependency files (`requirements.txt`, `package.json`, `pyproject.toml`) for added packages in the PR diff; queries PyPI/npm registry; flags nonexistent packages, packages registered <180 days ago that resemble established names (Levenshtein ≤ 2), and packages with <100 weekly downloads
- Write `autoproduct/tools/deterministic/csrf_ssrf_probe.py` per §09.7.3.6 — uses tree-sitter index to find state-changing endpoints (POST/PUT/DELETE/PATCH) and verifies CSRF middleware coverage; finds outbound HTTP calls (requests/httpx/fetch/axios) with user-supplied URLs and verifies allowlist presence; framework-specific patterns for FastAPI/Django/Flask/Express/Next.js
- `tools_node` runs all six security/integrity tools in parallel, writes normalized output to state
- Write `autoproduct/tools/playwright_runner.py` per §09.7.2.7 — wraps `npx playwright test --reporter=json`, parses the JSON report, returns a trimmed summary
- Write `skills/ui_behavior.md` per §09.4.4.8
- Register `UIBehaviorVoter` in the pipeline; it activates only when `codebase_profile.ui.framework` is set AND the current PR touches UI files (detected by `analyze_node` setting `ui_behavior_voter_active = true`)
- Wire `test_gate_node` to run Playwright as part of Gate 2 when UI framework is configured

```python
# autoproduct/tools/deterministic/semgrep.py
async def run_semgrep(changed_files: list[str], repo_root: Path) -> list[dict]:
    proc = await asyncio.create_subprocess_exec(
        "semgrep", "--config=p/python", "--config=p/security-audit",
        "--json", *changed_files,
        stdout=asyncio.subprocess.PIPE,
        cwd=repo_root,
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
    except asyncio.TimeoutError:
        proc.kill()
        return []
    data = json.loads(stdout.decode())
    return [_normalize_semgrep(r) for r in data.get("results", [])]
```

The slopsquat_check and csrf_ssrf_probe tools follow the same wrapper shape (subprocess or in-process check, async, normalized output, timeout-bounded). Together they form the deterministic backstop that the Security Voter (§09.4.4.2) reads in addition to its LLM-level reasoning.

Success criterion: `tools_node` runs all six security tools in <120s total on a typical AgentHire PR (slopsquat adds ~2-5s for registry HTTPS calls; CSRF/SSRF probe adds ~1-3s for tree-sitter index lookups); Playwright wrapper runs an existing test file and returns structured pass/fail summary; on a UI-touching PR, the UI Behavior voter activates and emits findings that reference Playwright test coverage gaps; on a PR adding a new dependency, slopsquat_check produces a finding referencing the PyPI/npm registry response; on a PR adding a state-changing endpoint without CSRF middleware, csrf_ssrf_probe produces a `CSRF_MIDDLEWARE_ABSENT` finding.

Note on AgentHire scope: AgentHire's React frontend is the concrete UI testing target. AgentHire's FastAPI backend is the concrete CSRF/SSRF probe target — the probe should detect that AgentHire's existing endpoints have proper CSRF middleware and flag any new endpoint added without it. For non-UI projects, `codebase_profile.ui.framework` is left unset and the UI Behavior voter + Playwright runner simply don't activate. For projects using a framework not in the CSRF probe's allowlist, the probe writes `UNKNOWN_FRAMEWORK_CSRF_PROBE_SKIPPED` to state and the Security Voter handles it via LLM-only reasoning.

#### Day 26.5 — Auto-triage mode router (deterministic mode selection)

Tasks (≈3 hours; this is a half-day insertion to keep Days 26 → 27 contiguous):
- Write `autoproduct/orchestrator/mode_router.py` per §08.3.5.1 — pure function `select_mode(parsed_diff, codebase_profile, user_override) -> Literal["fast", "standard", "deep"]`
- Implement the conservative-by-default decision tree: any state-changing endpoint, any new dependency, any safety-removal signature, or > 50 lines / > 3 files lands in `standard`; high-risk paths (auth, billing, migration, prod IaC) land in `deep`; only AST-verified cosmetic diffs < 20 lines / < 2 files land in `fast`
- Helper `_has_safety_removal_signature(pr_diff)` uses tree-sitter to detect decorator-removal patterns, sanitization-call removal, and CORS/CSRF token removal — direct AST match, not LLM
- Wire into `dor_gate_node`: mode selected before voters spawn; logged into `state["selected_mode"]` and per-voter log
- Unit tests covering the conservative-by-default branches: a 5-line PR adding a POST endpoint must land in `standard`, not `fast`

Success criterion: given the AgentHire git history, the router downgrades to `fast` on docstring/rename PRs, holds `standard` on typical feature PRs, and escalates to `deep` on PRs touching `auth/`, `billing/`, or `migrations/` paths. Every routing decision is logged with the matched rule for audit.

#### Day 26.7 — `debt_server` MCP server (radon + jscpd + vulture, per `11-ultimate-architecture.md` Part 19)

Tasks (~2 hours; complements Day 26's deterministic tools):

- Install: `pip install radon vulture`; `npm install -g jscpd`
- Implement `autoproduct/mcp_servers/debt_server.py` per §19.2 — exposes `radon_complexity`, `jscpd_clone_detection`, `vulture_dead_code` via MCP `tools/list` and `tools/call`
- Each tool wraps the underlying CLI as subprocess + JSON parsing + normalized finding shape
- Update Style Voter spec frontmatter (`skills/style.md`) to add `debt_server` to `mcp_servers` list and the three tool names to `mcp_tools_allowlist`
- Update Style Voter skill body (the markdown after frontmatter) per §19.3 — instructions on how to interpret debt-server findings; specifically the GitClear-grounded "treat jscpd clones as `medium` by default; upgrade to `high` if the clone reproduces an existing repo function (verifiable via `code_intel_server.tree_sitter_query`)"
- Add `radon`, `vulture` to Appendix B core deps; jscpd installed via npm

Success criterion: on a synthetic AgentHire PR that adds a deliberate code clone (re-implementing `agenthire.utils.normalize_email` instead of importing it), the Style Voter receives `jscpd_clone_detection` findings and emits a `high`-severity finding referencing the existing utility. On a PR adding a function with cyclomatic complexity 13, Style Voter emits `medium` finding citing `radon_complexity`.

This is the deterministic backstop for the P9 (tech debt) pain point that Round 5 left as LLM-judgment-only.

#### Day 27 — benchmark runner

Tasks:
- Write `autoproduct/benchmarks/runner.py` per §09.9.6
- Fetch real-PR benchmark subset (20 instances) from repo
- Run `autoproduct` against each, compare findings to ground truth
- Output recall and precision

Success criterion: `make bench-fast` completes in <30 minutes, produces `benchmarks/results/<sha>/cr_bench.json` with recall and precision.

#### Day 28 — Calibration

Tasks:
- Review benchmark results; identify systemic false positives and false negatives
- Refine skill prompts ("what NOT to flag" sections) based on FP analysis
- Re-run benchmark; aim for recall ≥ 40%, precision ≥ 50%
- Commit benchmark results

Success criterion: the 20-instance real-PR benchmark subset meets recall ≥ 40%, precision ≥ 50%.

#### Day 29 — Live usage on AgentHire

Tasks:
- Run `autoproduct review` on every AgentHire PR for the week
- Note which findings are actionable, which are noise
- Refine prompts as needed
- Merge improvements back to main

Success criterion: autoproduct reviews at least 5 real AgentHire PRs during the week; >50% of findings are rated "actionable" by Melody on review.

#### Day 30 — Weekend polish + gate verification

Tasks:
- Address any accumulated issues from live usage
- Ensure all CLI commands work (review, replay, resume, compound-loop, bench, voter-log)
- Verify all four gates fire correctly in production AgentHire flow:
  - Gate 1 (DoR): a deliberately incomplete PR gets rejected without invoking voters
  - Gate 2 (Test Gate): a PR that drops coverage below threshold gets verdict REQUEST_CHANGES
  - Gate 3 (HITL): an ESCALATE verdict opens a real GitHub Issue and resumes correctly on comment
  - Gate 4 (Rollback): the rollback workflow file is present and bench-fast runs on the autoproduct:compound-loop label
- Verify per-voter log is accumulating entries for each review
- Verify the structured test report is populated for a UI-touching AgentHire PR and a non-UI PR (confirm `not_configured` vs real data)
- Write short usage notes

Success criterion (end of Week 5): `autoproduct` is in daily use on AgentHire; benchmark baseline is documented; all four gates demonstrated working end-to-end on real PRs; per-voter logs accumulating; structured test report rendering correctly in PR comments.

---

### Week 6 — Design docs + README + public

**Goal by end of week:** Documents 08-11 finalized; main README written; repo set to public.

#### Day 31 — Archive prior design docs

Tasks:
- Create `design-docs/archive/` directory
- Move the seven prior iteration documents (`01-initial-stage-design.md` through `07-path-calibration.md`) to archive
- Write `design-docs/archive/README.md` with a superseded notice

Success criterion: Archive contains the seven prior docs; `design-docs/` contains only 08-11 plus README.

#### Day 32 — Finalize 08-10

Tasks:
- Cross-reference check: all §09.x references from 08 point to real sections
- Fill in any TODO markers
- Ensure code snippets match the actual code committed

Success criterion: Someone reading 08-11 cold can understand the system without reading archive.

#### Day 33 — Write the main README

Tasks:
- Write `README.md` at repo root
- Short description of what `autoproduct` does
- Quickstart (install, minimal config)
- Link to design-docs for depth
- License notice

```markdown
# autoproduct

A multi-agent code review and test system. Runs heterogeneous
specialist agents over a pull request, synthesizes findings through a
leader, surfaces escalations through human-in-the-loop gates, and
compounds its learning over time.

## What it does

Given a pull request, `autoproduct`:

1. Runs six specialist voters in parallel (Correctness, Security,
   Performance, Context, Repo Graph, Style) — each on a different model
   family
2. Runs deterministic SAST, secret-scanning, dependency-audit, and
   symbol-graph analysis alongside
3. Synthesizes findings through a Leader agent with structured verdict
   and taxonomy signals
4. Generates tests including adversarial mutation testing
5. Posts a structured PR comment and emits YAML artifacts
6. Accumulates signals over time into project constraints via a weekly
   compounding loop (self-improving context pattern)

## Status

Covers the code review and test stages of the software development
cycle. Later stages (spec-to-code, release, deploy, observability,
feedback-to-spec) are out of scope for this implementation.

## Quickstart

```bash
pip install autoproduct
autoproduct init                    # Creates .mas/ and .claude/ templates
# Edit CLAUDE.md and .mas/project.yaml
autoproduct review https://github.com/you/project/pull/42
```

## Design

See [`design-docs/`](design-docs/) for the full design:

- [`08-foundation.md`](design-docs/08-foundation.md) — Problem, research, architecture
- [`09-system-design.md`](design-docs/09-system-design.md) — Agents, state, tools, HITL, compounding
- [`10-implementation-plan.md`](design-docs/10-implementation-plan.md) — Build plan

## License

MIT.
```

Success criterion: README is readable, accurate, under 150 lines.

#### Day 34 — Repo hygiene

Tasks:
- Add `LICENSE` (MIT)
- `.gitignore` excludes `.mas/reviews/`, `__pycache__/`, `.mutmut-cache`, `benchmarks/results/` (optional commit)
- Tag `v0.1.0`
- Final read-through of all four design docs

Success criterion: Clean `git log`; one commit tagged v0.1.0.

#### Day 35 — Make public + interactive deep-dive wrapper

Tasks:
- Toggle repo visibility to public
- Update personal site / LinkedIn with link (if desired)
- First public commit
- Implement the `--interactive` flag for `autoproduct deep <PR-URL>` (§08.3.5): the same voter skill files run via Claude Code Agent Teams instead of LangGraph. Implementation is a thin wrapper in `autoproduct/cli/interactive.py` (~150 lines): launch Claude Code with the project's `.claude/skills/` registered, hand each voter as a separate agent, write the same final.yaml + evidence ledger artifacts on session close.
- Document the interactive surface in README with a 1-paragraph "When to use": batch mode for daily flow, interactive mode for the 1-2 PRs/week that warrant deeper investigation.

Success criterion: Repo is public. A cold reader can clone, install, and run a review on their own PR in under 30 minutes via either `autoproduct review <PR-URL>` (batch) or `autoproduct deep <PR-URL> --interactive` (interactive).

#### Day 36 — Retrospective and handover

Tasks:

- Write `RETRO.md` at repo root, committed to main. Structure:
  1. **What worked** — 3-5 specific things (e.g., "git worktree isolation saved two near-misses where generated tests touched the main checkout")
  2. **What didn't work** — 3-5 specific things (e.g., "Gemini 3.1 Pro rate-limiting on parallel voters caused retries ~8% of reviews")
  3. **Time vs plan** — for each Week, actual hours spent vs the 3-5h/day × 7d = 21-35h budget; note overrun causes
  4. **Gates effectiveness** — for each of the 4 gates, how many PRs were caught, any false positives/negatives
  5. **v0.2.0 backlog** — top 3-5 items to do next, each with rough effort estimate
  6. **Architecture decisions revisited** — list any design choices from §08/§09 that proved wrong; link to the ADR if one was written during implementation
- Archive external dependencies: run `pip freeze > RETRO-deps.txt` and commit alongside, so a future reader knows exactly what versions this v0.1.0 was built against
- Update `CHANGELOG.md` with the v0.1.0 entry (features delivered, known limitations)
- Update README.md's "Status" section: move from "v0.1.0 in development" to "v0.1.0 released"

Success criterion: `RETRO.md`, `RETRO-deps.txt`, and `CHANGELOG.md` entries are all committed to main and tagged alongside v0.1.0. Implementation is done. The system is in use. Design docs are public.

---

### Week 7 — Deployment MAS scaffolding

**Goal by end of week:** `autoproduct deploy review <PR-URL>` runs the full Deploy Review state machine end-to-end on a real AgentHire PR with at least 2 of 4 voters wired (DeployConfig + Migration). No live canary integration yet.

#### Day 43 — Deploy Review graph + state extension

Tasks:

- Implement `DeployStateExtension` per §09.11.9; merge into `ReviewState` as a discriminated union on `stage`
- Implement `build_deploy_graph()` per §09.11.4; node stubs that just log + transition for now
- Implement `deploy_dor_gate_node` per §09.11.10 with all 5 entry checks
- Implement `deploy_init_node` and `deploy_analyze_node`; the analyze node classifies `routine | risky | live_canary`
- Wire conditional edges; add unit tests covering each routing predicate

Success criterion: A test PR triggers the deploy graph and exits at `deploy_post` with a "no deploy review needed" comment when no IaC/CI files are touched. A test PR with `.github/workflows/` changes routes through `deploy_tools` correctly.

#### Day 44 — Deterministic tools: terraform + helm + kubectl dry-run

Tasks:

- Implement `autoproduct/tools/deterministic/terraform.py` — wraps `terraform validate` and `terraform plan` (no `apply`); never registered above L2
- Implement `autoproduct/tools/deterministic/helm.py` — wraps `helm template` and `helm lint`
- Implement `autoproduct/tools/deterministic/kubectl.py` — wraps `kubectl --dry-run=server` against staging cluster only (project config supplies kubeconfig path; production kubeconfig is **never** loaded by autoproduct)
- Add tool registry entries in `autoproduct/tools/registry_deploy.py` — explicit L1/L2 tags; L3+ symbols structurally absent (per §09.7.1 pattern)
- Each wrapper has a 60s timeout, JSON output, and graceful failure mode

Success criterion: Each tool wrapper runs against a fixture (small Terraform module, Helm chart, K8s manifest) and produces structured output. Dry-run failure (e.g., missing required field in K8s manifest) is captured as a structured tool error, not a Python exception.

#### Day 45 — DeployConfig voter

Tasks:

- Write `skills/deploy_config.md` with prompt structured per §09.4.4 voter skill template
- Implement DeployConfig voter class extending base `Voter`; uses Sonnet 4.6
- Voter context includes: terraform-plan output, helm-template output, kubectl-dry-run output, the diff hunks themselves
- Findings target: missing health-check probes, untyped resource limits, `image: latest` tags, missing rollback strategy, missing resource quotas, exposed unnecessary ports
- Add 5+ test fixtures covering common findings; voter must hit ≥80% recall on the fixtures

Success criterion: DeployConfig voter on a curated buggy K8s manifest catches 4 of 5 known issues (≥80% recall). Per-voter log records findings with proper file:line locations.

#### Day 46 — Migration voter + DB shadow mirror

Tasks:

- Implement `autoproduct/tools/deterministic/migration_dryrun.py` — applies migration script to a copy of staging DB schema, measures runtime, detects lock-table acquisition (uses `EXPLAIN ANALYZE` for SQL or framework-specific dry-run for Alembic/Django)
- The shadow DB connection string is read from `MIGRATION_SHADOW_DSN` env var; never the production DSN
- Write `skills/migration.md` covering: destructive ops detection (DROP, ALTER without IF EXISTS, NOT NULL on existing table without default), missing reverse migration, unsafe data backfills, lock-acquisition risk
- Implement Migration voter class using Opus 4.7 (high stakes)
- Add fixtures: 3 known-bad migrations + 2 known-safe ones; voter must classify all 5 correctly

Success criterion: On a real AgentHire migration that adds a NOT NULL column, the Migration voter flags the missing default value AND surfaces the lock-acquisition risk on the user table.

#### Day 47 — Verify + Leader for deploy

Tasks:

- Implement `deploy_verify_node` — same fresh-agent verification pattern as §09.5.4.7, applied to deploy findings
- Implement `deploy_leader_node` per §09.11.7 with 12-verdict taxonomy; reuses the confidence-scoring logic from §09.4.7
- Wire end-to-end on a real AgentHire PR that touches CI config: graph runs, voter findings emitted, verifier runs, leader synthesizes
- Per-voter log entries written to `.mas/voters/deploy_config/log.yaml` and `.mas/voters/migration/log.yaml`
- PR comment formatter for deploy review (different template than code review — emphasizes deploy risks)

Success criterion: `autoproduct deploy review <agenthire-test-PR>` runs end-to-end in <5 minutes, posts a structured PR comment listing deploy findings, writes evidence ledger to `.mas/deploys/{deploy_id}/`. At least one finding traces to a real deploy issue caught by the voter pair.

#### Day 48 — Weekend integration test + docs

Tasks:

- Run deploy review on 5 historical AgentHire deploy PRs; document hit/miss/false-positive in `implementation-notes-deploy.md` (private)
- Write basic deploy review docs in `docs/deploy-review.md` covering: when it triggers, what voters run, how to read the verdict
- Update README's "Status" section to note Deploy Review at v0.1.5 alpha

Success criterion (end of Week 7): Deploy Review state machine runs end-to-end on real PRs. Two of four voters operational. Tools wired. Verdict 12-tuple implemented.

---

### Week 8 — Trust tiers, Policy-as-Prompt, CanaryAnalysis voter

**Goal by end of week:** Trust-tier resolution working; policy-as-prompt compiler runs; CanaryAnalysis voter wired; `.mas/deploy-policy.yaml` template documented.

#### Day 49 — Trust-tier framework

Tasks:

- Implement `autoproduct/policy/trust_tier.py` — loads `.mas/deploy-policy.yaml`, resolves per-voter tier per environment (staging/production)
- Implement the `forbidden_autonomous` ceiling: reject any project config that sets a forbidden combination at startup with clear error message
- Tier propagation: each voter reads its resolved tier from `state["trust_tier"][voter_name]` (per ADR-001 single ReviewState); voters at `insight` tier emit findings only with `decision: null`; voters at `assistive` tier emit recommendations; voters at `autonomous-within-guardrails` tier execute (subject to policy check)
- Comprehensive unit tests: every tier × every voter × every forbidden_autonomous override

Success criterion: A `.mas/deploy-policy.yaml` that tries to set `production:migration_voter: autonomous` is rejected at config load with the exact error string. A staging deploy with all voters set to autonomous executes the auto-action path.

#### Day 50 — Policy-as-Prompt compiler

Tasks:

- Implement `autoproduct/policy/compile.py` — reads `.mas/deploy-policy.yaml` `guardrails` block, compiles each rule into either a Python deterministic check or a prompt-based classifier
- Deterministic rules: time-window matchers, regex on secrets, glob-matched paths, numeric thresholds (e.g., `request_count < 100`)
- Prompt classifiers: for semantic policies, generate a Sonnet 4.6 classifier prompt with the rule text + 3 positive + 3 negative examples (auto-extracted from the rule's description, validated by human review at compile-time)
- Output `runtime_classifiers.json` checked into `.mas/policy/` for auditability
- Re-compilation is triggered by `autoproduct policy compile` (manual) or by `autoproduct deploy review` if the policy file's mtime is newer than the compiled artifact

Success criterion: Compile the AgentHire example policy. Resulting JSON has 3 deterministic rules (time-window, secret-regex, request-count) and 2 prompt classifiers (NO_PROD_MIGRATIONS_WITHOUT_HUMAN, NO_AUTOROLLBACK_FOR_LOW_TRAFFIC). Each classifier prompt validates against its 6 examples (3 positive, 3 negative) at compile time.

#### Day 51 — Policy check node + violation routing

Tasks:

- Implement `policy_check_node` — runs all compiled rules against voter inputs and leader outputs in parallel
- Each rule emission appends to `.mas/policy/check_log.yaml` with rule_id + classifier_output + decision
- Hard-fail routing: any `violation` short-circuits to `deploy_hitl` per §09.11.4 graph; voters never run if policy fails
- Test: a deploy attempted during the configured freeze window is blocked with verdict `ESCALATE_POLICY_VIOLATION`; a deploy outside the window passes the gate

Success criterion: A test PR with a destructive migration attempted on production triggers `NO_PROD_MIGRATIONS_WITHOUT_HUMAN` and routes to `deploy_hitl`. The policy log clearly identifies which rule fired and what evidence triggered it.

#### Day 52 — CanaryAnalysis voter

Tasks:

- Implement `autoproduct/tools/deterministic/argocd.py` and `flagger.py` for reading rollout state
- Implement `autoproduct/tools/prometheus_client.py` — query API client; common queries (request rate, error rate, p50/p99 latency) factored into named methods
- Write `skills/canary_analysis.md` covering: spec validation (sufficient iterations, error-rate metric configured, threshold sensible) and live execution (interpret current canary metrics)
- Implement CanaryAnalysis voter using Sonnet 4.6 — has both a "spec review" path (PR-time) and a "live decision" path (during canary execution)
- Live path is gated: only invoked when `state.canary_in_flight == True`

Success criterion: Canary spec review on an Argo Rollouts AnalysisTemplate produces correct findings. A simulated live canary with `error_rate: 0.08` and threshold `0.05` causes the voter to recommend ROLLBACK with confidence ≥80.

#### Day 53 — Rollback voter + integration with Argo Rollouts/Flagger

Tasks:

- Write `skills/rollback.md` covering decision logic: synthesize CanaryAnalysis findings + service health context + traffic volume; emit AUTO_ROLLBACK or HOLD_FOR_HUMAN
- Implement Rollback voter using Opus 4.7
- Auto-rollback execution path (only at autonomous-within-guardrails tier on staging by default): write a status update to the Argo Rollouts AnalysisRun OR adjust the Flagger Canary's threshold; do **not** call kubectl directly — let the existing controller execute
- Audit log every rollback decision (recommendation OR execution) to `.mas/deploys/audit.yaml` regardless of trust tier

Success criterion: On a synthetic canary that breaches error-rate threshold during staging, the system writes the AnalysisRun failure condition and the existing Argo Rollouts controller rolls back. On a production canary with the same scenario, the verdict is `HOLD_FOR_HUMAN` and a structured incident is opened.

#### Day 54 — Deploy review benchmark calibration

Tasks:

- Curate 10-15 deploy-relevant historical AgentHire PRs with known issues (deploy config bugs, migration risks, canary spec issues)
- Run the now-complete 4-voter deploy review pipeline on each
- Measure deploy-stage recall, precision, and false-positive rate
- Tune voter prompts; if recall <70% on this set, do not advance to Week 9 — iterate prompts first
- Commit results to `benchmarks/deploy-calibration-week8.md`

Success criterion (end of Week 8): All 4 deploy voters operational. Trust-tier framework resolves and enforces. Policy compiler runs. Canary spec review and live-canary decisions both work. Recall ≥70% on calibration set.

---

### Week 9 — Maintenance MAS scaffolding

**Goal by end of week:** Webhook ingest works; Triage and RootCause voters wired; basic incident report emitted to `.mas/incidents/`.

#### Day 55 — Maintenance graph + state extension

Tasks:

- Implement `MaintenanceStateExtension` per §09.12.8
- Implement `build_maintenance_graph()` per §09.12.4 with all 9 nodes; stub bodies
- Implement `ingest_signal_node` with dedupe via `dedupe_key` against `.mas/incidents/index.yaml` from past 7 days
- Routing predicates: `route_after_ingest` returns `new_incident | duplicate | low_severity`

Success criterion: A test webhook payload (synthetic Sentry event) ingests, dedupes correctly against an existing incident, and routes to triage for new ones.

#### Day 56 — Webhook receiver + signal source clients

Tasks:

- Implement `autoproduct/api/maintenance_webhook.py` — FastAPI endpoint(s) per signal source: `/webhooks/sentry`, `/webhooks/datadog`, `/webhooks/pagerduty`
- Each handler validates the signature (per source's documented webhook auth scheme), normalizes the payload to a uniform internal representation, and triggers the maintenance graph asynchronously via Celery
- Implement `autoproduct/tools/sentry_client.py`, `datadog_client.py`, `pagerduty_client.py` — all read-only methods only; PagerDuty client structurally cannot acknowledge or resolve incidents (no method exists)
- Configure webhook URLs in `.mas/project.yaml` under `maintenance.webhook_endpoints`

Success criterion: A real Sentry test event posts to the webhook, validates the signature, normalizes correctly, and lands in the maintenance graph. Same for Datadog and PagerDuty test events.

#### Day 57 — Triage voter

Tasks:

- Write `skills/triage.md` — input: signal payload + recent deploy history (read from `.mas/deploys/index.yaml`) + service health snapshot
- Triage voter (Sonnet 4.6) outputs: severity classification, suspected service, correlation score with recent deploy, dedupe key
- Implement learned-skill registry stub: `.mas/learned_skills/` directory; for now, Triage just reads the index file (initially empty) and matches against any skill present (semantic match via Haiku call per skill)
- Triage emission writes to `.mas/incidents/{id}/triage.yaml`

Success criterion: A real Sentry event for a recent AgentHire production issue triages correctly: severity classified (high/medium/low), suspected service named, correlation with recent merge identified.

#### Day 58 — RootCause voter + parallel hypotheses

Tasks:

- Implement Jaeger client + Loki client (read-only methods only)
- Write `skills/root_cause.md` — voter is told to generate 2-3 parallel hypotheses, gather evidence for each, then rank by confidence
- RootCause voter (Opus 4.7) outputs: top hypothesis + confidence + evidence paths
- Voter explicitly instructed to *not* commit to a hypothesis prematurely; if all hypotheses come back below 60% confidence, output the highest one but mark `confidence: <60`
- Evidence is recorded via path references, not pasted: voter writes `evidence_paths: [".mas/incidents/{id}/datadog_logs.txt", "..."]`

Success criterion: On a known historical incident (DynamoDB throttling causing 500s), RootCause produces hypothesis "DynamoDB read capacity exceeded" with confidence ≥80 and evidence paths pointing to the actual log query results.

#### Day 59 — Confidence-check loop

Tasks:

- Implement `confidence_check_node` per §09.12.4 with `CONFIDENCE_THRESHOLD = 60` and `MAX_REINVESTIGATIONS = 3`
- On reinvestigation: increment counter, append the previous attempt to context (so subsequent calls see what was tried), invoke RootCause again
- After MAX_REINVESTIGATIONS, route to `hitl` with all 3 hypotheses + their confidences for human review
- Comprehensive test: synthetic incident where first 2 hypothesis attempts are below threshold, third is above — confirm flow exits via `sufficient` after the third attempt

Success criterion: A simulated incident with confounding evidence triggers 2 reinvestigation passes and resolves on the third with confidence ≥60. A truly intractable incident escalates to HITL after 3 attempts with structured "what we tried" report.

#### Day 60 — Maintenance verdict + incident report writer

Tasks:

- Implement `maintenance_leader_node` and `post_incident_node`
- Maintenance Leader emits 8-verdict taxonomy per §09.12.7
- Incident report template at `.mas/templates/incident_report.md` (project-overridable)
- Reports include: signal payload (redacted of any secrets per §11.6 SECRETS_NEVER_IN_DEPLOY_OUTPUT pattern), triage classification, root-cause hypothesis with evidence paths, action taken (or escalation reason)
- Audit log to `.mas/incidents/audit.yaml`

Success criterion (end of Week 9): A real Sentry event for an AgentHire incident flows webhook → triage → root-cause → leader → incident report. Report is human-readable and identifies cause + suggested action. No fix-PR generation yet.

---

### Week 10 — FixPR voter + auto-action shim + LearnedSkill voter

**Goal by end of week:** Maintenance produces fix-PRs that re-enter Code Review; auto-action shim works for staging only; LearnedSkill registry generates first proposals.

#### Day 61 — FixPR voter

Tasks:

- Write `skills/fix_pr.md` — input: RootCause hypothesis + affected code files + existing tests for those files
- FixPR voter (Opus 4.7) generates: code patch + corresponding test cases that would have caught the bug
- Implement git worktree setup for FixPR (similar to §09.5.4.9 adversarial test): branch named `mas-fix/{incident_id}`, isolated checkout
- FixPR opens a PR via GitHub API with body template noting `provenance: maintenance`, links to incident report, lists files changed
- The PR's metadata flag flows back into Code Review when the PR is reviewed (per §09.12.11 cross-stage feedback)

Success criterion: For a known historical incident, FixPR voter generates a PR with both the code fix and a test that would have caught the original bug. PR is opened in `assistive` mode (always; never autonomous regardless of trust tier).

#### Day 62 — Auto-action shim

Tasks:

- Implement `autoproduct/tools/auto_action_shim.py` per §09.12.5 with allowlist matching, constraint checking, cooldown
- Three default allowlist entries: `scale_up_replicas` (max +1), `restart_pod` (max 1/hr/service), `rotate_to_previous_image` (only if current deployed <30min ago)
- Audit log writes regardless of executed/rejected
- Helper: `autoproduct doctor maintenance-actions` shows the resolved allowlist plus cooldown state (does not execute)

Success criterion: A maintenance run that proposes "delete production database" sees the action rejected (not in allowlist), audit-logged, and routed to ESCALATE_INCIDENT_OUT_OF_BOUNDS. A proposed `scale_up_replicas` for a service in the allowlist with available cooldown executes; second attempt within cooldown is rejected.

#### Day 63 — LearnedSkill voter + registry mechanics

Tasks:

- Write `skills/learned_skill.md` — input: triage + root-cause history across past 30 days (read from `.mas/incidents/`)
- Voter detects recurring patterns (same service + similar root-cause >=3 times in window)
- For each detected pattern, generate a skill YAML per §09.12.6 example format
- Implement compounding-loop integration: every Sunday, the existing weekly compound loop runs the LearnedSkill voter and proposes new skills via PR (mirroring CLAUDE.md compound loop §09.8.4)

Success criterion: After seeding 4 synthetic incidents of the same DynamoDB-throttling class, the LearnedSkill voter generates the skill YAML matching the §09.12.6 example shape, opens a PR for human review, and the PR is mergeable (no syntax/lint errors).

#### Day 64 — Maintenance-driven CLAUDE.md updates

Tasks:

- Extend the compounding loop (§09.8.4) to read maintenance-stage taxonomy signals alongside code-review signals
- Pattern detection: services that recur in incident root-causes get flagged as "high-risk" in CLAUDE.md proposals
- Per §09.12.11: incidents flagged as caught-too-late suggest CLAUDE.md additions for review-stage prevention
- Compounding loop's weekly PR now has a "Maintenance signals" section listing top 3 recurring incident patterns

Success criterion: After a week of synthetic incidents involving `parsers/workday.py`, the compound loop's PR includes a proposed CLAUDE.md line "Workday parser fragility — reviewers, look for unchecked schema assumptions". PR is human-readable; signal traceback to actual incidents is included.

#### Day 65 — Production health gate + signal filtering

Tasks:

- Implement Gate 6 logic: severity threshold (configurable, default >=high), service ownership check, dedupe cross-reference
- Rejected signals write to `.mas/incidents/rejected.yaml` (audit-only, no LLM tokens consumed)
- "Maintenance hours" config (rare): if set, signals outside the window buffer until next window; nothing blocks for >24h though (escalates as `ESCALATE_INCIDENT_BUFFERED_TOO_LONG`)
- Health metrics: `autoproduct doctor maintenance-stats` shows ingest count, dedup rate, escalation rate per week

Success criterion: A flood of low-severity duplicate alerts (50 signals in 5 min) results in 1 incident triage and 49 dedup-rejected entries. Gate 6 budget consumed: 0 LLM tokens for the rejected ones.

#### Day 66 — Weekend stress test + retro

Tasks:

- Synthetic stress test: replay 30 days of AgentHire production incidents through the maintenance pipeline at accelerated speed
- Measure: triage classification accuracy, RootCause confidence distribution, fix-PR generation success rate, learned-skill detection delay
- Document gotchas in `implementation-notes-maintenance.md` (private)

Success criterion (end of Week 10): Maintenance MAS handles real production signals end-to-end. FixPRs generated. Auto-action shim enforces allowlist. LearnedSkill generates first proposals. Gate 6 filters appropriately.

---

### Week 11 — Cross-stage integration testing on AgentHire

**Goal by end of week:** All four stages operational on AgentHire; cross-stage signal flow verified end-to-end on real production usage.

#### Day 67 — Stage routing and shared state

Tasks:

- Implement the unified state graph that dispatches between Code Review, Test, Deploy Review, Maintenance based on `stage` field
- Each stage's substate is its own TypedDict extension; the discriminated union pattern keeps types clean
- Verify checkpointer compatibility: a state mid-stage can be resumed cleanly even if the autoproduct binary is upgraded between checkpoint and resume

Success criterion: An interrupted Deploy Review (e.g., killed mid-vote) resumes correctly when restarted via `autoproduct resume <state_id>`.

#### Day 68 — Real PR walk-through

Tasks:

- Pick a real AgentHire PR that touches code, CI config, and a migration
- Walk it through Code Review → Test → Deploy Review manually, observing each stage's verdict
- Document any places where stages misalign (e.g., Code Review approves but Deploy Review identifies an issue that Code Review's voters should have caught)
- Cross-stage feedback: if Deploy Review flags something Code Review missed, log a "missed in code review" tag for the next compound loop cycle

Success criterion: One real AgentHire feature PR walks through 3 stages end-to-end. Verdicts at each stage are sensible. Missed-issue feedback is recorded.

#### Day 69 — Live canary test

Tasks:

- Set up a staging deploy with a deliberately-flaky version (e.g., introduces a 1% error rate)
- Run the canary through Argo Rollouts; let CanaryAnalysis voter observe
- Verify auto-rollback triggers correctly at staging trust tier
- Test the same scenario at production trust tier — verify it correctly produces HOLD_FOR_HUMAN instead of executing rollback

Success criterion: Staging canary auto-rolls back. Production canary holds for human approval. Both are audit-logged.

#### Day 70 — Real production incident replay

Tasks:

- Pull last 30 days of real AgentHire Sentry events; replay through Maintenance MAS
- Verify: dedup rate, triage accuracy on known-classified incidents, RootCause confidence correlates with how easy human investigation was
- For 2-3 high-confidence cases, let FixPR generate a PR; manually review the PR — does it solve the actual issue?

Success criterion: Replay completes in <2 hours. Triage accuracy >70% on known-classified incidents. At least 1 generated fix-PR is mergeable as-is or with trivial human edit.

#### Day 71 — End-to-end customer-facing scenario

Tasks:

- Synthetic scenario: a user reports a parser bug → maintenance triages → root-cause identifies → fix-PR opened → fix-PR re-enters Code Review → approved → Deploy Review at staging → canary observes → auto-promote → production health gate watches → no recurrence → incident closed
- Time the whole flow; verify every transition is audit-logged
- Identify any gates that need tuning (e.g., confidence thresholds, cooldowns)

Success criterion: Full scenario completes in under 90 minutes wall time on AgentHire infrastructure. Every state transition is in `.mas/audit.yaml`. The customer-facing fix flowed through 4 stages without human intervention except final PR merge approval.

#### Day 72 — Weekend retro

Tasks:

- `RETRO-week11.md`: what worked, what didn't, what tuning is needed for week 12
- Time spent vs budget; flag any voter that consumed disproportionate tokens

Success criterion (end of Week 11): All four stages work end-to-end on AgentHire. Cross-stage flow validated. Audit log complete.

---

### Week 12 — Hardening + observability

**Goal by end of week:** Production-readiness pass: error handling, observability, cost dashboards, runbooks.

#### Day 73 — Error budgets and graceful degradation

Tasks:

- Implement cost budgets per stage in `.mas/project.yaml` `budgets`
- When a stage hits 80% of budget, log warning; at 100%, fail-soft — voters get "you have N tokens left" in their context, fewer total calls
- Verify each stage degrades gracefully under provider failure (Anthropic 5xx, etc.) — fall back to Sonnet-only if Opus unavailable, fall back to single voter if multiple voters fail

Success criterion: A simulated Anthropic outage during a Deploy Review degrades to OpenAI-only voters with notes-in-comment about reduced coverage; the verdict is still produced (with appropriate confidence reduction).

#### Day 74 — Observability dashboards

Tasks:

- Build a minimal Streamlit/Datasette dashboard at `dashboard/` that reads from `.mas/` directories
- Pages: per-stage verdict distribution (last 7d, 30d), voter cost breakdown, escalation rate, fix-PR merge rate, learned-skill registry
- Dashboard runs locally; not deployed; not multi-user; just "Melody opens it once a week"

Success criterion: Dashboard shows current state across all 4 stages on AgentHire data. Useful enough that the weekly compound-loop review uses it as the primary read.

#### Day 75 — Runbooks for each ESCALATE_*

Tasks:

- Write `docs/runbooks/` with one runbook per ESCALATE_* verdict — what the human does, where to look first, common false-positives
- Total: 12 (deploy) + 8 (maintenance) + 8 (code review/test) — about 20 runbooks
- Each runbook is short (<1 page), structured: signal, immediate action, investigation steps, resolution criteria

Success criterion: Each runbook is reviewed by Melody-as-on-call simulating a 3am page; quality bar is "would this be enough at 3am?"

#### Day 76 — Production rollout protocol

Tasks:

- Document the protocol for moving each stage from `insight` to `assistive` to `autonomous-within-guardrails`
- Trust-tier raise is a versioned change to `.mas/deploy-policy.yaml` and `.mas/maintenance-policy.yaml`; PR review required
- Compounding loop's weekly PR includes a recommendation when a voter's metrics support a tier raise (action rate ≥80%, miss rate ≤20% for 4 weeks); but the PR is the proposal — Melody reviews and merges

Success criterion: Documentation answers "when can I raise the trust tier for X?" with concrete metrics. A simulated PR proposing tier raise is generated correctly.

#### Day 77 — Cost dashboard reconciliation

Tasks:

- Build `cost_reconciliation.py` — reads `.mas/voters/*/log.yaml` and reconciles against actual provider usage (Anthropic Console, OpenAI dashboard, etc.)
- Discrepancies (e.g., we logged $X but provider charged $Y) are flagged for investigation; commonly indicate a missing log entry
- Weekly cost report goes into the compounding loop's PR

Success criterion: Reconciliation runs over week 11 data; discrepancy <5%.

#### Day 78 — Weekend retro

Tasks:

- Validate against the methodology note's §47 Runtime Observability checklist (correlation IDs, replay capability, cost tracking)
- Mark any items still missing as backlog for v0.2.0
- `RETRO-week12.md`

Success criterion (end of Week 12): System is production-ready. Observability, error handling, runbooks, cost reconciliation all functional.

---

### Week 13-14 — Real production usage at AgentHire scale

**Goal by end of weeks 13-14:** AgentHire runs autoproduct in production for 2 weeks; collect real signal; tune.

#### Days 79-92 (Weeks 13-14)

Tasks:

- AgentHire production on autoproduct: every PR goes through Code Review → Test → Deploy Review; production signals flow to Maintenance
- Daily check: `autoproduct doctor` to verify nothing's broken; review escalations
- Weekly compound loop runs; review proposed CLAUDE.md updates and learned-skill proposals
- Collect quantitative metrics: PR-to-merge time delta (with vs without autoproduct, comparing to historical), incident-MTTR delta, fix-PR merge-as-is rate
- For any voter at <80% action rate after 2 weeks, root-cause why — usually a skill-prompt issue
- Document any class of issue that the system *missed* (caught later by Melody manually) — these become §09.X.Z follow-ups

Success criteria:

- 100% of merged PRs have a Code Review verdict
- 90% of deploys have a Deploy Review verdict
- 95% of Sentry events with severity ≥high enter Maintenance
- At least 3 incidents resolved end-to-end with autoproduct's fix-PRs (merged after human review)
- At least 1 learned skill is created from real recurring incidents
- No production-mutating action executed outside the allowlist

---

### Week 15-16 — Polish + benchmark calibration

**Goal by end of weeks 15-16:** All metrics within target ranges; documentation complete; design docs reflect actual implementation.

#### Days 93-106 (Weeks 15-16)

Tasks:

- Recalibrate every voter on the data accumulated weeks 13-14
- For voters with action rate <80%, tune skill prompts and re-benchmark
- For voters with miss rate >20%, expand skill targets or add a verifier check
- Update `09-system-design.md` to reflect any architectural decisions that changed during implementation; cross-reference with archive iterations to maintain history
- Write `RETRO.md` cumulative — what worked, what didn't, what changes for v0.2.0
- Ensure all 6 gates have corresponding test coverage and runbook
- Final sweep: every cross-reference in §08/§09/§10 resolves; no stale section numbers

Success criterion: Every metric in §09.4.2 (action rate ≥60%, miss rate ≤30%, cost per acted-on finding ≤$5) is met or has a documented reason for missing it. Design docs are accurate.

---

### Week 17 — Public release prep

**Goal by end of week 17:** Repo is publishable; README reads well to a cold visitor.

#### Days 107-112

Tasks:

- Repo cleanup: remove implementation-notes-*.md files (private notes), validate no secrets in committed files (`autoproduct doctor secret-scan`)
- README.md polish: concrete onboarding instructions, screenshots of dashboard, link to design docs
- `CONTRIBUTING.md` — minimal; "this is a personal infra reference, not seeking contributors, but if you find a bug...."
- License: MIT
- Public domain registration if applicable (handle, vanity URL)
- Last hallucination sweep: same 29-pattern grep that caught earlier issues

Success criterion: A cold reader can clone the repo, read 10 minutes, understand what autoproduct is and where to start.

---

### Week 18 — Public release + retrospective

**Goal by end of week 18:** Repo public; retrospective written.

#### Days 113-119

Tasks:

- Toggle repo to public
- Tag `v1.0.0` (since v0.1.0 was the code-review-only milestone in week 6, the 4-stage system is v1.0)
- Personal site / LinkedIn update with link
- Write `RETRO.md` cumulative across the full 24-30 week build: what surprised, what didn't, what would have been done differently
- Time vs plan: 24-30 week × 3-5 hours/week budget = 84-140 hours; document actual hours spent across the four milestones (v0.1.0 / v0.5.0 / v0.8.0 / v1.0.0)
- v1.1.0 backlog: top 5-7 items, with rough effort estimate each

Success criterion: Repo is public. v1.0.0 tagged. RETRO.md committed. 中文 AI 圈 announcement post drafted (in `docs/blog-post-zh.md`, optional publication).

---


## Appendix A — Glossary

| Term | Meaning |
|---|---|
| Voter | A specialist LLM agent that produces findings for one domain (correctness, security, etc.) |
| Leader | The synthesizer agent that aggregates voter findings into a final verdict |
| Finding | A structured claim about the PR (severity, confidence, location, claim, evidence) |
| Taxonomy signal | A structured piece of information emitted by Leader for the compounding loop. Uses STAR-L schema (Situation, Task, Approach, Result, Landing) |
| Landing | The "where does this signal go?" field of a taxonomy signal; points to a section of CLAUDE.md |
| HITL | Human-in-the-loop. The system pauses, opens a GitHub Issue, and waits for human input |
| Compounding loop | Weekly cron that reads accumulated signals, proposes CLAUDE.md updates via PR |
| Self-improving context pattern | The general research direction where an LLM system's scaffolding (instructions, constraints, accumulated playbook) is optimized rather than its weights; see ACE (arXiv:2510.04618) |
| DAPLab | The Columbia research lab that published the 9-pattern vibe-code failure taxonomy |
| Real-PR benchmark subset | The 20-instance benchmark used for recall/precision calibration; specific benchmark chosen at implementation time (see §11 Decision 15) |
| STAR-L | The 5-field taxonomy signal schema (Situation, Task, Approach, Result, Landing) |
| AdverTest | Adversarial mutation testing research (arXiv 2602.08146); inspires the adversarial_test node |
| Safety-removal pattern | DAPLab-documented pattern where LLMs "fix" errors by removing safety checks |
| STAR-L Landing | Points to which constraint file section (CLAUDE.md > Known hazards > X) should be updated |

## Appendix B — Dependencies

Pinned versions in `pyproject.toml`:

```toml
[project]
dependencies = [
    # Orchestration
    "langgraph==1.0.*",           # Pinned to 1.0.x; minor releases can change checkpointer schema
    "langgraph-checkpoint-sqlite>=2.0",
    "langgraph-checkpoint-postgres>=2.0; extra == 'webhook'",

    # LLM providers (direct SDKs)
    "anthropic>=0.40",
    "openai>=1.40",
    "google-generativeai>=0.7",
    # xAI via openai-compatible endpoint; no separate SDK needed

    # Embeddings (§12.6.1 vector skill matching)
    "voyageai>=0.3",              # voyage-3-large for skill matching; alternative: openai's text-embedding-3-large

    # Vector search (§12.6.1)
    "faiss-cpu>=1.8",             # CPU-only FAISS for skill registry; <10k skills fits comfortably

    # Data + validation
    "pydantic>=2.8",
    "pyyaml>=6.0",

    # CLI
    "typer>=0.12",
    "rich>=13.7",

    # HTTP
    "httpx>=0.27",

    # Code intelligence
    "tree-sitter>=0.23",
    "tree-sitter-language-pack==1.6.*",  # Supersedes deprecated tree-sitter-languages; pin to 1.6.x
    # pyright installed separately via npm

    # Git
    "pygit2>=1.15",

    # Code Review tools
    "semgrep>=1.85",
    "bandit>=1.7",
    "pip-audit>=2.7",
    # trufflehog installed separately (Go binary)
    "mutmut>=3.2",
    "rapidfuzz>=3.10",            # Fast Levenshtein for slopsquat_check.py typosquat distance (§07.3.5)
    "radon>=6.0",                 # Cyclomatic complexity for debt_server (per `11-ultimate-architecture.md` §19)
    "vulture>=2.13",              # Dead-code detection for debt_server
    # jscpd installed separately via npm (Node.js binary)

    # MCP transport (per `11-ultimate-architecture.md` Part 17)
    "mcp>=1.25,<2",               # Anthropic-published Model Context Protocol SDK; MIT-licensed.
                                  # Pinned to v1.x line per SDK maintainers' guidance: v2 (planned Q1 2026 spec
                                  # release) introduces breaking transport-layer changes. v1.0.0 of autoproduct
                                  # targets v1.25+ which is the stable v1 baseline. Migration to mcp v2 is a
                                  # deliberate v1.2 milestone, NOT a free upgrade.
    "python-frontmatter>=1.1",    # Parse YAML frontmatter from skill markdown for SpecValidator (§18)
    "jsonschema>=4.21",           # Schema validation for voter specs and module specs (§18)
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-httpx>=0.35",
    "pytest-cov>=5.0",
    "ruff>=0.6",
    "pyright>=1.1.380",             # Python pyright wrapper; CLI still needs npm install
]

bench = [
    # Dependencies used only by the benchmark runner
    "datasets>=3.0",                # For loading benchmark instance sets
]

webhook = [
    "fastapi>=0.111",
    "uvicorn>=0.30",
    "celery>=5.4",
    "redis>=5.0",
]

deploy = [
    # Deploy Review stage (§11) — Python SDKs only; binaries listed below
    "kubernetes>=30.1",             # K8s Python client; reads cluster state via kubectl context
    "python-hcl2>=4.3",             # Terraform HCL parsing for migration_dryrun.py shadow execution
    # argocd, flagger interactions go through kubectl + REST (no separate Python SDK needed)
    # railway: REST API only; uses httpx
]

maintenance = [
    # Maintenance stage (§12) — read-only signal source clients
    "sentry-sdk>=2.13",             # Sentry SDK; read methods only
    "datadog>=0.50",                # Datadog Python API client
    "pdpyras>=5.2",                 # PagerDuty REST API session helper
    "prometheus-api-client>=0.5",   # Prometheus query API
    # jaeger / loki use REST via httpx; no separate SDK
]

secrets = [
    # §11.12 credential threat model
    "hvac>=2.3",                    # HashiCorp Vault Python client
    "boto3>=1.35",                  # AWS Secrets Manager (alternative)
]

dashboard = [
    # §11.13 observability dashboards
    "streamlit>=1.38",
    "altair>=5.4",                  # Plotting for Streamlit
]

all = [
    # Convenience extras for full 4-stage install
    "autoproduct[webhook,deploy,maintenance,secrets,dashboard]",
]

[project.scripts]
autoproduct = "autoproduct.cli:app"

[build-system]
requires = ["poetry-core>=1.9"]
build-backend = "poetry.core.masonry.api"
```

**External binaries required for v0.1.0 (Code Review + Test only):**

- **Node.js ≥20** — required for `pyright` and for `npx playwright test` (Gate 2 UI tests). Install via `nvm` on dev machines; deploy image must include it.
- `pyright` (`npm install -g pyright`)
- `trufflehog` (Go binary — `brew install trufflehog` on macOS, or official Go install)
- `ripgrep` / `rg` (for the `grep` tool — `brew install ripgrep` or apt)
- `git >= 2.5` (for `git worktree`; standard on any modern system)

**Additional binaries required for v1.0.0 (Deploy Review + Maintenance):**

- `terraform >= 1.7` (for `terraform validate` + `terraform plan` in §11.3) — only needed if project uses Terraform
- `helm >= 3.14` (for `helm template` + `helm lint`) — only needed if project uses Helm
- `kubectl >= 1.29` (for `kubectl --dry-run=server`) — only needed if project deploys to K8s
- `argocd >= 2.10` CLI (for `argocd app diff`) — only needed if project uses Argo CD
- Project-specific PostgreSQL or MySQL client — for `migration_dryrun.py` shadow DB

**Skip if not deploying to K8s.** AgentHire's Railway deploy path (§11.11) avoids all four K8s-related binaries; it uses Railway's REST API via httpx only.

Optional (only if the target project has a frontend):

- `playwright` — installed via `npx playwright install` inside the target project, not globally. `autoproduct` invokes it via `npx` so it uses the project's pinned version.

**Install footprint by stage:**

| Stage scope | Install command | Binary deps | Approx Python deps install size |
|---|---|---|---|
| Code Review + Test (v0.1.0) | `pip install autoproduct` | Node.js, pyright, trufflehog, ripgrep | ~150 MB |
| + Deploy Review (Railway) | `pip install autoproduct[deploy,secrets]` | (none additional) | ~250 MB |
| + Deploy Review (K8s) | `pip install autoproduct[deploy,secrets]` | + terraform, helm, kubectl, argocd | ~450 MB |
| + Maintenance | `pip install autoproduct[maintenance]` | (none additional) | +50 MB |
| + Dashboard | `pip install autoproduct[dashboard]` | (none additional) | +200 MB |
| Full v1.0.0 (K8s) | `pip install autoproduct[all]` | All of above | ~700 MB |
| Full v1.0.0 (Railway) | `pip install autoproduct[all]` | Node.js + standard | ~500 MB |


## Appendix C — File tree

Complete file structure at v0.1.0:

```
autoproduct/
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
│
├── src/autoproduct/
│   ├── __init__.py
│   ├── cli.py                        # Typer CLI entry
│   │
│   ├── state/
│   │   ├── __init__.py
│   │   ├── review_state.py           # TypedDict
│   │   ├── finding.py                # VoterFinding dataclass
│   │   └── validators.py             # Pydantic mirror
│   │
│   ├── harness/                     # Per `11-ultimate-architecture.md` Part 18
│   │   ├── __init__.py              # Harness top-level class — 7-step startup
│   │   ├── spec_validator.py        # §18, validates voter frontmatter at load
│   │   ├── spec_loader.py           # Loads .mas/specs/**/*.spec.yaml module specs
│   │   ├── fixture_gate.py          # §18.2 — voter cannot register if pass <87.5%
│   │   ├── contract_checker.py      # §18.3 — runtime input/output/spec-alignment validation
│   │   ├── mcp_host.py              # §17.4 — MCP server lifecycle (spawn/shutdown)
│   │   ├── mcp_client.py            # Wrapper over mcp.client.session for voter-side calls
│   │   ├── policy_loader.py         # Compiles deploy/maintenance-policy.yaml at startup
│   │   └── schemas/
│   │       ├── voter_spec.schema.json    # Schema for skill frontmatter
│   │       ├── module_spec.schema.json   # Schema for .mas/specs/*.spec.yaml
│   │       └── policy.schema.json        # Schema for .mas/{deploy,maintenance}-policy.yaml
│   │
│   ├── mcp_servers/                 # Per `11-ultimate-architecture.md` Part 17.2
│   │   ├── __init__.py
│   │   ├── read_only_server.py      # L0: read_file, grep, git_log, git_blame
│   │   ├── code_intel_server.py     # L0: tree_sitter_query, lsp_references, repo_graph_traverse
│   │   ├── sast_server.py           # L0: semgrep, bandit, trufflehog, pip_audit (wraps §07.3.1-2)
│   │   ├── integrity_server.py      # L0: slopsquat_check, csrf_ssrf_probe (wraps §07.3.5-6)
│   │   ├── debt_server.py           # L0: radon, jscpd, vulture (per §19, ultimate arch)
│   │   ├── test_exec_server.py      # L2 (T3 sandbox): run_tests, run_playwright, mutmut. Runs INSIDE Docker
│   │   │                            # container per `11-ultimate-architecture.md` §17.4 (mandatory). Host harness
│   │   │                            # communicates via stdio over docker exec; worktree mounted read-only.
│   │   ├── deploy_server.py         # L1: terraform/helm/kubectl/argocd/flagger/railway/migration_dryrun (read-only)
│   │   └── maintenance_server.py    # L1: sentry/datadog/pagerduty/prometheus/loki/jaeger (read-only)
│   │
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── dispatcher.py            # §5.5 — top-level dispatcher graph
│   │   ├── dispatcher_routes.py     # route_after_code_review, route_after_test, route_after_deploy
│   │   ├── mode_router.py           # §08.3.5.1 — auto-triage to fast/standard/deep based on diff
│   │   ├── code_review_graph.py     # build_code_review_graph() — Code Review subgraph
│   │   ├── test_graph.py            # build_test_graph() — Test subgraph (mutation, UI test gen)
│   │   ├── deploy_graph.py          # §11.4 — Deploy Review subgraph
│   │   ├── maintenance_graph.py     # §12.4 — Maintenance subgraph
│   │   ├── conditionals.py          # Code Review route_after_* (DoR, analyze, vote, verify, leader, test_gate, reverse_merge)
│   │   ├── conditionals_deploy.py   # §11.4.2 routing predicates
│   │   ├── conditionals_maintenance.py  # §12.4 routing predicates (separate retry + confidence loops)
│   │   └── nodes/
│   │       ├── __init__.py
│   │       ├── dor_gate.py           # Gate 1 — Definition of Ready
│   │       ├── init.py
│   │       ├── analyze.py
│   │       ├── tools.py
│   │       ├── vote.py
│   │       ├── peer.py
│   │       ├── verify.py              # §09.4.6 — second-pass verification
│   │       ├── leader.py
│   │       ├── adversarial_test.py   # Uses git worktree for edit isolation
│   │       ├── test_gate.py          # Gate 2 — Test Gate
│   │       ├── reverse_merge.py      # Reverse-merge safety check
│   │       ├── post.py
│   │       ├── hitl.py               # Gate 3 — Review Gate
│   │       │
│   │       │   # Deploy Review subgraph nodes (§11)
│   │       ├── deploy_dor_gate.py    # Gate 5 — Deploy Review Gate entry (§11.10)
│   │       ├── deploy_init.py
│   │       ├── deploy_analyze.py     # Sets state.deploy_classification
│   │       ├── deploy_tools.py       # Invokes terraform/helm/kubectl wrappers
│   │       ├── policy_check.py       # §11.6 Policy-as-Prompt runtime classifiers
│   │       ├── deploy_vote.py        # 4 voters: DeployConfig, CanaryAnalysis, Rollback, Migration
│   │       ├── deploy_verify.py      # Fresh-agent verification of deploy findings
│   │       ├── deploy_leader.py      # 12-verdict synthesis (§11.7)
│   │       ├── deploy_post.py
│   │       ├── deploy_hitl.py
│   │       │
│   │       │   # Maintenance subgraph nodes (§12)
│   │       ├── ingest_signal.py      # Webhook entry; dedupe (§12.4)
│   │       ├── triage.py             # Triage voter
│   │       ├── root_cause.py         # RootCause voter (parallel hypotheses)
│   │       ├── confidence_check.py   # §12.4.1 — confidence-driven re-investigation
│   │       ├── fix_or_action.py      # FixPR voter OR auto-action shim
│   │       ├── maintenance_verify.py
│   │       ├── maintenance_leader.py # 8-verdict synthesis (§12.7)
│   │       ├── post_incident.py
│   │       └── maintenance_hitl.py   # Pages on-call via PagerDuty
│   │
│   ├── policy/                      # §11.6 Policy-as-Prompt machinery
│   │   ├── __init__.py
│   │   ├── trust_tier.py            # Loads .mas/deploy-policy.yaml; resolves per-voter tier per env
│   │   ├── compile.py               # Compiles policies to runtime_classifiers.json
│   │   ├── loader.py                # Validates forbidden_autonomous ceilings at startup
│   │   └── runtime.py               # policy_check_node helper (deterministic + prompt classifiers)
│   │
│   ├── compound/
│   │   ├── __init__.py
│   │   ├── weekly.py                # Compounding loop (cross-stage)
│   │   ├── aggregator.py            # _aggregate_signals (Code Review + Deploy + Maintenance)
│   │   ├── proposer.py              # _propose_claude_md_update
│   │   ├── learned_skill.py         # §12.6 — proposes new entries to .mas/learned_skills/
│   │   └── tier_raise.py            # §11.5.1 — proposes trust-tier raise PRs (4-week metric window)
│   │
│   ├── api/                         # FastAPI webhook receiver
│   │   ├── __init__.py
│   │   └── maintenance_webhook.py   # Sentry/Datadog/PagerDuty webhook handlers
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── voter.py                  # Base Voter class
│   │   └── leader.py                 # Leader agent (separate from voters)
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py                 # Abstract LLMClient
│   │   ├── anthropic_client.py
│   │   ├── openai_client.py
│   │   ├── google_client.py
│   │   ├── xai_client.py
│   │   ├── openrouter_client.py      # Fallback
│   │   ├── factory.py                # get_client_for_model()
│   │   └── embedding_client.py      # §12.6.1 voyage-3-large for skill matching
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py               # ToolRegistry — Code Review tools (L0-L2)
│   │   ├── registry_deploy.py        # Deploy tools (L1-L2; L3+ structurally absent)
│   │   ├── registry_maintenance.py   # Maintenance tools (L1; auto_action_shim is the only L2)
│   │   ├── read_file.py
│   │   ├── grep.py
│   │   ├── git_tools.py              # git_log, git_blame
│   │   ├── git_worktree.py           # create/remove/reverse_merge helpers
│   │   ├── tree_sitter_index.py
│   │   ├── tree_sitter_query.py
│   │   ├── pyright_wrapper.py
│   │   ├── lsp_references.py
│   │   ├── run_tests.py
│   │   ├── playwright_runner.py      # UI test runner (Gate 2 + UI Behavior voter)
│   │   │
│   │   │   # Maintenance signal-source clients (read-only)
│   │   ├── sentry_client.py          # Sentry API — fetch issue, breadcrumbs, similar-issue grouping
│   │   ├── datadog_client.py         # Datadog API — metrics, logs, APM
│   │   ├── pagerduty_client.py       # PagerDuty API — read incident; structurally NO ack/resolve method
│   │   ├── prometheus_client.py      # Prometheus query API (shared with deploy)
│   │   ├── jaeger_client.py          # Distributed-trace fetching
│   │   ├── loki_client.py            # Log query
│   │   ├── kubectl_readonly.py       # `kubectl get events` only — no mutating verbs
│   │   ├── auto_action_shim.py       # §12.5 — only path to L2 production mutation; allowlist-gated
│   │   ├── github_client.py          # PR creation for FixPR voter
│   │   │
│   │   └── deterministic/
│   │       ├── __init__.py
│   │       ├── semgrep.py
│   │       ├── bandit.py
│   │       ├── trufflehog.py
│   │       ├── pip_audit.py
│   │       ├── slopsquat_check.py      # §07.3.5 — registry-presence + age + typosquat-distance + low-usage probe (PyPI/npm)
│   │       ├── csrf_ssrf_probe.py      # §07.3.6 — tree-sitter-based CSRF middleware coverage + SSRF user-URL allowlist check; framework-aware (FastAPI/Django/Flask/Express/Next.js)
│   │       ├── mutmut.py
│   │       │
│   │       │   # Deploy Review deterministic tools (§11.3)
│   │       ├── terraform.py          # terraform validate + plan (no apply)
│   │       ├── helm.py               # helm template + lint
│   │       ├── kubectl.py            # kubectl --dry-run=server (staging only; prod kubeconfig never loaded)
│   │       ├── argocd.py             # argocd app diff (read-only)
│   │       ├── flagger.py            # flagger inspect (read Canary CRD state)
│   │       ├── migration_dryrun.py   # Apply migration to shadow DB; measure runtime + lock risk
│   │       │
│   │       │   # Railway-specific (§11.11 — primary AgentHire deploy target)
│   │       ├── railway.py            # Railway API client (read-only); per-service deploy events
│   │       │
│   │       └── replay.py             # §12.10 — deterministic replay framework for maintenance signals
│   │
│   ├── hooks/                       # §09.7.6 — deterministic enforcement
│   │   ├── __init__.py
│   │   ├── base.py                  # HookInput, HookOutput, HookDecision
│   │   ├── pre_tool_use/
│   │   │   ├── __init__.py
│   │   │   ├── block_secret_paths.py
│   │   │   ├── enforce_worktree_naming.py
│   │   │   └── enforce_credential_scope.py    # §11.12 threat model
│   │   ├── post_voter_run/
│   │   │   ├── __init__.py
│   │   │   └── enforce_voter_envelope.py
│   │   └── post_merge/
│   │       └── README.md            # GitHub Actions workflows live in .github/workflows/
│   │
│   ├── secrets/                     # §11.12 credential threat model
│   │   ├── __init__.py
│   │   ├── vault_client.py          # HashiCorp Vault integration
│   │   ├── aws_secrets_manager.py   # AWS SM integration (alternative)
│   │   ├── env_loader.py            # Fallback for local dev
│   │   └── rotation_check.py        # `autoproduct doctor secret-rotation` cadence audit
│   │
│   ├── github/
│   │   ├── __init__.py
│   │   ├── client.py                 # GitHub API wrappers
│   │   ├── pr_comment.py
│   │   └── hitl_issue.py
│   │
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── yaml_mirror.py
│   │   ├── replay.py                 # autoproduct replay (review level)
│   │   ├── voter_log.py              # Per-voter append-only log
│   │   ├── evidence_ledger.py        # Evidence ledger writer (§09.9.5.1)
│   │   ├── tool_audit.py             # Tool invocation audit log (§09.7.1)
│   │   ├── cost_calculator.py        # Token-usage → USD per model (Code Review + Deploy + Maintenance)
│   │   ├── test_report.py            # Structured test report assembler
│   │   ├── metrics.py                # Prometheus metrics
│   │   ├── dashboard/                # §11.13 — observability dashboards
│   │   │   ├── __init__.py
│   │   │   ├── app.py               # Streamlit entry
│   │   │   ├── views/
│   │   │   │   ├── verdicts.py     # Per-stage verdict distribution
│   │   │   │   ├── voter_cost.py    # Voter cost breakdown
│   │   │   │   ├── escalation.py   # Escalation rate, fix-PR merge rate
│   │   │   │   ├── learned_skills.py  # Registry browser
│   │   │   │   └── on_call.py       # Current incidents, paged-this-week, MTTR trend
│   │   │   └── data.py              # Reads from .mas/ — no live API calls
│   │   └── ab_testing/              # §11.14 — confidence threshold A/B framework
│   │       ├── __init__.py
│   │       ├── tracker.py           # Tracks action_rate vs miss_rate per project, 4-week window
│   │       └── proposer.py          # Proposes threshold adjustment via PR
│   │
│   ├── benchmarks/
│   │   ├── __init__.py
│   │   ├── runner.py
│   │   ├── cr_bench.py
│   │   ├── defects4j_py.py
│   │   └── results_compare.py
│   │
│   └── config/
│       ├── __init__.py
│       ├── project_yaml.py           # Load .mas/project.yaml
│       └── codebase_profile.py       # Load .mas/codebase_profile.yaml
│
├── skills/                           # Voter skill markdown files
│   ├── correctness.md
│   ├── security.md
│   ├── performance.md
│   ├── context.md
│   ├── repo_graph.md
│   ├── style.md
│   ├── leader.md
│   │   # Deploy Review skills (§11.2)
│   ├── deploy_config.md
│   ├── canary_analysis.md
│   ├── rollback.md
│   ├── migration.md
│   │   # Maintenance skills (§12.2)
│   ├── triage.md
│   ├── root_cause.md
│   ├── fix_pr.md
│   └── learned_skill.md
│
├── templates/                       # Project-overridable templates
│   ├── deploy-policy.template.yaml  # §11.6 starter; copied to .mas/ on init
│   ├── maintenance-policy.template.yaml
│   ├── incident_report.md.template
│   ├── postmortem.md.template
│   └── learned_skill.yaml.template
│
├── benchmarks/
│   ├── fixtures/                     # benchmark instance data
│   └── results/                      # Committed per-commit results
│
├── containers/                       # Per `11-ultimate-architecture.md` §17.4 T3 sandbox
│   └── test-exec/
│       ├── Dockerfile                # Minimal Python 3.11 base + pinned pytest/mutmut/playwright
│       ├── server.py                 # FastMCP server entrypoint inside the container
│       └── README.md                 # Build instructions; image digest tracking
│
├── tests/
│   ├── conftest.py
│   ├── fixtures/                    # Shared fixtures (sample diffs, configs)
│   ├── unit/
│   │   ├── test_state.py
│   │   ├── test_conditionals.py
│   │   ├── test_voter.py
│   │   ├── test_tools.py
│   │   ├── test_git_worktree.py
│   │   └── test_rate_limiting.py
│   └── integration/
│       ├── test_end_to_end.py
│       ├── test_hitl_flow.py
│       ├── test_gates.py            # DoR, Test Gate, Rollback
│       └── voters/
│           ├── test_correctness.py
│           ├── test_repo_graph.py
│           ├── test_ui_behavior.py
│           └── fixtures/            # Recorded voter_conversation.yaml per voter
│               ├── correctness/
│               ├── repo_graph/
│               └── ui_behavior/
│
└── design-docs/
    ├── README.md
    ├── 08-foundation.md
    ├── 09-system-design.md
    ├── 10-implementation-plan.md     # This file
    └── archive/
        ├── 01-initial-stage-design.md
        ├── 02-framework-voting-hitl.md
        ├── 03-tool-level-design.md
        ├── 04-unified-design.md
        ├── 05-sop-addendum.md
        ├── 06-sota-review.md
        ├── 07-path-calibration.md
        └── README.md
```

**Per-target-project runtime layout** (created at first run inside the consumer's project, not in autoproduct itself):

```
{target-project}/
├── CLAUDE.md
└── .mas/
    ├── project.yaml                   # §10.3 project config
    ├── codebase_profile.yaml
    ├── deploy-policy.yaml             # §11.6 deploy policy (PR-reviewable)
    ├── maintenance-policy.yaml        # §12.5 auto-action allowlist
    ├── policy/
    │   ├── runtime_classifiers.json   # Auto-generated from deploy-policy.yaml
    │   └── check_log.yaml             # Append-only policy decisions
    ├── reviews/{review_id}/           # One per Code Review run
    │   ├── ...
    │   └── mcp-audit.yaml             # Per `11-ultimate-architecture.md` §17.5 — JSON-RPC-level audit for MCP calls
    ├── specs/                         # Per `11-ultimate-architecture.md` Part 16.3 — module specs
    │   ├── parsers/
    │   │   └── workday.spec.yaml      # Example: AgentHire Workday parser invariants
    │   ├── builders/
    │   │   └── resume.spec.yaml
    │   └── ...                        # One file per critical module
    ├── deploys/                       # One per Deploy Review run
    │   ├── index.yaml
    │   ├── audit.yaml                 # Append-only; every rollback decision
    │   └── {deploy_id}/
    ├── incidents/                     # One per Maintenance run
    │   ├── index.yaml
    │   ├── audit.yaml                 # Append-only; every auto-action decision
    │   ├── rejected.yaml              # Gate 6 rejected signals (audit-only)
    │   └── {incident_id}/
    ├── learned_skills/                # §12.6 registry
    │   ├── README.md                  # Index, last updated
    │   ├── index.yaml
    │   ├── embeddings.faiss           # §12.6.1 vector search index
    │   └── *.yaml                     # One file per skill
    ├── voters/{voter_name}/           # Per-voter append-only logs (all stages)
    │   └── log.yaml
    └── retired_skills/                # 90-day auto-archive (§12.6); tombstones never hard-deleted
        └── *.yaml
```

Line-of-code estimate at v1.0.0 (4-stage MAS): ~9,000 lines of Python (harness + tools + agents + dispatcher + 4 subgraphs + dashboard) + ~7,500 lines of skill markdown (15 skills × ~500 avg) + ~5,500 lines of tests. Totals **~22,000 lines**. The Code Review-only v0.1.0 milestone is ~9,000 lines as before; the deploy + maintenance extension adds ~13,000 lines.

---

## Appendix D — Risk register

Living document. Additions go at the bottom with the date. Mitigations are what's actually planned, not wishful thinking.

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **LLM provider breaking API change** (Anthropic / OpenAI / Google / xAI each ship frequent updates) | Medium (observed 2-3x/year per provider) | High — voters fail | Model IDs pinned in `project.yaml`; CI runs a smoke test hitting each provider weekly; OpenRouter fallback path already in `llm/factory.py` |
| R2 | **Model deprecation mid-build** (e.g., Gemini 3 Pro Preview was shut down March 9, 2026) | Medium | Medium — need to swap model and re-validate benchmark | Subscribe to provider deprecation feeds; every 2 weeks, run `autoproduct check-models` that hits `GET /v1/models` on each provider and flags any pinned ID that's no longer listed |
| R3 | **LangGraph 1.x breaking change in a minor release** | Low-Medium | High — checkpoint format can change | Pin `langgraph==1.0.*` not `>=1.0`; read release notes before bumping; checkpointer migration plan documented in Day-34 dependency review |
| R4 | **Solo-founder time collapse** — 18-month horizon with 3-5 h/week is tight; life disruptions happen | High (historical base rate) | High — project stalls | Change-control protocol above; v0.1.0 scope is intentionally minimum-viable so a partial build is still useful personally; public commitment (GitHub repo + 中文 AI 圈 readers) creates social accountability |
| R5 | **Target-project test suite flakes** cause false Gate-2 blocks | Medium (flaky tests are endemic) | Medium — PR reviews block on unrelated issues | `testing.retry_count: 2` in `project.yaml`; flake detection in test report section (same test fails then passes on retry → logged, not counted as failure); escalate via HITL only on consistent failure |
| R6 | **GitHub Actions free minutes exhaustion** for the rollback-check workflow on a popular public repo | Low (benchmark runs ~5min, triggered only on label-tagged merges) | Low — fallback to manual `make bench-fast` | Monitor Actions minutes in Week 5; move to a self-hosted runner if trends suggest overage |
| R7 | **Claude pricing change** (Anthropic has raised Opus pricing historically) | Medium | Low-Medium — deep mode becomes expensive | Cost model in §09.4.1 tracks expected $/review; if actual exceeds 2× expected, downgrade Correctness+Leader from Opus to Sonnet for a week while re-evaluating |
| R8 | **Benchmark noise** (20-PR subset) triggers spurious rollbacks | Medium | Low — wastes a human review to reject the rollback | Rollback workflow refuses to auto-revert on first post-rollback comparison (§09.8.6); `recall_tolerance_pp` default of 3 is set well above observed noise |
| R9 | **tree-sitter grammar changes** break symbol graph indexing | Low | Medium — Repo Graph voter becomes unreliable | Pin `tree-sitter-language-pack==1.6.*`; parse failures are caught and surfaced as "tool_error" rather than silently dropped |
| R10 | **Secrets leak via YAML mirror** (API tokens accidentally written into state) | Low | High — credential exposure | YAML mirror writer explicitly filters known secret-env-var names before serialization; `.mas/` added to `.gitignore` by default; `autoproduct doctor` scans committed mirrors for patterns matching `sk-ant-*`, `sk-*`, `AIza*`, `xai-*`, `ghp_*`, `ghs_*` |
| R11 | **Worktree accumulation** on long-running webhook mode leaks disk space | Low-Medium | Low | `post_node` always calls `remove_worktree` on success; a cleanup cron job on the webhook runner prunes any worktree older than 7 days as a safety net |
| R12 | **Compound loop proposes harmful CLAUDE.md changes** (reward hacking) | Low-Medium | High — silent drift in voter behavior | §09.8.4.3 reward-hacking mitigations: human approval required, benchmark gate, Stage-2 self-editing out of scope, rollback gate (§09.8.6) |
| R13 | **Prompt injection via PR content** degrades voter quality | Medium (injection attempts will arrive on any public-repo deployment) | Medium — voters may miss findings, but structured output + Leader synthesis limits blast radius | §09.4.2.2 mitigations: `<untrusted_*>` framing in voter prompts, YAML-structured output contracts, safety-removal detection triggers HITL. Residual risk accepted; equivalent to the risk in human review. |
| R14 | **Auto-rollback fires on noise during low-traffic canary** — staging canary with low request count produces statistically meaningless metrics, false rollback confidence | Medium | Medium — wastes a deploy iteration | `NO_AUTOROLLBACK_FOR_LOW_TRAFFIC` policy guardrail (§09.11.6) requires minimum request count before AUTO_ROLLBACK verdict; below threshold, defaults to HOLD_FOR_HUMAN regardless of metric severity |
| R15 | **Maintenance agent paged unnecessarily** — agent fails to dedupe a recurring noisy alert, on-call gets pages it should have absorbed | Medium | Medium — alert fatigue erodes on-call trust | Gate 6 dedupe with 7-day window; LearnedSkill voter detects recurrence after 3 instances and absorbs into runbook; signal source filters configurable per service |
| R16 | **Learned-skill drift** — skill registry accumulates entries that contradict each other or no longer match production behavior after refactor | Low-Medium | Medium — RootCause voter applies stale shortcuts producing wrong hypotheses | Skills auto-archive after 90 days without recurrence; weekly compound loop reviews skill registry for staleness; skill PR review at creation time validates the shortcut against current code |
| R17 | **Trust-tier creep** — stage at `assistive` gradually moves to `autonomous` based on optimistic metrics, but the autonomy crosses an organizational risk threshold | Low | High — autonomous wrong action in production | Architectural ceiling on `forbidden_autonomous` list (§09.11.5, §09.12.5) — production deploys, L4 tools, auth/billing changes can never be set to autonomous; tier raises always go through PR review with metric evidence; compound loop's tier-raise proposals are reviewed monthly |
| R18 | **Cross-stage state corruption** — Code Review state and Deploy Review state share `production_touched` flag; if one stage sets it incorrectly, downstream stages over- or under-react | Low-Medium | Medium — incorrect escalation behavior | Single source of truth for `production_touched` is the `deploy_target` field set by `deploy_init_node`; Code Review only reads, never writes; comprehensive unit tests on the discriminated-union state machine; runtime assertion in `post_node` that flag matches the stage that set it |

Update cadence: review monthly during implementation; re-evaluate after v0.1.0 launch and any time a risk materializes (whether listed or not).

---

*End of 10-implementation-plan.md.*
