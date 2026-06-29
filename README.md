# 🚀 AP Copilot — Autonomous Accounts Payable Agent

**Kaggle Capstone Submission: 5-Day AI Agents Intensive Vibe Coding Course With Google**  
*Track: Agents for Business | Framework: Google ADK 2.0 & Antigravity*

---

## 💡 Executive Summary & ROI Value Proposition

Manual Accounts Payable (AP) processing is an enterprise bottleneck costing organizations **$14.50+ per invoice** in labor, slow processing cycles, and risk of duplicate payments. 

**AP Copilot** is an autonomous accounts-payable agent built on **Google Agent Development Kit (ADK 2.0)** that automates invoice extraction, GL account coding, and NetSuite ERP posting—with a **hard Human-in-the-Loop safety gate** on high-dollar or risky invoices.

### 📈 Benchmark Performance & ROI Highlights (N=50 Synthetic Invoices)
* **Autonomous Auto-Post Rate:** **44.0%** of routine invoices posted instantly with zero human intervention.
* **Safety Routing Accuracy:** **94.0%** accurate routing of risky invoices (over $5,000 threshold, PO mismatches, duplicates, low OCR confidence).
* **Blended Cost per Invoice:** Reduced from **$14.50** (manual baseline) to **$1.75** (blended compute + triage cost).
* **Net Cost Reduction:** **87.9% Total Cost Savings**.

---

## 🏗️ System Architecture

AP Copilot is structured as a linear 6-node ADK 2.0 `Workflow` graph threading shared state (`InvoiceState`) and decision audit logs across every execution step:

```
┌──────────┐     ┌───────────┐     ┌──────────┐     ┌──────────────────┐
│  Intake  │ ──> │ Extractor │ ──> │ GL-Coder │ ──> │ Policy-Validator │
└──────────┘     └───────────┘     └──────────┘     └──────────────────┘
                                                             │
                                      ┌──────────────────────┴──────────────────────┐
                                      ▼ (auto_post)                                 ▼ (human_review)
                                ┌──────────┐                                ┌────────────┐
                                │  Poster  │ <───────────────────────────── │ Human Gate │ (Approved)
                                └──────────┘                                └────────────┘
                                (NetSuite ERP)                               (Safety Rail)
```

### 🧩 Node Breakdown

| Node | Responsibilities | Shared State Transition |
|---|---|---|
| **Intake** | Ingests raw invoice payloads (JSON/text/scans) and initializes normalized shared state. | `raw invoice` → `normalized state` |
| **Extractor** | Structured vision/LLM parsing of vendor, total amount, date, line items, PO#, and per-field confidence. | `invoice doc` → `structured fields + confidence` |
| **GL-Coder** | Maps line items to GL accounts and department codes using rules loaded from portable `SKILL.md`. | `line items` → `GL-coded entries` |
| **Policy-Validator** | Evaluates compliance: duplicate checks, PO database verification, low confidence (<0.85), and **$5,000 auto-post ceiling**. | `coded entry` → `auto_post` vs `human_review` |
| **Human Gate** | Intercepts flagged entries via ADK `RequestInput` for interactive human triage (Approve/Reject). | `flagged entry` → `approved / rejected` |
| **Poster** | Writes approved entries to NetSuite sandbox API via MCP and records transaction ID (`NS-POST-XXXXX`). | `approved entry` → `posted GL entry` |

---

## 🎯 Competition Concepts Demonstrated (3 Core Named Concepts)

1. **ADK 2.0 Workflow Multi-Agent Graph:** Built natively using `google.adk.workflow.Workflow`, `@node` decorators, and explicit conditional routing (`Edge(from_node=..., to_node=..., route=...)`).
2. **Agent Skills (`SKILL.md`):** Portable skill definition in `skills/ap_invoice_skill/SKILL.md` encapsulating GL mapping tables, keyword fallbacks, and policy thresholds loaded dynamically at runtime.
3. **Security & Human-in-the-Loop Safety Rails:** Hard **$5,000 auto-post dollar ceiling**, duplicate invoice prevention, and interactive `RequestInput` human gate.
*(Note: Google Antigravity framework orchestration is also demonstrated in the video walkthrough).*

---

## 🛠️ Installation & Setup

### Prerequisites
* Python **3.11+**
* Virtual Environment manager (`uv` or standard `venv`)

### Setup Commands
```bash
# Clone the repository
git clone https://github.com/hectorluisalamo/ap-invoice-processor.git
cd ap-invoice-processor

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt

# Export Gemini API Key (optional / for LLM vision parsing)
export GEMINI_API_KEY="your_gemini_api_key_here"
```

---

## 🚀 How to Run the Demo & Evaluation

### 1. Launch the Live Web Dashboard UI
Experience the interactive visual dashboard featuring real-time node pipeline state animations, human-in-the-loop triage intervention desk, and audit logs:
```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn web.server:web_app --reload --port 8000
```
👉 Open your browser to **`http://localhost:8000`**

### 2. Run the Interactive CLI Demo
Run sample invoice scenarios directly in your console:
```bash
source .venv/bin/activate
PYTHONPATH=. python cli_demo.py
```

### 3. Run the Automated Evaluation Benchmark (N=50)
Execute the batch evaluation harness across 50 synthetic invoices to verify accuracy and generate the statistical ROI readout:
```bash
source .venv/bin/activate
PYTHONPATH=. python eval/eval_harness.py
```

### 4. Run Unit Tests
```bash
source .venv/bin/activate
PYTHONPATH=. pytest tests/
```

---

## 📂 Repository Structure

```text
ap-invoice-processer/
├── ap_invoice_processor/    # Core ADK agent graph & node implementations
│   ├── graph.py             # ADK 2.0 Workflow graph assembly & edges
│   ├── nodes.py             # Intake, Extractor, GL-Coder, Validator, Gate, Poster nodes
│   ├── models.py            # Pydantic shared state models (InvoiceState, DecisionStep)
│   └── skill_loader.py      # Portable SKILL.md rules loader
├── skills/
│   └── ap_invoice_skill/
│       └── SKILL.md         # Portable agent skill (GL mapping & policy thresholds)
├── data/                    # Master tables & synthetic dataset generator
│   ├── gl_chart_of_accounts.json
│   ├── vendor_master.json
│   └── generate_synthetic_data.py
├── web/                     # FastAPI dashboard backend & web UI
│   ├── server.py            # FastAPI server with session & triage endpoints
│   └── static/              # HTML/CSS/JS frontend files (index.html, style.css, app.js)
├── eval/
│   └── eval_harness.py      # Batch benchmark script (N=50) & ROI readout
├── tests/                   # Pytest unit testing suite
├── docs/                    # Project specifications & Kaggle writeup draft
├── cli_demo.py              # Terminal interactive demo script
└── README.md                # Project documentation
```

---

## ⚖️ Disclosures & License

* **Commercial Tools Used:** Developed using Google Antigravity, Google Agent Development Kit (ADK 2.0), and Claude Code.
* **License:** Licensed under the [Apache 2.0 License](LICENSE).
