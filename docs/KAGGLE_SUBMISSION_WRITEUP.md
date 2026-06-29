# AP Copilot: Autonomous Accounts Payable Processing with Human Gate Safety Rails

**Track:** Agents for Business  
**Submission Title:** AP Copilot — Linear ADK 2.0 Agent Graph for Autonomous Invoice Processing  
**Author:** Hector Luis Alamo  
**Frameworks Used:** Google Agent Development Kit (ADK 2.0), Google Antigravity, FastAPI, Pydantic  

---

## 1. The Problem

Accounts payable is where finance teams burn the most hours for the least credit. A clerk must key in vendor names, match purchase orders by hand, code line items to the right General Ledger (GL) account, and pray they don't pay the same invoice twice. Industry benchmarks for fully-loaded manual AP — the APQC and Ardent Partners type figures — land somewhere between $10 and $20 per invoice once you count labor, paper, and rework. I use **$14.50 as a representative midpoint** throughout this writeup, and I'm clear that it's an assumed benchmark, not a measured one.

OCR cleaned up the data-entry half of the job, but it didn't add judgment. A scanner can pull "$4,200.00" off a page; it can't decide that a Datadog charge belongs in Cloud Services, flag the invoice that's $300 over the PO, or refuse to post anything over five grand without a human signing off. That's the gap I built AP Copilot to close.

**AP Copilot** runs invoices end to end — from raw intake to a NetSuite GL posting — on a **Google ADK 2.0** agent graph with a hard human gate on anything high-dollar or compliance-flagged. The agent does the grunt work, but a person still owns the decisions.

---

## 2. System Architecture

AP Copilot is a linear six-node graph built on the **ADK 2.0 Workflow API**. Every node reads and writes one validated, immutable shared state (`InvoiceState`) and appends to a decision trail (`DecisionStep`), so I can replay exactly why the agent did what it did.

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
                                (NetSuite via MCP)                           (Safety Rail)
