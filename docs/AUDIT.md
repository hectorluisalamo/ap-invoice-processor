# Development & Audit Trail

AP Copilot was built and hardened across **four rounds** by two agentic tools — built fast with Google Antigravity, audited hard with Claude Code, then expanded again. This file is the honest record of what happened in each round, with the build artifacts preserved so the trail is verifiable rather than just asserted.

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
- The MCP Server "concept" wasn't real — the Poster fabricated its transaction ID inline via `random.randint()`, with no MCP server or client anywhere in round 2.

## Round 3 — Independent audit & real remediation (Claude Code)

A second Claude Code audit — the first had produced the blocker list that round 2 tried to address — went deeper: a multi-agent review (confidentiality, rules-compliance, security, writing, code/architecture) with a separate fresh-context agent re-running the system to verify every fix. It caught that round 2 was still broken, and did the real remediation that ships in this repo.

Round 3 was an audit rather than a tool-authored build, so it produced no live plan/walkthrough of its own. To keep the per-round folder convention complete, a reconstructed pair — assembled from this file and the git history, and labeled as reconstructed — is preserved in [`round3_remediation/`](round3_remediation):

- [`implementation_plan_v3.md`](round3_remediation/implementation_plan_v3.md)
- [`walkthrough_v3.md`](round3_remediation/walkthrough_v3.md)

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

## Round 4 — Feature expansion (Google Antigravity)

After the audit, the project went back to Antigravity for a feature round focused on the demo surface. Its artifacts are preserved in [`round4_feature_expansion/`](round4_feature_expansion) — as-authored, except that absolute local filesystem paths were scrubbed to repo-relative links (the same confidentiality fix round 3 applied):

- [`implementation_plan_v4.md`](round4_feature_expansion/implementation_plan_v4.md)
- [`walkthrough_v4.md`](round4_feature_expansion/walkthrough_v4.md)
- [`task_v4.md`](round4_feature_expansion/task_v4.md)

What this round shipped:

- **"Test Your Own Invoice" flow** — a custom-invoice form (`POST /api/run-custom`) that runs an arbitrary vendor/amount/PO/line-item through the same agent graph, so the policy rails (ceiling, unknown vendor, bad PO) can be exercised live, not just on the bundled scenarios.
- **Branched, animated workflow graph** — the dashboard graph was rebuilt from a flat row into a true fork (auto-post bypass vs. Human Gate path), with nodes lighting up in sequence as each fires, so a viewer can watch the actual path an invoice takes.
- **Rejection-lockout fix** — after a Human Gate rejection the UI had blocked selecting another invoice; polling/state are now released on every terminal state (`completed`, `aborted`, `error`).
Folding this round into the trail also included a documentation-accuracy pass (Claude Code), separate from the Antigravity feature commits above:

- **Dashboard ROI readout corrected** — round 3 standardized the ROI figure across the docs and eval ($14.50 → $1.75, 87.9%), but the live dashboard card had retained the older numbers ($2.36 / 83.7%); the card was brought in line with the single traceable model.
- **Doc-accuracy fixes** — corrected stale claims a fresh review surfaced: the graph described as "linear" (it branches at the Policy-Validator), an Extractor described as live vision/LLM parsing (it reads pre-structured synthetic fields), the undocumented custom-invoice flow, and the undocumented unknown-vendor rail. The removed claim that a Gemini API key is required was also part of this pass — the demo is keyless.

Verification: the eval harness and unit/integration suite continue to pass unchanged (the feature changes are front-end plus one additive endpoint; the documentation pass touched no agent logic), and the three smoke scenarios — clean auto-post, gated-approve, gated-reject — were re-run end to end on both the CLI and the web surfaces.

## Why this trail exists

Agents that move money fail quietly. Round 2 is the proof: an agentic tool reported a fix complete, twice, while the code stayed broken. Building with one tool and auditing with a second — builder and reviewer kept independent — caught what a single pass shipped silently. That separation, not either tool alone, is what made the final result trustworthy.
