import os
import json
import asyncio
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from google.adk.apps import App
from google.adk.runners import InMemoryRunner
from google.genai import types

from ap_invoice_processor.graph import root_agent

HUMAN_GATE_INTERRUPT_ID = "human_triage"


def _is_paused_at_gate(event) -> bool:
    """The human gate pause surfaces as a normal Event whose long_running_tool_ids
    contains the interrupt id - the runner never yields a RequestInput here."""
    return bool(event.long_running_tool_ids and HUMAN_GATE_INTERRUPT_ID in event.long_running_tool_ids)


def _poster_ran(state: dict) -> bool:
    """True once the Poster node has appended a step to the decision trail."""
    if not isinstance(state, dict):
        return False
    return any(step.get("node_name") == "Poster" for step in state.get("decision_trail", []))


def _build_resume_message(decision: str, reasoning: str) -> types.Content:
    """Resume the interrupted human_gate_node by sending a FunctionResponse carrying
    the decision. The runner maps it to ctx.resume_inputs['human_triage']."""
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

app_instance = App(name="ap_copilot_app", root_agent=root_agent)
runner = InMemoryRunner(app=app_instance)

web_app = FastAPI(title="AP Copilot - Autonomous Invoice Processing Dashboard")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), "data")

web_app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}

def load_synthetic_invoices() -> list:
    inv_path = os.path.join(DATA_DIR, "synthetic_invoices", "invoices.json")
    if os.path.exists(inv_path):
        with open(inv_path, "r") as f:
            return json.load(f)
    return []

@web_app.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    with open(index_path, "r") as f:
        return HTMLResponse(content=f.read())

@web_app.get("/api/invoices")
async def list_invoices():
    return load_synthetic_invoices()

@web_app.get("/api/sessions/{session_id}")
async def get_session_state(session_id: str):
    if session_id not in ACTIVE_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    return ACTIVE_SESSIONS[session_id]

class RunInvoiceRequest(BaseModel):
    invoice_id: str

class HumanTriageRequest(BaseModel):
    decision: str  # "approved" or "rejected"
    reasoning: Optional[str] = None

@web_app.post("/api/run")
async def run_invoice(req: RunInvoiceRequest):
    invoices = load_synthetic_invoices()
    selected = next((inv for inv in invoices if inv["id"] == req.invoice_id), None)
    if not selected:
        raise HTTPException(status_code=404, detail=f"Invoice {req.invoice_id} not found")

    session_id = f"sess_{req.invoice_id}_{int(asyncio.get_event_loop().time())}"
    
    adk_session = await runner.session_service.create_session(
        app_name="ap_copilot_app", user_id="demo_user"
    )

    ACTIVE_SESSIONS[session_id] = {
        "session_id": session_id,
        "adk_session_id": adk_session.id,
        "invoice_id": req.invoice_id,
        "status": "running",
        "current_node": "START",
        "invoice_state": None,
        "is_paused_at_gate": False,
        "interrupt_id": None
    }

    input_text = json.dumps(selected)
    start_msg = types.Content(role="user", parts=[types.Part.from_text(text=input_text)])
    asyncio.create_task(_execute_workflow(session_id, adk_session.id, new_msg=start_msg))
    return {"session_id": session_id, "status": "started"}

async def _execute_workflow(session_id: str, adk_session_id: str, new_msg: types.Content = None):
    sess_info = ACTIVE_SESSIONS.get(session_id)
    if not sess_info:
        return

    try:
        paused = False
        # Consume the stream fully; the runner suspends at the gate on its own (the
        # gate event is the last one yielded). Returning mid-stream cancels the
        # workflow and emits noisy errors.
        async for event in runner.run_async(
            user_id="demo_user",
            session_id=adk_session_id,
            new_message=new_msg,
        ):
            if _is_paused_at_gate(event):
                paused = True

            if event.output and isinstance(event.output, dict) and "invoice_id" in event.output:
                st = event.output
                sess_info["invoice_state"] = st
                if st.get("decision_trail"):
                    last_step = st["decision_trail"][-1]
                    sess_info["current_node"] = last_step["node_name"]

        if paused:
            sess_info["status"] = "paused"
            sess_info["is_paused_at_gate"] = True
            sess_info["interrupt_id"] = HUMAN_GATE_INTERRUPT_ID
            sess_info["current_node"] = "Human Gate"
            return

        # The stream ended without pausing: the Poster ran (posted or aborted).
        final_state = sess_info.get("invoice_state") or {}
        if isinstance(final_state, dict) and final_state.get("human_decision") == "rejected" and _poster_ran(final_state):
            sess_info["status"] = "aborted"
        else:
            sess_info["status"] = "completed"
        sess_info["is_paused_at_gate"] = False
        sess_info["current_node"] = "Poster"
    except Exception as e:
        print(f"Workflow Execution Error for {session_id}: {e}")
        sess_info["status"] = "error"
        sess_info["error_message"] = str(e)

@web_app.post("/api/sessions/{session_id}/triage")
async def submit_triage(session_id: str, req: HumanTriageRequest):
    sess_info = ACTIVE_SESSIONS.get(session_id)
    if not sess_info:
        raise HTTPException(status_code=404, detail="Session not found")
    if not sess_info.get("is_paused_at_gate"):
        raise HTTPException(status_code=400, detail="Session is not paused at Human Gate")

    decision = req.decision.lower()
    reasoning = req.reasoning or f"Reviewed and {decision} via dashboard triage."

    sess_info["status"] = "resuming"
    sess_info["is_paused_at_gate"] = False

    resume_msg = _build_resume_message(decision, reasoning)
    asyncio.create_task(_execute_workflow(session_id, sess_info["adk_session_id"], new_msg=resume_msg))
    return {"status": "resumed", "decision": decision}
