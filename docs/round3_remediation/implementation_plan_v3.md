> **Reconstructed artifact.** Unlike the Antigravity-authored artifacts in rounds 1, 2, and 4 (preserved as-authored), this round-3 pair was reconstructed on 2026-06-30 from [`docs/AUDIT.md`](../AUDIT.md) and the git history, to complete the per-round folder convention. The authoritative narrative record for round 3 remains `AUDIT.md`.

# Implementation Plan v3 — Independent Audit & Real Remediation (Claude Code)

Round 3 was not a feature round. It was an independent audit — built with one tool (Google Antigravity), audited with a second (Claude Code) — that re-ran the system end to end, found that round 2's reported fixes had not held, and did the real remediation that ships in this repo.

## The problem this round addressed

A first Claude Code review had produced a blocker list; round 2 (Antigravity) reported those blockers fixed. A second, deeper audit re-ran the system and found two of round 2's "fixes" were silently broken and one claimed concept did not exist in code. The plan below is what that audit set out to verify and repair.

## Planned remediation

### 1. MCP Server — make the concept real
- **Found:** the Poster fabricated its transaction ID inline via `random.randint()`. No MCP server or client existed anywhere, despite "MCP Server" being claimed as a competition concept.
- **Plan:** build an actual local NetSuite MCP server + a matching client (`mcp_server/`); rewire the Poster to post the GL entry across the MCP protocol and return the real transaction ID.

### 2. Demo / Human-in-the-Loop — fix the silently broken resume
- **Found:** the `state_delta`-based resume re-ran the graph from the start, so the human reviewer's decision never reached the Poster. Both CLI and web demos exited before posting — with no exception, which is why it slipped through.
- **Plan:** rewire resume to the actual ADK 2.3.0 API (a `FunctionResponse` resume message) so an approval posts and a rejection aborts, end to end.

### 3. Test coverage — cover the path that broke
- **Found:** 4 node-level unit tests; the broken resume path had no test, so it "passed CI" while failing in practice.
- **Plan:** add full-graph resume integration tests (approve → posted, reject → aborted) so the regression cannot recur silently.

### 4. ROI figures — one traceable model
- **Found:** inconsistent ROI numbers across docs.
- **Plan:** standardize on a single model computed by `eval/eval_harness.py` over 50 synthetic invoices ($14.50 manual → $1.75 blended, 87.9% savings), and make every doc cite it.

### 5. Confidentiality — scrub the repo
- **Found:** a local filesystem path and internal planning notes had been committed to a public repo.
- **Plan:** remove the path, remove the internal strategy docs, and scrub them from history.

## Verification approach (definition of done)

Round 3's gate was an independent, fresh-context agent re-running the full system — not the builder grading itself. Done means observable: `pytest` green including the new resume tests; the CLI posting on a clean invoice and approving/aborting correctly on a flagged one; and `eval/eval_harness.py` reproducing the stated metrics. No claim left unbacked by code. See [`walkthrough_v3.md`](walkthrough_v3.md) for the results.
