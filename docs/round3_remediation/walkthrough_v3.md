> **Reconstructed artifact.** Unlike the Antigravity-authored artifacts in rounds 1, 2, and 4 (preserved as-authored), this round-3 pair was reconstructed on 2026-06-30 from [`docs/AUDIT.md`](../AUDIT.md) and the git history, to complete the per-round folder convention. The authoritative narrative record for round 3 remains `AUDIT.md`.

# Walkthrough v3 — Audit Remediation Results & Independent Verification

This walkthrough records what round 3 actually shipped and how an independent fresh-context agent verified it. It is the counterpart to [`implementation_plan_v3.md`](implementation_plan_v3.md).

## What shipped

| Area | After rounds 1–2 (Antigravity) | After round 3 (audit) |
|---|---|---|
| **MCP Server** | A `random.randint()` stub; no MCP code, despite being claimed as a concept. | A real local NetSuite MCP server + client (`mcp_server/`); the Poster posts the GL entry across the MCP protocol. |
| **Demo / Human-in-the-Loop** | `state_delta`-based resume left both demos silently broken — the human decision never reached the Poster. | Resume rewired to the actual ADK 2.3.0 API (a `FunctionResponse` resume message): approve posts, reject aborts, end to end. |
| **Test coverage** | 4 node-level unit tests; the broken resume path was untested. | Added full-graph resume integration tests (approve → posted, reject → aborted). 6 tests pass. |
| **ROI figures** | Inconsistent across docs. | One traceable model: **$14.50 manual → $1.75 blended (87.9% savings)**, computed by `eval/eval_harness.py` over 50 synthetic invoices. |
| **Confidentiality** | A local filesystem path and internal planning notes were committed to a public repo. | Path removed; internal strategy docs removed and scrubbed from history. |

## Independent verification

After the remediation, a separate fresh-context agent re-ran the full system and observed:

- `pytest` → **6 passed**, including the new full-graph resume integration tests.
- **CLI** on a clean invoice → posts via the MCP server; on a flagged invoice, **approve** posts and **reject** aborts with no posting.
- `eval/eval_harness.py` → GL coding **82%**, **$14.50 → $1.75**, **87.9% savings** — reproduced.

The builder did not grade its own work: the verification came from an independent agent re-deriving the results, which is the control that caught round 2's silent failures in the first place.

## Outcome

No claim in the submission is left unbacked by code. The full round-by-round narrative — including why building with one tool and auditing with a second is what made the result trustworthy — is in [`../AUDIT.md`](../AUDIT.md).
