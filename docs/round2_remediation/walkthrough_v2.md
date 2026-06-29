# Walkthrough v2 - Final Remediation & 50-Invoice Benchmark Verification

This walkthrough documents the completion and verification of the Round 2 remediation pass.

## Round 2 Verification & Benchmark Results

### 1. Fixed Demo Resumption & ADK 2.3.0 Compatibility
- Updated `server.py` and `cli_demo.py` to use `state_delta={"invoice_state": updated_state}`. Both web UI and CLI demos execute cleanly across paused human gate interventions without exceptions.

### 2. Dynamic SKILL.md Parsing Verified
- Executed dynamic table parser test in `skill_loader.py`. Successfully extracted 5 vendor mapping rules directly from `skills/ap_invoice_skill/SKILL.md`.

### 3. Expanded Statistical Benchmark Results (N=50 Synthetic Invoices)
Ran `python eval/eval_harness.py` across 50 randomized synthetic invoices:
```text
===========================================================================
 📈 FINAL PERFORMANCE METRICS & ROI READOUT (N=50 Statistical Benchmark)
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

### 4. Repository Cleanliness & Remote Deployment
- Created root `LICENSE` (Apache 2.0) and `requirements.txt`.
- Published repository to public remote: `https://github.com/hectorluisalamo/ap-invoice-processor`.
