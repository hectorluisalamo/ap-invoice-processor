# ABOUTME: Shared human-in-the-loop (HITL) helpers for the AP Copilot agent graph.
# ABOUTME: One source of truth for the human-gate interrupt id, pause detection, resume message, and poster check.
from google.genai import types

# The human gate suspends the workflow under this interrupt id; resuming targets
# ctx.resume_inputs['human_triage'].
HUMAN_GATE_INTERRUPT_ID = "human_triage"


def is_paused_at_gate(event) -> bool:
    """The runner surfaces the human gate pause as a normal Event whose
    long_running_tool_ids contains the interrupt id - never as a RequestInput."""
    return bool(event.long_running_tool_ids and HUMAN_GATE_INTERRUPT_ID in event.long_running_tool_ids)


def build_resume_message(decision: str, reasoning: str) -> types.Content:
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


def poster_ran(state: dict) -> bool:
    """True once the Poster node has appended a step to the decision trail."""
    if not isinstance(state, dict):
        return False
    return any(step.get("node_name") == "Poster" for step in state.get("decision_trail", []))
