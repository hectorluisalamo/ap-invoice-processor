<!-- Build-execution layout for the Kaggle "AP Copilot" capstone — agentic workflow and features. -->

# AP Copilot — BUILD Layout

_Companion to `PLAN.md` (architecture, rules, and scoring). This file is the build execution reference for the agentic workflow and feature specifications._

---

## ⏰ Timeline reality

- **Deadline: July 6, 11:59 PM PT — ~7.5 days from 2026-06-29.**
- The original 13-day plan had the agent graph built by today. The last 2 days are locked for **writeup + 5-min video + README = 40 of 100 pts**, non-negotiable.
- **Real build window: ~5 days.** Scope stays throwaway-grade, certificate-grade. Do not gold-plate.

---

## THE AGENTIC WORKFLOW — what you're building

A linear ADK agent graph: **one invoice in → one posted GL entry out**, with a human gate on anything risky.

```
Intake → Extractor → GL-Coder → Policy-Validator → 🧑 Human Gate → Poster
```

| Node | Job | In → Out |
|------|-----|----------|
| **Intake** | Pull an invoice (email/Drive MCP or watched folder), normalize into the shared state object. | raw invoice → normalized state |
| **Extractor** | Pull vendor, amount, date, line items, PO# into structured fields. The Gemini-vision/parse step. | invoice doc → structured fields + per-field confidence |
| **GL-Coder** | Map line items to the right GL account using the `SKILL.md` rules (the "agent skill" concept box). | line items → GL-coded entries |
| **Policy-Validator** | Duplicate check, PO match, approval thresholds, "no auto-post above $X." | coded entry → pass / flag(s) |
| **🧑 Human Gate** | Anything failing validation or tripping a threshold routes to human approve/reject. The **Security** box — money on the line. | flagged entry → approved / rejected |
| **Poster** | Write the approved entry to NetSuite via **MCP** (real sandbox if one exists, lightweight mock if not). | approved entry → posted GL entry |

**Shared state** threads through every node: invoice fields + per-field confidence + validation flags + the running **decision trail**. That trail is also what the eval scores and what the demo visualizes.

---

## FEATURES (the demoable surface)

- End-to-end autonomous run: drop an invoice, watch it flow to a posted entry.
- **Human-in-the-loop triage**: risky invoices pause and wait for an approve/reject decision.
- **Hard safety rail**: no auto-post above a configurable $ ceiling — always routes to human.
- **Portable agent skill** (`SKILL.md`): GL-mapping rules, vendor matching, approval thresholds as one reusable unit.
- **Decision trail / audit log**: every node's call + confidence + outcome, viewable per invoice.
- **Eval harness + ROI readout**: accuracy + auto-post rate → the cost-per-invoice number.

---

## CONCEPTS TICKED (need 3 of 6 named; we map 5)

- **ADK / multi-agent** ✅ — the graph above.
- **MCP server** ✅ — NetSuite MCP (ERP read/write) + email/Drive MCP for intake.
- **Agent skill / SKILL.md** ✅ — GL rules, vendor matching, thresholds as one portable skill.
- **Security** ✅ — human gate, no-auto-post ceiling, sandboxed execution, scrubbed secrets, slopsquat-safe deps. **Strongest Agents-for-Business selling point.**
- **Antigravity** ✅ — build it there (see below); the build itself ticks the box.
- _(Deployability ⬜ — optional 6th; deploy NOT required. A documented cheap deploy path scores a little. Skip unless trivially free.)_

---

## EVAL + ROI (not a named concept, but it's the pitch)

Run the agent over the synthetic invoice set, score:
- **GL-coding accuracy** (correct account vs. ground truth),
- **% auto-posted vs. routed to human** (and false-route / false-post rates).

Convert to the money line baked into the demo:

> **Manual AP = $12.88–$19.83/invoice → agent-automated ≈ $2.36/invoice.**

This number powers the Kaggle pitch narrative.

---

## AGENT ORCHESTRATION WITH ANTIGRAVITY

Antigravity provides agentic development orchestration across IDE, CLI, and visual agent management.

**Key orchestration workflows:**
1. **Plan-artifact-first:** Lock implementation plan artifacts before execution.
2. **Sequential node development:** Build and verify nodes sequentially (`Intake → Extractor → GL-Coder → Policy-Validator → Human Gate → Poster`).
3. **Artifact walkthroughs:** Generate visual walkthroughs and recorded execution flows for submission video assets.

---

## FIRST MOVE

**Lock the synthetic dataset before touching the graph** — everything downstream depends on it:
- Synthetic invoices (clean set),
- GL chart of accounts,
- Vendor master,
- A handful of **deliberately-dirty edge cases** for the human gate to catch: duplicates, over-threshold amounts, PO mismatches, unknown vendors.

Then build the graph node-by-node in Antigravity, plan-artifact-first, verifying each node against the synthetic data before moving on.

---

## DELIVERABLES CHECKLIST (from PLAN.md — all required for a valid submission)

- [ ] Kaggle Writeup ≤ 2,500 words, **track = Agents for Business**, hit **Submit** (drafts aren't judged).
- [ ] Cover image + Media Gallery.
- [ ] YouTube video ≤ 5 min, published (problem → why-agents → architecture → demo → the build).
- [ ] Public GitHub repo + README (problem, solution, architecture, setup, diagrams — worth **20 pts**).
- [ ] ≥3 of 6 named concepts demonstrated (we map 5).
- [ ] **No API keys / secrets in the repo** — it goes public; scrub before submit.
- [ ] Final finance logic pass on GL rules + approval thresholds before Jul 5.
