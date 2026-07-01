import os
import json
import asyncio
from typing import Dict, Any, List

from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types

from ap_invoice_processor.graph import root_agent
from ap_invoice_processor.hitl import is_paused_at_gate

async def run_evaluation():
    print("=" * 75)
    print(" 📊 AP COPILOT - AUTOMATED EVALUATION HARNESS & ROI READOUT")
    print("=" * 75)

    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    inv_path = os.path.join(data_dir, "synthetic_invoices", "invoices.json")
    
    if not os.path.exists(inv_path):
        print("Error: Invoices dataset missing.")
        return

    with open(inv_path, "r") as f:
        invoices = json.load(f)

    app_instance = App(name="eval_app", root_agent=root_agent)
    runner = InMemoryRunner(app=app_instance)

    results = []
    errored = []
    total_invoices = len(invoices)
    correct_gl_count = 0
    correct_route_count = 0
    auto_posted_count = 0
    human_routed_count = 0

    for inv in invoices:
        session = await runner.session_service.create_session(app_name="eval_app", user_id="eval_user")
        input_text = json.dumps(inv)
        new_msg = types.Content(role="user", parts=[types.Part.from_text(text=input_text)])

        final_state = None
        route_signal = None
        paused_at_gate = False

        try:
            # Consume the stream fully (don't break) - the runner suspends at the
            # gate on its own; breaking mid-stream cancels the workflow noisily.
            async for event in runner.run_async(user_id="eval_user", session_id=session.id, new_message=new_msg):
                if is_paused_at_gate(event):
                    paused_at_gate = True

                if event.output and isinstance(event.output, dict) and "invoice_id" in event.output:
                    final_state = event.output
                    route_signal = event.output.get("route_signal")
        except Exception as e:
            # Never silently swallow a run failure: a crashed invoice must surface as
            # an explicit error (and count against the metrics), not masquerade as a
            # clean auto_post. Record it and score it as a miss.
            errored.append({"id": inv["id"], "error": repr(e)})
            results.append({
                "id": inv["id"],
                "type": inv["test_case_type"],
                "expected_route": inv["ground_truth"]["expected_route"],
                "actual_route": "ERROR",
                "route_correct": False,
                "expected_gl": inv["ground_truth"].get("expected_gl"),
                "actual_gl": None,
                "gl_correct": False,
            })
            continue

        gt = inv["ground_truth"]
        expected_route = gt["expected_route"]
        actual_route = "human_review" if paused_at_gate else (route_signal or "auto_post")

        if actual_route == expected_route:
            correct_route_count += 1

        if actual_route == "auto_post":
            auto_posted_count += 1
        else:
            human_routed_count += 1

        actual_gl = None
        if final_state and final_state.get("extracted_fields", {}).get("line_items"):
            actual_gl = final_state["extracted_fields"]["line_items"][0].get("gl_account")
        
        if actual_gl == gt.get("expected_gl"):
            correct_gl_count += 1

        results.append({
            "id": inv["id"],
            "type": inv["test_case_type"],
            "expected_route": expected_route,
            "actual_route": actual_route,
            "route_correct": actual_route == expected_route,
            "expected_gl": gt.get("expected_gl"),
            "actual_gl": actual_gl,
            "gl_correct": actual_gl == gt.get("expected_gl")
        })

    gl_accuracy = (correct_gl_count / total_invoices) * 100.0
    route_accuracy = (correct_route_count / total_invoices) * 100.0
    auto_post_rate = (auto_posted_count / total_invoices) * 100.0

    # ROI Formula Calculations. Unit costs are STATED MODELING ASSUMPTIONS, adjustable here.
    # manual baseline is a conservative mid-range of APQC/Ardent AP benchmarks; compute & triage
    # are internal estimates. See "ROI methodology & assumptions" in README.md for sourcing.
    manual_cost_per_inv = 14.50
    ai_compute_cost_per_inv = 0.35
    human_triage_cost_per_inv = 2.50
    
    avg_agent_cost_per_inv = (auto_post_rate / 100.0) * ai_compute_cost_per_inv + (1 - auto_post_rate / 100.0) * (ai_compute_cost_per_inv + human_triage_cost_per_inv)
    roi_savings_pct = ((manual_cost_per_inv - avg_agent_cost_per_inv) / manual_cost_per_inv) * 100.0

    print("\nBENCHMARK RESULTS BREAKDOWN:")
    print(" Status = PASS only when BOTH route and GL are correct; each FAIL notes the failing dimension.")
    print("-" * 92)
    print(f"{'Invoice ID':<14} {'Scenario Type':<20} {'Route exp→act':<28} {'GL exp→act':<14} {'Status':<8}")
    print("-" * 92)
    for r in results:
        route_cell = f"{r['expected_route']}→{r['actual_route']}"
        gl_cell = f"{r['expected_gl']}→{r['actual_gl']}"
        if r["route_correct"] and r["gl_correct"]:
            status_str = "✅ PASS"
        else:
            dims = []
            if not r["route_correct"]: dims.append("route")
            if not r["gl_correct"]: dims.append("GL")
            status_str = "❌ FAIL (" + ", ".join(dims) + ")"
        print(f"{r['id']:<14} {r['type']:<20} {route_cell:<28} {gl_cell:<14} {status_str}")
    print("-" * 92)
    print(" Note: low_confidence invoices mask the vendor name, so the agent correctly routes to a human")
    print(" AND falls back to the default GL (6100). Those rows route right but score as a GL miss against")
    print(" the hidden true account — expected, conservative behavior, not an agent error.")

    if errored:
        print("\n" + "!" * 75)
        print(f" ⚠️  {len(errored)} INVOICE(S) ERRORED DURING EVALUATION (scored as misses):")
        for e in errored:
            print(f"    - {e['id']}: {e['error']}")
        print("!" * 75)

    print("\n" + "=" * 75)
    print(" 📈 FINAL PERFORMANCE METRICS & ROI READOUT")
    print("=" * 75)
    print(f" Total Invoices Evaluated  : {total_invoices}")
    print(f" GL Coding Accuracy        : {gl_accuracy:.1f}%")
    print(f" Safety Route Accuracy     : {route_accuracy:.1f}%")
    print(f" Autonomous Auto-Post Rate : {auto_post_rate:.1f}%")
    print(f" Human Triage Rate         : {(100.0 - auto_post_rate):.1f}%")
    print("-" * 75)
    print(f" Baseline Manual AP Cost   : ${manual_cost_per_inv:.2f} / invoice")
    print(f" AP Copilot Blended Cost   : ${avg_agent_cost_per_inv:.2f} / invoice")
    print(f" Net Cost Reduction        : ${manual_cost_per_inv - avg_agent_cost_per_inv:.2f} / invoice")
    print(f" Total ROI Savings         : {roi_savings_pct:.1f}% Savings")
    print("=" * 75 + "\n")

if __name__ == "__main__":
    asyncio.run(run_evaluation())
