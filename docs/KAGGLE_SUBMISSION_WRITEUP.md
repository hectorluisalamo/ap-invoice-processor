# AP Copilot: Autonomous Accounts Payable Processing with Human Gate Safety Rails

**Track:** Agents for Business  
**Submission Title:** AP Copilot — Linear ADK 2.0 Agent Graph for Autonomous Invoice Processing  
**Author:** Hector  
**Frameworks Used:** Google Agent Development Kit (ADK 2.0), Google Antigravity, FastAPI, Pydantic  

---

## 1. Problem Statement & Enterprise ROI Context

Accounts Payable (AP) processing remains one of the most labor-intensive and error-prone back-office operations in modern enterprise finance. Organizations typically incur **$12.88 to $19.83 per invoice** in manual labor, paper handling, data entry, and GL account coding. Furthermore, manual processing creates significant risk exposure to duplicate payments, mismatched purchase orders (POs), and policy compliance violations.

While optical character recognition (OCR) and document extraction tools have improved data ingestion, traditional systems lack autonomous reasoning capabilities. They cannot dynamically map unstructured line items to standard General Ledger (GL) accounts based on vendor context, nor can they enforce nuanced financial safety controls.

**AP Copilot** solves this challenge by implementing an autonomous accounts-payable agent powered by **Google ADK 2.0**. It automates end-to-end invoice processing—from raw intake to NetSuite ERP posting—while introducing a **hard Human-in-the-Loop (HITL) safety rail** on high-dollar or compliance-flagged invoices.

---

## 2. System Architecture & Agent Workflow Graph

AP Copilot is architected as a linear 6-node graph using the **ADK 2.0 Workflow API**. The workflow threads a validated, immutable shared state model (`InvoiceState`) and a granular decision trail (`DecisionStep`) across every step of execution.

```text
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

### Node Execution Responsibilities:

1. **Intake Node (`intake_node`):** Ingests raw invoice payloads (JSON, text streams, visual scans) and normalizes the data into an initialized `InvoiceState` shared object.
2. **Extractor Node (`extractor_node`):** Executes structured entity parsing to extract vendor names, total amounts, invoice dates, line item details, and PO numbers, assigning confidence scores (0.0 to 1.0) for each field.
3. **GL-Coder Node (`gl_coder_node`):** Applies rules from a portable **Agent Skill (`SKILL.md`)** to map individual line items to the correct 4-digit GL account codes (e.g., GL 6000 Cloud Services, GL 6100 Office Supplies) and department tags based on vendor patterns and item descriptions.
4. **Policy-Validator Node (`policy_validator_node`):** Checks hard financial policies and safety rails:
   - **$5,000 Auto-Post Ceiling:** Automatically flags any invoice $\ge \$5,000.00$ for human review.
   - **Duplicate Detection:** Verifies invoice numbers against historical ERP records.
   - **PO Matching:** Validates purchase orders against the procurement master database.
   - **Confidence Threshold:** Flags extractions with confidence $< 0.85$.
   - *Routing Signal:* Sets conditional route to `auto_post` or `human_review`.
5. **Human Gate Node (`human_gate_node`):** An interactive suspend/resume node. If policy flags are raised, execution pauses via ADK `RequestInput` and waits for human reviewer triage (Approve or Reject).
6. **Poster Node (`poster_node`):** Executes mock NetSuite ERP GL posting via MCP backend integration, generating a transaction tracking ID (`NS-POST-XXXXX`).

---

## 3. Demonstration of Core Competition Concepts

AP Copilot successfully demonstrates **5 of the 6 official competition concepts**:

### Concept 1: ADK 2.0 Workflow Multi-Agent Graph
Built natively using `google.adk.workflow.Workflow`, `@node` decorators, and explicit conditional edge routing (`Edge(from_node=..., to_node=..., route=...)`). The framework manages event propagation and async state serialization.

### Concept 2: MCP Server Integration
Simulates ERP read/write tools and Model Context Protocol (MCP) interactions for vendor master verification, PO database lookups, and final NetSuite GL posting.

### Concept 3: Portable Agent Skill (`SKILL.md`)
Encapsulates company accounting policies, vendor GL mapping tables, fallback rules, and approval thresholds inside a modular `skills/ap_invoice_skill/SKILL.md` file, demonstrating how financial intelligence can be packaged and reused across agents.

### Concept 4: Security Features & Human-in-the-Loop Safety Rails
Financial agents manage real money. AP Copilot enforces a strict **hard dollar ceiling ($5,000.00)** and duplicate protection. Flagged transactions suspend cleanly in memory via `RequestInput` and cannot write to NetSuite without explicit human approval.

### Concept 5: Antigravity Development Orchestration
Scaffolded and developed using Google Antigravity agent workflows, leveraging artifact-driven implementation planning (`implementation_plan.md` and `walkthrough.md`).

---

## 4. Evaluation Benchmark & Statistical ROI Readout

To validate AP Copilot under statistical rigor, an automated evaluation harness ([eval_harness.py](file:///Users/hector/development/Antigravity/ap-invoice-processer/eval/eval_harness.py)) was executed across a randomized benchmark suite of **50 synthetic invoices** representing clean routine bills and dirty compliance edge cases.

### Benchmark Results (N=50 Synthetic Invoices):
- **Total Invoices Evaluated:** 50
- **GL Coding Accuracy:** **82.0%**
- **Safety Routing Accuracy:** **94.0%** (Correctly routed risky invoices to human triage)
- **Autonomous Auto-Post Rate:** **44.0%**
- **Human Triage Rate:** **56.0%**

### Enterprise Financial ROI Model:
- **Baseline Manual AP Cost:** $14.50 / invoice
- **AP Copilot Compute Cost:** $0.35 / invoice (AI extraction & reasoning)
- **Human Triage Cost:** $2.50 / review (for flagged invoices)
- **Blended AP Copilot Cost:** **$1.75 / invoice**
- **Net Cost Reduction:** **$12.75 saved per invoice**
- **Total ROI Savings:** **87.9% Cost Savings**

---

## 5. User Interfaces & Demoable Surface

AP Copilot features two complete user interfaces:
1. **Interactive Web Dashboard (FastAPI + HTML/CSS/JS):** A sleek, dark-mode web application (`http://localhost:8000`) providing live visual node pipeline animations, an interactive Human Gate Triage desk, and step-by-step decision audit log inspection.
2. **Interactive Terminal CLI (`cli_demo.py`):** A console runner allowing users to step through invoice scenarios and simulate human approval prompts in terminal environments.

---

## 6. Conclusion & Summary

AP Copilot demonstrates how Google's ADK 2.0 framework and Antigravity tooling enable developers to build robust, secure, and business-critical AI agents. By pairing autonomous GL coding with unbypassable human safety rails, organizations can capture an **87.9% cost reduction** while retaining complete auditability and financial risk control.
