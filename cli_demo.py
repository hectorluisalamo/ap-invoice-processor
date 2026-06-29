import os
import json
import asyncio
from ap_invoice_processor.graph import root_agent
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.adk.events.request_input import RequestInput
from google.genai import types

async def run_cli_demo():
    print("=" * 70)
    print(" 🚀 AP COPILOT - AUTONOMOUS INVOICE PROCESSING AGENT (CLI DEMO)")
    print("=" * 70)

    data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "synthetic_invoices", "invoices.json")
    if not os.path.exists(data_path):
        print("Error: Synthetic invoices dataset not found. Run data/generate_synthetic_data.py first.")
        return

    with open(data_path, "r") as f:
        invoices = json.load(f)

    print("\nAvailable Synthetic Invoice Test Scenarios:")
    for idx, inv in enumerate(invoices[:6], 1):
        print(f"  [{idx}] {inv['id']} - {inv['ground_truth']['vendor_name']} (${inv['ground_truth']['total_amount']:.2f}) [{inv['test_case_type']}]")

    try:
        choice = input("\nSelect an invoice number to process (1-6) [default: 5]: ").strip()
        choice_idx = int(choice) - 1 if choice else 4
        selected_inv = invoices[choice_idx]
    except Exception:
        selected_inv = invoices[4]

    print(f"\n---> Starting ADK Workflow Graph for Invoice {selected_inv['id']}...")
    print(f"Description: {selected_inv['description']}\n")

    app_instance = App(name="ap_copilot_cli_app", root_agent=root_agent)
    runner = InMemoryRunner(app=app_instance)
    session = await runner.session_service.create_session(app_name="ap_copilot_cli_app", user_id="cli_user")

    input_text = json.dumps(selected_inv)
    new_msg = types.Content(role="user", parts=[types.Part.from_text(text=input_text)])

    last_state = None
    state_delta = None

    while True:
        paused_at_gate = False
        async for event in runner.run_async(
            user_id="cli_user",
            session_id=session.id,
            new_message=new_msg if not state_delta else None,
            state_delta=state_delta
        ):
            if isinstance(event, RequestInput):
                paused_at_gate = True
                break

            if event.actions and event.actions.state_delta and "invoice_state" in event.actions.state_delta:
                st = event.actions.state_delta["invoice_state"]
                last_state = st
                if st.get("decision_trail"):
                    last_step = st["decision_trail"][-1]
                    print(f"  [Node: {last_step['node_name']:<16}] Action: {last_step['action']}")
                    print(f"                            Reasoning: {last_step['reasoning']}")

            if event.output and isinstance(event.output, dict) and "posted_entry_id" in event.output:
                final_st = event.output
                if final_st.get("posted_entry_id"):
                    print("\n" + "=" * 70)
                    print(f" SUCCESS: NetSuite Transaction Posted! Transaction ID: {final_st['posted_entry_id']}")
                    print("=" * 70)
                elif final_st.get("human_decision") == "rejected":
                    print("\n" + "=" * 70)
                    print(" ABORTED: Posting cancelled by human reviewer rejection.")
                    print("=" * 70)
                return

        if paused_at_gate and last_state:
            print("\n" + "!" * 70)
            print(f" 🧑 HUMAN GATE INTERVENTION REQUIRED FOR INVOICE {last_state.get('invoice_id')}!")
            print("!" * 70)
            decision = input("\nApprove or Reject invoice? (approve/reject) [default: approve]: ").strip().lower()
            if not decision: decision = "approved"
            else: decision = "approved" if decision.startswith("a") else "rejected"
            
            reasoning = input("Enter reviewer reasoning: ").strip()
            if not reasoning: reasoning = f"Reviewed and {decision} via CLI prompt."

            last_state["human_decision"] = decision
            last_state["human_reasoning"] = reasoning
            state_delta = {"invoice_state": last_state}
            new_msg = None
        else:
            break

if __name__ == "__main__":
    asyncio.run(run_cli_demo())
