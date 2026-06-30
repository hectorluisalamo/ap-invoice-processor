# Implementation Plan v1 - Initial Architecture & POC Build

Build an end-to-end linear ADK 2.0 Agent Workflow for Autonomous Accounts Payable (AP) Invoice Processing (`Intake → Extractor → GL-Coder → Policy-Validator → Human Gate → Poster`).

## Initial Scope & Key Architectural Choices
1. **Framework Version**: Built natively on ADK 2.0 Workflow API (`google.adk.workflow.Workflow`, `FunctionNode`, `Event`, `RequestInput`, `Context`).
2. **Auto-Post Hard Ceiling**: Set by default to $5,000.00 in `skills/ap_invoice_skill/SKILL.md`. Invoices $\ge \$5,000.00$ automatically route to the Human Gate.
3. **Dual Interface**: FastAPI Web UI dashboard and interactive terminal CLI.

## Initial Phase Breakdown
- **Phase 1: Master Data & Synthetic Payload Generator**: Generated 6 synthetic invoice scenarios to smoke-test specific code branches (clean auto-posts, high-dollar ceiling, PO mismatch, duplicate invoice, low confidence).
- **Phase 2: Core Agent Graph**: Implemented `models.py`, `skill_loader.py`, `nodes.py`, and `graph.py`.
- **Phase 3: Web Dashboard & CLI**: Created `server.py`, `index.html`, `style.css`, `app.js`, and `cli_demo.py`.
- **Phase 4: Evaluation Harness**: Created initial `eval_harness.py` running the 6-invoice smoke test suite.
