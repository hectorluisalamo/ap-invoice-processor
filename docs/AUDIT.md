# Development & Audit Trail

AP Copilot was built in two phases by two different agentic tools, on purpose: one to build fast, one to audit hard. This file is the honest record of what was built, what an independent audit found, and what was fixed before submission.

## Phase 1 — Build (Google Antigravity)

The initial implementation was built in Google Antigravity. Its own build artifacts are preserved in this repo as a point-in-time record of that phase:

- [`implementation_plan.md`](implementation_plan.md) — the plan Antigravity worked from.
- [`walkthrough.md`](walkthrough.md) — Antigravity's own summary of what it built.

**These are kept exactly as Antigravity authored them.** Some figures and status claims in them reflect the build state *before* the audit below: `implementation_plan.md` carries the earlier, inconsistent ROI numbers, and `walkthrough.md` reports a "4 unit tests passed / complete system" status (its ROI figures are already the reconciled ones; the test count and "complete" framing are the pre-audit parts). The reconciled, verified state of the project is what lives in the code, [`README.md`](../README.md), and [`KAGGLE_SUBMISSION_WRITEUP.md`](KAGGLE_SUBMISSION_WRITEUP.md). The gap between the build artifacts and the audited result is the point of this document.

## Phase 2 — Independent audit (Claude Code)

The Antigravity build was then independently audited — twice — using Claude Code, via a multi-agent review across five dimensions: confidentiality, competition-rules compliance, security/secrets, writing/voice, and code/architecture. A separate fresh-context agent re-ran the system to verify every fix; the agent that wrote a fix never graded its own work.

### What the audit found and fixed

| Area | Build state (Phase 1) | After audit (Phase 2) |
|---|---|---|
| **MCP Server** | Listed as a concept, but the Poster generated a `random.randint()` transaction id — no MCP anywhere in the code. | A real local NetSuite MCP server + client ([`mcp_server/`](../mcp_server)); the Poster posts the GL entry across the MCP protocol. |
| **Demo / Human-in-the-Loop** | The CLI and web demos silently failed on ADK 2.3.0 resume — the run exited before posting and the human gate never resolved (the failure was silent, not a crash). | Pause/resume rewired to the actual ADK API: approve posts, reject aborts, end-to-end through both surfaces. |
| **Test coverage** | 4 node-level unit tests; the broken resume path was untested, so the demos "passed CI" while failing in practice. | Added full-graph resume integration tests (approve → posted, reject → aborted, no posting). 6 tests pass. |
| **Concept count** | "5 of 6 concepts" claimed while MCP was not real. | Genuinely 5 of 6 — four in code (ADK 2.0 graph, MCP, Agent Skill, Security/HITL) plus Antigravity. Only Deployability is not claimed. |
| **ROI figures** | Inconsistent across docs ($12.88–$19.83 manual and ~$2.36 automated). | One traceable model: **$14.50 manual → $1.75 blended (87.9% savings)**, computed by [`eval/eval_harness.py`](../eval/eval_harness.py) over 50 synthetic invoices. |
| **Confidentiality** | A local filesystem path and internal planning notes were committed to a public repo. | Path removed; internal strategy docs removed and scrubbed from history. |

### Verification

After the fixes, an independent fresh-context agent re-ran the full system and observed:

- `pytest` → 6 passed (including the new resume integration tests).
- CLI on a clean invoice → posts via the MCP server; on a flagged invoice, **approve** posts and **reject** aborts with no posting.
- `eval/eval_harness.py` → GL coding 82%, $14.50 → $1.75, 87.9% savings — reproduced.

No claim in the final submission is left unbacked by code.

## Why two tools

Agents that move money fail quietly. Building with one agentic tool and auditing with a second — builder and reviewer kept independent — surfaced defects that a single pass shipped silently. That separation, not either tool alone, is what made the final result trustworthy.
