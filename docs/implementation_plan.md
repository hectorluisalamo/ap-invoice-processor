# Implementation Plan - Autonomous AP Invoice Processing ADK Graph ("AP Copilot")

Build an end-to-end linear ADK 2.0 Agent Workflow for Autonomous Accounts Payable (AP) Invoice Processing (`Intake → Extractor → GL-Coder → Policy-Validator → Human Gate → Poster`), aligned with [PLAN.md](docs/PLAN.md) and [BUILD.md](docs/BUILD.md).

> **Note on Alignment:** The implementation plan perfectly mirrors the 6-node graph, 5 named concepts (ADK, MCP, SKILL.md, Security/HITL, Antigravity), and the ROI story. As specified in `BUILD.md` ("FIRST MOVE"), we prioritize generating the synthetic dataset and master tables before building downstream agent graph nodes.

## User Review Required

> [!IMPORTANT]
> **Phase 1 Priority:** Per `BUILD.md`, we will begin immediately by generating the synthetic data tables (`data/`):
> 1. `gl_chart_of_accounts.json` — Standard enterprise GL accounts (6000 Cloud Services, 6100 Office Supplies, 6200 Consulting, 7000 Equipment).
> 2. `vendor_master.json` — Approved vendors with default payment terms and default GL accounts.
> 3. `synthetic_invoices/` — Clean invoices + dirty edge cases (over $5,000 threshold, PO mismatches, duplicate invoice numbers, low confidence).
>
> **ROI Story Alignment:** The dashboard and evaluation harness will measure cost savings based on the pitch formula: Manual AP ($12.88–$19.83/invoice) vs. Agent Automated (~$2.36/invoice).

## Open Questions

None.

---

## Proposed Changes

### Phase 1: Synthetic Dataset & Master Tables (`data/`)

#### [NEW] [gl_chart_of_accounts.json](data/gl_chart_of_accounts.json)
- Chart of GL accounts with account numbers, names, and department codes.

#### [NEW] [vendor_master.json](data/vendor_master.json)
- Vendor database with vendor IDs, names, matching aliases, and standard payment terms.

#### [NEW] [generate_synthetic_data.py](data/generate_synthetic_data.py) & [invoices.json](data/synthetic_invoices/invoices.json)
- Script generating synthetic invoice payloads: clean PO matches under threshold, high-dollar over threshold ($5,000 ceiling), PO mismatch, duplicate invoice number, unknown vendor.

---

### Phase 2: Core Agent & Data Models (`ap_invoice_processor/`)

#### [NEW] [models.py](ap_invoice_processor/models.py)
- Define Pydantic models for structured invoice processing and shared state threading through nodes:
  - `LineItem`, `FieldConfidence`, `DecisionStep`, `ValidationFlags`, `InvoiceState`.

#### [NEW] [skill_loader.py](ap_invoice_processor/skill_loader.py)
#### [NEW] [SKILL.md](skills/ap_invoice_skill/SKILL.md)
- Portable Agent Skill definitions containing vendor GL mapping tables, keyword fallback rules, department codes, and policy thresholds ($5,000 auto-post ceiling).

#### [NEW] [nodes.py](ap_invoice_processor/nodes.py)
- Implementation of the six workflow nodes (`intake_node`, `extractor_node`, `gl_coder_node`, `policy_validator_node`, `human_gate_node`, `poster_node`).

#### [NEW] [graph.py](ap_invoice_processor/graph.py)
- Assembles the ADK 2.0 `Workflow` graph with conditional routes (`auto_post` vs `human_review`).

---

### Phase 3: Web Dashboard & CLI (`web/` & `cli_demo.py`)

#### [NEW] [server.py](web/server.py)
- FastAPI app managing sessions, workflow executions, invoice drops, and HITL resume endpoints (`/api/invoices/{id}/approve` and `/api/invoices/{id}/reject`).

#### [NEW] [index.html](web/static/index.html) & [app.js](web/static/app.js) & [style.css](web/static/style.css)
- Sleek modern dashboard showing live node execution graph, HITL triage desk, audit trail inspector, and ROI metrics header ($12.88/invoice vs $2.36/invoice).

#### [NEW] [cli_demo.py](cli_demo.py)
- Interactive CLI runner.

---

### Phase 4: Evaluation Harness (`eval/`)

#### [NEW] [eval_harness.py](eval/eval_harness.py)
- Evaluator running batch invoices through the runner, checking accuracy and ROI metrics.

---

## Verification Plan

### Automated Tests
- Run `python data/generate_synthetic_data.py` to generate master data and verify test invoices.
- Run `pytest` suite testing node functions.
- Run `python eval/eval_harness.py` for batch accuracy and ROI output.

### Manual Verification
- Launch web dashboard via `python web/server.py` and run end-to-end invoice drop and HITL review testing.
