# ABOUTME: Integration tests driving the FULL ADK workflow graph through the human gate,
# ABOUTME: resuming with approve/reject and asserting the posted/aborted terminal state.
"""End-to-end resume integration tests.

These run the real ADK Workflow via InMemoryRunner against a gated invoice, pause at the
human gate (detected via long_running_tool_ids), and resume by sending a FunctionResponse
carrying the human decision - exactly as the CLI and web demos do. Approve must end with a
posted_entry_id (posted through the NetSuite MCP server); reject must abort with none.
"""

import asyncio
import json
import os

from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types

from ap_invoice_processor.graph import root_agent
from ap_invoice_processor.hitl import is_paused_at_gate, build_resume_message, poster_ran

DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "synthetic_invoices",
    "invoices.json",
)


def _load_gated_invoice() -> dict:
    """Return a synthetic invoice whose expected route is human_review (a gated one)."""
    with open(DATA_PATH, "r") as f:
        invoices = json.load(f)
    for inv in invoices:
        if inv["ground_truth"]["expected_route"] == "human_review":
            return inv
    raise AssertionError("No gated (human_review) invoice found in dataset")


async def _run_gated_with_decision(decision: str) -> dict:
    """Run a gated invoice to the human gate, resume with `decision`, return final state."""
    app = App(name="test_app", root_agent=root_agent)
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(app_name="test_app", user_id="test_user")

    invoice = _load_gated_invoice()
    start_msg = types.Content(role="user", parts=[types.Part.from_text(text=json.dumps(invoice))])

    paused = False
    final_state = None
    async for event in runner.run_async(
        user_id="test_user", session_id=session.id, new_message=start_msg
    ):
        if is_paused_at_gate(event):
            paused = True
            break
        if event.output and isinstance(event.output, dict) and "invoice_id" in event.output:
            final_state = event.output

    assert paused, "Workflow did not pause at the human gate for a gated invoice"

    async for event in runner.run_async(
        user_id="test_user", session_id=session.id, new_message=build_resume_message(decision, f"integration test {decision}")
    ):
        if event.output and isinstance(event.output, dict) and "invoice_id" in event.output:
            final_state = event.output

    assert final_state is not None, "No terminal state produced after resume"
    return final_state


def test_gated_invoice_approved_posts():
    state = asyncio.run(_run_gated_with_decision("approved"))
    assert state.get("human_decision") == "approved"
    assert state.get("posted_entry_id"), "Approved gated invoice should have a posted_entry_id"
    assert state["posted_entry_id"].startswith("NS-POST-")
    # The Poster's step should truthfully credit the MCP server.
    poster_steps = [s for s in state["decision_trail"] if s["node_name"] == "Poster"]
    assert poster_steps, "Poster node should have run"
    assert poster_steps[-1]["output_summary"].get("posted_via") == "netsuite_mcp_server"


def test_gated_invoice_rejected_aborts():
    state = asyncio.run(_run_gated_with_decision("rejected"))
    assert state.get("human_decision") == "rejected"
    assert not state.get("posted_entry_id"), "Rejected invoice must NOT be posted"
    assert poster_ran(state), "Poster node should have run (to record the abort)"
    poster_steps = [s for s in state["decision_trail"] if s["node_name"] == "Poster"]
    assert poster_steps[-1]["output_summary"].get("status") == "aborted"
