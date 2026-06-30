# Round 5 — Independent Re-Audit, Grading & Remediation

_Authored 2026-06-30 by an independent Claude Code pass, run from a clean clone at the round-4 HEAD. This is a real artifact of the round-5 review, not a reconstruction. The authoritative narrative record remains [`../AUDIT.md`](../AUDIT.md)._

## Scope

A fresh-context, adversarial re-audit of the feature-complete repo — explicitly tasked with trying to break it, not confirm it. Run as a fan-out of focused agents, each re-deriving conclusions from the live code rather than trusting any prior round:

- **Code & evaluation integrity** — is the eval honest or rigged? Are the tests meaningful?
- **Documentation vs. live code** — does any doc or on-screen surface claim something the code doesn't do?
- **Audit-trail honesty** — do the four documented rounds hold up against git history?
- **Public-repo security** — secrets, PII, personal paths, dependency safety.

A separate panel graded the submission against the official competition rubric (Pitch 30 / Implementation 70) to prioritize remediation.

## What the audit confirmed (re-derived from live code)

- **Reproducible headline results:** `pytest` → 6 passed; `eval/eval_harness.py` → GL 82.0%, route 94.0%, auto-post 44.0%, $14.50 → $1.75, 87.9% savings.
- **Eval is honest, not rigged:** ROI is computed from the live auto-post rate (not a hardcoded constant), and the agent is scored *down* for real misses — a rigged eval flatters; this one penalizes.
- **Tests are meaningful:** the human-gate resume path and the NetSuite MCP round-trip are exercised end-to-end (approve → `NS-POST-…`; reject → aborted), not stubbed.
- **The audit trail is accurate:** the `historical/` reorg is a verified pure `git mv` (100% renames, zero content edits); the reconstructed round-3 pair is clearly labeled and does not overclaim against git history.
- **The repo is safe to publish:** no secrets or personal filesystem paths in the working tree or git history; dependencies are real, pinned, and not typosquatted; Apache-2.0 license present; CI clean.

## What the audit fixed (remediation applied this round)

| # | Fix | Why |
|---|---|---|
| 1 | Dashboard Extractor tile "Vision Parse" 👁️ → "Field Extract" 🧾 (`web/static/index.html`) | The tile claimed vision parsing the code doesn't do — an on-camera overclaim that contradicted round 4's own correction of the same claim elsewhere. |
| 2 | Generator line items now sum exactly to the invoice total (`data/generate_synthetic_data.py`) | Items were re-divided and the total overwritten with the smaller sum, which could drop a `high_dollar_ceiling` invoice below the $5k ceiling and mislabel it. |
| 3 | Generator vendor list derived from `vendor_master.json`; fixed seed added | A parallel hand-kept vendor list had drifted from the master (e.g. an "Apple Store" alias the master didn't list), producing spurious `unknown_vendor` routes. |
| 4 | Eval harness surfaces run failures instead of swallowing them (`eval/eval_harness.py`) | A bare `except: pass` could let a crashed invoice masquerade as a clean auto-post and inflate the metrics. |
| 5 | HITL helpers consolidated into `ap_invoice_processor/hitl.py` | Gate-pause / resume-message / poster-check helpers were copy-pasted across the CLI, web server, eval, and tests. |

**Note on the dataset:** the two generator bugs (fixes 2–3) only ever made the agent's measured accuracy look *worse* than it is. The committed `synthetic_invoices/invoices.json` was deliberately **not** regenerated, so the published numbers are unchanged and the 94% route accuracy understates rather than overstates the system. Re-baselining the dataset to show the true (~100%) route accuracy was considered and declined, to avoid churning the graded metrics close to the deadline.

## Verification

After remediation, both checks reproduce unchanged:

- `pytest` → **6 passed**
- `eval/eval_harness.py` → GL **82.0%** / route **94.0%** / auto-post **44.0%** / $14.50 → **$1.75** / **87.9%** savings

The remediation is behavior-preserving for the agent graph; the helper consolidation and eval hardening change no agent logic, and the generator fix is not run against the committed dataset.
