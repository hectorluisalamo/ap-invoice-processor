import os
import json
import asyncio
from typing import Dict, Any, List

from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types

from ap_invoice_processor.graph import root_agent

HUMAN_GATE_INTERRUPT_ID = "human_triage"


def _is_paused_at_gate(event) -> bool:
    """The human gate pause surfaces as a normal Event whose long_running_tool_ids
    contains the interrupt id - the runner never yields a RequestInput here."""
    return bool(event.long_running_tool_ids and HUMAN_GATE_INTERRUPT_ID in event.long_running_tool_ids)

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
                if _is_paused_at_gate(event):
                    paused_at_gate = True

                if event.output and isinstance(event.output, dict) and "invoice_id" in event.output:
                    final_state = event.output
                    route_signal = event.output.get("route_signal")
        except Exception as e:
            pass

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

    # ROI Formula Calculations (from PLAN.md / BUILD.md)
    manual_cost_per_inv = 14.50
    ai_compute_cost_per_inv = 0.35
    human_triage_cost_per_inv = 2.50
    
    avg_agent_cost_per_inv = (auto_post_rate / 100.0) * ai_compute_cost_per_inv + (1 - auto_post_rate / 100.0) * (ai_compute_cost_per_inv + human_triage_cost_per_inv)
    roi_savings_pct = ((manual_cost_per_inv - avg_agent_cost_per_inv) / manual_cost_per_inv) * 100.0

    print("\nBENCHMARK RESULTS BREAKDOWN:")
    print("-" * 75)
    print(f"{'Invoice ID':<15} {'Scenario Type':<24} {'Expected':<14} {'Actual':<14} {'Status':<8}")
    print("-" * 75)
    for r in results:
        status_str = "✅ PASS" if r["route_correct"] and r["gl_correct"] else "❌ FAIL"
        print(f"{r['id']:<15} {r['type']:<24} {r['expected_route']:<14} {r['actual_route']:<14} {status_str:<8}")

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
