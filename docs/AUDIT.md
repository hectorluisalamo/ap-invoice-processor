# Development & Audit Trail

AP Copilot was built and hardened across **three rounds** by two different agentic tools — built fast with one, audited hard with another. This file is the honest record of what happened in each round, with the original build artifacts preserved so the trail is verifiable rather than just asserted.

## Round 1 — Initial build (Google Antigravity)

The first implementation was built in Google Antigravity as a proof of concept. Its own artifacts are preserved, unedited, in [`round1_initial_build/`](round1_initial_build):

- [`implementation_plan_v1.md`](round1_initial_build/implementation_plan_v1.md) — the plan Antigravity worked from.
- [`walkthrough_v1.md`](round1_initial_build/walkthrough_v1.md) — Antigravity's summary of the POC build.

## Round 2 — Remediation attempt (Google Antigravity)

After a first review flagged problems, Antigravity attempted fixes and reported them complete. Its artifacts are preserved, unedited, in [`round2_remediation/`](round2_remediation):

- [`implementation_plan_v2.md`](round2_remediation/implementation_plan_v2.md)
- [`walkthrough_v2.md`](round2_remediation/walkthrough_v2.md)

**Two of round 2's reported fixes did not actually hold** — and the artifacts are kept as-authored precisely so that's on the record:

- `walkthrough_v2.md` states the demo was fixed by switching to `state_delta=...`. It wasn't: that approach re-runs the graph from the start, so the human reviewer's decision never reaches the Poster — the CLI and web demos exited before posting. The failure was *silent* (no exception), which is exactly why it slipped through.
- The MCP Server "concept" was still a `random.randint()` stub — no MCP server or client existed in round 2.

## Round 3 — Independent audit & real remediation (Claude Code)

A second, deeper audit — a multi-agent review (confidentiality, rules-compliance, security, writing, code/architecture) with a separate fresh-context agent re-running the system to verify every fix — caught that round 2 was still broken, and did the real remediation that ships in this repo.

### What round 3 found and fixed

| Area | After rounds 1–2 (Antigravity) | After round 3 (audit) |
|---|---|---|
| **MCP Server** | A `random.randint()` stub; no MCP code, despite being claimed as a concept. | A real local NetSuite MCP server + client ([`mcp_server/`](../mcp_server)); the Poster posts the GL entry across the MCP protocol. |
| **Demo / Human-in-the-Loop** | `state_delta`-based resume left both demos silently broken — the human decision never reached the Poster. | Resume rewired to the actual ADK 2.3.0 API (a `FunctionResponse` resume message): approve posts, reject aborts, end-to-end. |
| **Test coverage** | 4 node-level unit tests; the broken resume path was untested, so it "passed CI" while failing in practice. | Added full-graph resume integration tests (approve → posted, reject → aborted). 6 tests pass. |
| **Concept count** | "5 of 6" claimed while MCP wasn't real. | Genuinely 5 of 6 — four in code (ADK 2.0 graph, MCP, Agent Skill, Security/HITL) plus Antigravity. Only Deployability is not claimed. |
| **ROI figures** | Inconsistent across docs ($12.88–$19.83 manual and ~$2.36 automated). | One traceable model: **$14.50 manual → $1.75 blended (87.9% savings)**, computed by [`eval/eval_harness.py`](../eval/eval_harness.py) over 50 synthetic invoices. |
| **Confidentiality** | A local filesystem path and internal planning notes were committed to a public repo. | Path removed; internal strategy docs removed and scrubbed from history. |

### Verification

After round 3, an independent fresh-context agent re-ran the full system and observed:

- `pytest` → 6 passed (including the new resume integration tests).
- CLI on a clean invoice → posts via the MCP server; on a flagged invoice, **approve** posts and **reject** aborts with no posting.
- `eval/eval_harness.py` → GL coding 82%, $14.50 → $1.75, 87.9% savings — reproduced.

No claim in the final submission is left unbacked by code.

## Why this trail exists

Agents that move money fail quietly. Round 2 is the proof: an agentic tool reported a fix complete, twice, while the code stayed broken. Building with one tool and auditing with a second — builder and reviewer kept independent — caught what a single pass shipped silently. That separation, not either tool alone, is what made the final result trustworthy.
