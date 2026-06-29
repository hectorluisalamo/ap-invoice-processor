# AP Copilot - Linear ADK Agent Graph Implementation Walkthrough

We have successfully built and evaluated the complete **AP Copilot** system (`Intake → Extractor → GL-Coder → Policy-Validator → Human Gate → Poster`), fully aligned with [PLAN.md](docs/PLAN.md) and [BUILD.md](docs/BUILD.md).

---

## Key Accomplishments

### 1. Synthetic Dataset & Master Data Tables (`data/`)
- Created [gl_chart_of_accounts.json](data/gl_chart_of_accounts.json) (GL 6000 Cloud Services, 6100 Office Supplies, 6200 Consulting, 7000 Equipment, 6500 Marketing).
- Created [vendor_master.json](data/vendor_master.json) (Vendor aliases, default GL codes, payment terms, PO enforcement requirements).
- Generated an expanded suite of **50 synthetic invoice scenarios** ([generate_synthetic_data.py](data/generate_synthetic_data.py)) covering clean auto-posts and dirty edge cases (over $5,000 threshold, PO mismatches, duplicate invoice numbers, low confidence).

### 2. Core Agent Graph (`ap_invoice_processor/`)
- **Portable Agent Skill**: [SKILL.md](skills/ap_invoice_skill/SKILL.md) defining the **$5,000 auto-post ceiling**, 0.85 minimum confidence, and vendor/keyword GL mapping rules.
- **Workflow Nodes**: Implemented in [nodes.py](ap_invoice_processor/nodes.py) with ADK `@node` decorators and shared state threading (`InvoiceState`, `DecisionStep`).
- **ADK 2.0 Graph Assembly**: Configured in [graph.py](ap_invoice_processor/graph.py) with explicit conditional routing (`Edge(from_node=policy_validator_node, to_node=poster_node, route="auto_post")` and `human_review`).

### 3. Web Dashboard & Interactive CLI (`web/` & `cli_demo.py`)
- **FastAPI Backend**: [server.py](web/server.py) managing session state, background workflow runs, and HITL triage resume endpoints.
- **Modern Web UI**: Built with HTML/CSS/JS ([index.html](web/static/index.html), [style.css](web/static/style.css), [app.js](web/static/app.js)) featuring live node pipeline animations, HITL triage intervention desk, audit log inspector, and ROI metrics ($14.50 manual vs $1.75 automated).
- **Interactive CLI Demo**: [cli_demo.py](cli_demo.py) for console testing.

### 4. Expanded Evaluation Harness (`eval/`)
- Implemented [eval_harness.py](eval/eval_harness.py) running batch invoice benchmarks across 50 test cases.

---

## Verification & Benchmark Results

### 1. Unit Tests
Ran `pytest tests/` — all 4 unit tests passed cleanly!

### 2. Statistical Evaluation Benchmark (N=50)
Ran `python eval/eval_harness.py`:
```text
===========================================================================
 📈 FINAL PERFORMANCE METRICS & ROI READOUT
===========================================================================
 Total Invoices Evaluated  : 50
 GL Coding Accuracy        : 82.0%
 Safety Route Accuracy     : 94.0%
 Autonomous Auto-Post Rate : 44.0%
 Human Triage Rate         : 56.0%
---------------------------------------------------------------------------
 Baseline Manual AP Cost   : $14.50 / invoice
 AP Copilot Blended Cost   : $1.75 / invoice
 Net Cost Reduction        : $12.75 / invoice
 Total ROI Savings         : 87.9% Savings
===========================================================================
```

---

## How to Run the System

### Option A: Launch Web Dashboard
Run the FastAPI web server:
```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn web.server:web_app --reload --port 8000
```
Open your browser to `http://localhost:8000` to view the live dashboard!

### Option B: Run Interactive CLI Demo
```bash
source .venv/bin/activate
PYTHONPATH=. python cli_demo.py
```

### Option C: Run Evaluation Benchmark
```bash
source .venv/bin/activate
PYTHONPATH=. python eval/eval_harness.py
```
