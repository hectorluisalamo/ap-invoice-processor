# Walkthrough v1 - Initial Build & Proof-of-Concept Verification

This walkthrough documents the initial proof-of-concept (POC) build pass for **AP Copilot**.

## Initial Build Verification (N=6 Synthetic Invoices)

### 1. Functional Testing & Unit Tests
- Implemented core node transformations and verified graph import.
- Ran `pytest tests/` (4 unit tests passed).

### 2. Initial Benchmark Execution Output (N=6 Smoke Test)
Ran `python eval/eval_harness.py` across the initial 6 curated test cases:
```text
===========================================================================
 📈 INITIAL PERFORMANCE METRICS (N=6 Smoke Test)
===========================================================================
 Total Invoices Evaluated  : 6
 GL Coding Accuracy        : 83.3%
 Safety Route Accuracy     : 100.0%
 Autonomous Auto-Post Rate : 33.3%
 Human Triage Rate         : 66.7%
---------------------------------------------------------------------------
 Baseline Manual AP Cost   : $14.50 / invoice
 AP Copilot Blended Cost   : $2.02 / invoice
 Total ROI Savings         : 86.1% Savings
===========================================================================
```

### Initial Observations & Identified Review Areas
- **Sample Size:** 6 invoices confirmed functional branch routing, but constituted a small sample for statistical evaluation.
- **Resumption Signature:** Initial resumption logic relied on passing `resume_inputs` to `run_async()`, which required refinement for native ADK 2.3.0 state compatibility.