```

### What each node does:

1. **Intake (`intake_node`):** Takes raw invoice payloads — JSON, text, visual scans — and normalizes them into an initialized `InvoiceState`.
2. **Extractor (`extractor_node`):** Parses out vendor, totals, dates, line items, and PO numbers, scoring each field's confidence from 0.0 to 1.0.
3. **GL-Coder (`gl_coder_node`):** Reads an Agent Skill (`SKILL.md`) and maps each line item to a four-digit GL account (6000 Cloud Services, 6100 Office Supplies, and so on) plus a department tag, working from vendor patterns and item descriptions.
4. **Policy-Validator (`policy_validator_node`):** Enforces the hard rules and sets the route:
   - **$5,000 auto-post ceiling:** anything at or above $5,000 goes to a human.
   - **Duplicate detection:** checks invoice numbers against ERP history.
   - **PO matching:** validates against the procurement master.
   - **Confidence threshold:** flags any extraction below 0.85.
   - Then it routes to `auto_post` or `human_review`.
5. **Human Gate (`human_gate_node`):** A suspend/resume node. When a flag fires, execution pauses on ADK `RequestInput` and waits for a reviewer to approve or reject. Nothing slips past it.
6. **Poster (`poster_node`):** Posts the GL entry to NetSuite through a local MCP server and returns a transaction ID (`NS-POST-XXXXX`).

---

## 3. Competition Concepts Demonstrated

AP Copilot demonstrates **five of the six named concepts** — four in code, one in the build — leaving out only Deployability.

### Concept 1: ADK 2.0 Workflow Multi-Agent Graph
Built on `google.adk.workflow.Workflow` with `@node` decorators and explicit conditional edges (`Edge(from_node=..., to_node=..., route=...)`). ADK handles event propagation and async state serialization across the graph.

### Concept 2: MCP Server (real, not a stub)
The Poster posts through a **local NetSuite MCP server I wrote, called by a matching MCP client.** This isn't a mocked function pretending to be an integration — the agent makes a real MCP call across the protocol to post the GL entry. The server stands in for a NetSuite tenant, but the wire between agent and ERP is genuine MCP.

### Concept 3: Agent Skill (`SKILL.md`)
The accounting policy — vendor-to-GL tables, fallback rules, approval thresholds — lives in `skills/ap_invoice_skill/SKILL.md` and gets parsed at runtime, not hardcoded. Swap the file, swap the company's chart of accounts. The financial intelligence is portable.

### Concept 4: Security & Human-in-the-Loop
Financial agents move real money, so the controls are hard, not advisory. A $5,000 ceiling and duplicate protection are non-negotiable, and any flagged transaction suspends in memory via `RequestInput` and cannot write to NetSuite without explicit human approval.

### Concept 5: Antigravity

I built AP Copilot in Google Antigravity, and I got there by elimination. I first tried to build the whole thing in a general-purpose coding agent (Claude Code) on my laptop. Claude struggled, probably since ADK 2.0 and the Antigravity workflow aren't in its training; it stopped to research nearly every step, hit walls, and troubleshot its way forward — a slowgoing process. I paused it and moved to Antigravity (the desktop app), which is purpose-built for exactly this stack.

There the workflow was the opposite of a slog. I created a project, dropped in my `PLAN.md` and `BUILD.md` (created with Claude Code), and fed Antigravity my intent: "build a linear ADK agent graph: one invoice in → one posted GL entry out, with a human gate on anything risky." Antigravity produced an implementation plan ([`round1_initial_build/implementation_plan_v1.md`](round1_initial_build/implementation_plan_v1.md)) in under a minute; I reviewed and approved it, and the build followed.

---

## 4. Evaluation & ROI

I ran `eval/eval_harness.py` over **50 synthetic invoices** — a mix of clean routine bills and dirty compliance edge cases — to see how the agent actually performs instead of guessing.

### Results (N=50 synthetic invoices):
- **GL coding accuracy:** **82.0%**
- **Safety routing accuracy:** **94.0%** (risky invoices correctly sent to a human)
- **Auto-post rate:** **44.0%**
- **Human triage rate:** **56.0%**

### The ROI math:
- **Manual baseline:** $14.50 / invoice (representative industry midpoint, as stated above)
- **AP Copilot compute:** $0.35 / invoice
- **Human triage:** $2.50 / flagged review
- **Blended cost:** **$1.75 / invoice**
- **Savings:** **$12.75 per invoice — 87.9%**

The harness computes the blend straight from the auto-post and triage rates above, so the number moves if the rates move. No hand-waving.

---

## 5. The Surfaces

Two ways to drive it:

1. **Web dashboard (FastAPI + HTML/CSS/JS):** A dark-mode app at `http://localhost:8000` with live node-pipeline animation, a Human Gate triage desk, and a step-by-step decision audit log you can open up and read.
2. **Terminal CLI (`cli_demo.py`):** A console runner that steps through invoice scenarios and simulates the approval prompt for people who live in a shell.

---

## 6. Development & Validation

I built AP Copilot in Google Antigravity, then put it through two independent audits with Claude Code — involving a five-agent review covering confidentiality, rules-compliance, security, writing, and code & architecture. Every blocker the audits turned up got fixed before I submitted, including hardening the MCP integration from a stub into a real client-server pair. I ran the reviews because money agents fail quietly, and I'd rather catch the failures than ship them. The full round-by-round trail — including Antigravity's own build artifacts — is in [`docs/AUDIT.md`](AUDIT.md).

---

## 7. Conclusion

AP Copilot pairs autonomous GL coding with a human gate that can't be bypassed. The agent handles the volume — intake, extraction, coding, policy checks — and a person makes the call on anything that touches real money over the line. On 50 synthetic invoices, that combination cuts the per-invoice cost by 87.9% against a $14.50 baseline while keeping a full, replayable audit trail. The data here is 100% synthetic; the architecture is built to take real invoices next.
