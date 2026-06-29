import os
import json
import asyncio
from ap_invoice_processor.graph import root_agent
from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types

HUMAN_GATE_INTERRUPT_ID = "human_triage"


def _is_paused_at_gate(event) -> bool:
    """The runner surfaces the human gate pause as a normal Event whose
    long_running_tool_ids contains the interrupt id - never as a RequestInput."""
    return bool(event.long_running_tool_ids and HUMAN_GATE_INTERRUPT_ID in event.long_running_tool_ids)


def _build_resume_message(decision: str, reasoning: str) -> types.Content:
    """Resume an interrupted node by sending a FunctionResponse carrying the human
    decision. The runner maps it to ctx.resume_inputs['human_triage']."""
    return types.Content(
        role="user",
        parts=[
            types.Part(
                function_response=types.FunctionResponse(
                    id=HUMAN_GATE_INTERRUPT_ID,
                    name="adk_request_input",
                    response={"decision": decision, "reasoning": reasoning},
                )
            )
        ],
    )

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
    next_message = new_msg

    while True:
        paused_at_gate = False
        # Consume the full event stream to completion - never break out early. The
        # runner suspends the generator on its own at the human gate (the gate event
        # is the last one yielded), and on a non-gated run the stream ends after the
        # Poster. Breaking mid-stream cancels the workflow and produces noisy errors.
        async for event in runner.run_async(
            user_id="cli_user",
            session_id=session.id,
            new_message=next_message,
        ):
            if _is_paused_at_gate(event):
                paused_at_gate = True

            if event.output and isinstance(event.output, dict) and "invoice_id" in event.output:
                st = event.output
                last_state = st
                if st.get("decision_trail"):
                    last_step = st["decision_trail"][-1]
                    print(f"  [Node: {last_step['node_name']:<16}] Action: {last_step['action']}")
                    print(f"                            Reasoning: {last_step['reasoning']}")

        # Terminal detection: the Poster ran (posted a real id, or aborted on reject).
        if last_state and last_state.get("posted_entry_id"):
            print("\n" + "=" * 70)
            print(f" SUCCESS: NetSuite Transaction Posted via MCP! Transaction ID: {last_state['posted_entry_id']}")
            print("=" * 70)
            return
        if last_state and last_state.get("human_decision") == "rejected" and _poster_ran(last_state):
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

            next_message = _build_resume_message(decision, reasoning)
        else:
            break


def _poster_ran(state: dict) -> bool:
    """True once the Poster node has appended a step to the decision trail."""
    return any(step.get("node_name") == "Poster" for step in state.get("decision_trail", []))

if __name__ == "__main__":
    asyncio.run(run_cli_demo())
