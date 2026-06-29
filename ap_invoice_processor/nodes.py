import os
import json
import random
from typing import Any, AsyncGenerator
from datetime import datetime

from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.agents.context import Context
from google.adk.workflow import node

from ap_invoice_processor.models import InvoiceState, DecisionStep, LineItem
from ap_invoice_processor.skill_loader import load_skill_rules

def _load_json_data(filename: str) -> Any:
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    filepath = os.path.join(data_dir, filename)
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return {}

def _parse_input_to_dict(node_input: Any) -> dict:
    if isinstance(node_input, dict):
        return node_input
    if hasattr(node_input, "parts") and node_input.parts:
        for part in node_input.parts:
            if hasattr(part, "text") and part.text:
                try:
                    return json.loads(part.text)
                except Exception:
                    pass
    if isinstance(node_input, str):
        try:
            return json.loads(node_input)
        except Exception:
            pass
    return {}

@node
def intake_node(ctx: Context, node_input: Any) -> Event:
    """Intake node: pulls raw invoice payload and initializes normalized shared state."""
    payload = _parse_input_to_dict(node_input)
    
    if payload and "id" in payload:
        invoice_id = payload.get("id")
        raw_text = payload.get("raw_text", "")
        extracted_sim = payload.get("simulated_extraction", {})
    else:
        invoice_id = f"INV-{random.randint(1000, 9999)}"
        raw_text = str(node_input)
        extracted_sim = {}

    invoice_state = InvoiceState(
        invoice_id=invoice_id,
        raw_text=raw_text
    )

    if extracted_sim:
        for k, v in extracted_sim.items():
            if k == "line_items":
                invoice_state.extracted_fields.line_items = [LineItem(**item) for item in v]
            elif k == "confidence":
                for conf_k, conf_v in v.items():
                    setattr(invoice_state.field_confidence, conf_k, conf_v)
            elif hasattr(invoice_state.extracted_fields, k):
                setattr(invoice_state.extracted_fields, k, v)

    step = DecisionStep(
        step_index=len(invoice_state.decision_trail) + 1,
        node_name="Intake",
        action="Pull & Normalize Raw Invoice",
        reasoning=f"Successfully ingested raw invoice payload for ID {invoice_id}.",
        confidence=1.0,
        output_summary={"invoice_id": invoice_id, "raw_length": len(raw_text)}
    )
    invoice_state.decision_trail.append(step)

    state_dict = invoice_state.model_dump()
    return Event(output=state_dict, state={"invoice_state": state_dict})

@node
def extractor_node(ctx: Context, node_input: Any) -> Event:
    """Extractor node: structured extraction & confidence calculation."""
    state_dict = node_input if isinstance(node_input, dict) and "invoice_id" in node_input else ctx.state.get("invoice_state", {})
    invoice_state = InvoiceState(**state_dict)

    fields = invoice_state.extracted_fields
    conf = invoice_state.field_confidence

    avg_conf = (conf.vendor_name + conf.invoice_number + conf.date + conf.total_amount + conf.line_items) / 5.0

    step = DecisionStep(
        step_index=len(invoice_state.decision_trail) + 1,
        node_name="Extractor",
        action="Structured Vision & Entity Parsing",
        reasoning=f"Extracted vendor '{fields.vendor_name}', total ${fields.total_amount:.2f}, with average confidence {avg_conf:.2f}.",
        confidence=avg_conf,
        output_summary={
            "vendor_name": fields.vendor_name,
            "total_amount": fields.total_amount,
            "po_number": fields.po_number,
            "line_items_count": len(fields.line_items),
            "avg_confidence": round(avg_conf, 2)
        }
    )
    invoice_state.decision_trail.append(step)

    res_dict = invoice_state.model_dump()
    return Event(output=res_dict, state={"invoice_state": res_dict})

@node
def gl_coder_node(ctx: Context, node_input: Any) -> Event:
    """GL-Coder node: map line items to GL accounts using SKILL.md rules."""
    state_dict = node_input if isinstance(node_input, dict) and "invoice_id" in node_input else ctx.state.get("invoice_state", {})
    invoice_state = InvoiceState(**state_dict)

    skill_rules = load_skill_rules()
    vendor_master = _load_json_data("vendor_master.json")

    vendor_name_clean = (invoice_state.extracted_fields.vendor_name or "").lower()
    matched_vendor_entry = None
    if isinstance(vendor_master, list):
        for vm in vendor_master:
            if vm["name"].lower() in vendor_name_clean or any(alias.lower() in vendor_name_clean for alias in vm.get("aliases", [])):
                matched_vendor_entry = vm
                break

    coded_count = 0
    for item in invoice_state.extracted_fields.line_items:
        gl = None
        gl_name = None
        dept = None

        if matched_vendor_entry:
            gl = matched_vendor_entry.get("default_gl_account")
            dept = matched_vendor_entry.get("default_department")

        if not gl:
            for rule in skill_rules.vendor_mappings:
                if any(kw in vendor_name_clean for kw in rule["keywords"]):
                    gl = rule["gl"]
                    gl_name = rule["gl_name"]
                    dept = rule["department"]
                    break

        if not gl:
            desc_clean = item.description.lower()
            for fb in skill_rules.fallback_keywords:
                if any(kw in desc_clean for kw in fb["keywords"]):
                    gl = fb["gl"]
                    gl_name = fb["gl_name"]
                    dept = fb["department"]
                    break

        if not gl:
            gl = "6100"
            gl_name = "Office Supplies & Software (Fallback)"
            dept = "Administration"

        item.gl_account = gl
        item.gl_account_name = gl_name
        item.department = dept
        coded_count += 1

    step = DecisionStep(
        step_index=len(invoice_state.decision_trail) + 1,
        node_name="GL-Coder",
        action="Apply Portable Agent Skill GL Rules",
        reasoning=f"Mapped {coded_count} line items to GL accounts based on SKILL.md vendor & keyword rules.",
        confidence=0.95 if matched_vendor_entry else 0.85,
        output_summary={"coded_line_items": coded_count, "matched_vendor": matched_vendor_entry["name"] if matched_vendor_entry else "Fallback"}
    )
    invoice_state.decision_trail.append(step)

    res_dict = invoice_state.model_dump()
    return Event(output=res_dict, state={"invoice_state": res_dict})

@node
def policy_validator_node(ctx: Context, node_input: Any) -> Event:
    """Policy-Validator node: check hard ceiling ($5k), duplicates, PO match, confidence."""
    state_dict = node_input if isinstance(node_input, dict) and "invoice_id" in node_input else ctx.state.get("invoice_state", {})
    invoice_state = InvoiceState(**state_dict)

    skill_rules = load_skill_rules()
    po_db = _load_json_data("po_database.json")
    historical_invoices = _load_json_data("historical_invoices.json")

    flags = invoice_state.validation_flags
    fields = invoice_state.extracted_fields
    conf = invoice_state.field_confidence

    if isinstance(historical_invoices, list) and fields.invoice_number in historical_invoices:
        flags.duplicate_found = True

    if fields.total_amount >= skill_rules.auto_post_ceiling:
        flags.exceeds_auto_post_ceiling = True

    min_extracted_conf = min(conf.vendor_name, conf.invoice_number, conf.date, conf.total_amount)
    if min_extracted_conf < skill_rules.min_confidence:
        flags.low_confidence_fields = True

    vendor_master = _load_json_data("vendor_master.json")
    matched_vendor = False
    po_req = False
    if isinstance(vendor_master, list):
        v_clean = (fields.vendor_name or "").lower()
        for vm in vendor_master:
            if vm["name"].lower() in v_clean or any(alias.lower() in v_clean for alias in vm.get("aliases", [])):
                matched_vendor = True
                po_req = vm.get("po_required", False)
                invoice_state.extracted_fields.vendor_id = vm.get("vendor_id")
                break
    if not matched_vendor:
        flags.unknown_vendor = True

    if po_req or fields.po_number:
        po = fields.po_number
        if not po or po not in po_db:
            flags.po_matched = False
            flags.po_mismatch_reason = f"PO '{po}' not found in PO database."

    needs_human = (
        flags.duplicate_found or
        flags.exceeds_auto_post_ceiling or
        flags.low_confidence_fields or
        flags.unknown_vendor or
        not flags.po_matched
    )

    route_signal = "human_review" if needs_human else "auto_post"
    invoice_state.route_signal = route_signal

    flag_list = []
    if flags.duplicate_found: flag_list.append("Duplicate Invoice")
    if flags.exceeds_auto_post_ceiling: flag_list.append(f"Exceeds ${skill_rules.auto_post_ceiling:.0f} Ceiling")
    if flags.low_confidence_fields: flag_list.append("Low Confidence")
    if flags.unknown_vendor: flag_list.append("Unknown Vendor")
    if not flags.po_matched: flag_list.append("PO Mismatch")

    step = DecisionStep(
        step_index=len(invoice_state.decision_trail) + 1,
        node_name="Policy-Validator",
        action="Evaluate Compliance & Hard Safety Rails",
        reasoning=f"Validation evaluated. Route = '{route_signal}'. Tripped flags: {', '.join(flag_list) if flag_list else 'None'}.",
        confidence=1.0,
        output_summary={"route_signal": route_signal, "flags": flag_list}
    )
    invoice_state.decision_trail.append(step)

    res_dict = invoice_state.model_dump()
    return Event(output=res_dict, route=route_signal, state={"invoice_state": res_dict})

@node(rerun_on_resume=True)
async def human_gate_node(ctx: Context, node_input: Any) -> AsyncGenerator[Any, None]:
    """Human Gate node: pauses for user triage approval/rejection if flagged."""
    state_dict = node_input if isinstance(node_input, dict) and "invoice_id" in node_input else ctx.state.get("invoice_state", {})
    invoice_state = InvoiceState(**state_dict)

    if not ctx.resume_inputs or "human_triage" not in ctx.resume_inputs:
        yield RequestInput(
            interrupt_id="human_triage",
            message=f"HUMAN GATE PAUSE: Invoice {invoice_state.invoice_id} (${invoice_state.extracted_fields.total_amount:.2f}) requires human review."
        )
        return

    triage_data = ctx.resume_inputs["human_triage"]
    if isinstance(triage_data, str):
        decision = triage_data.lower()
        reasoning = "Reviewed and decided via triage input."
    elif isinstance(triage_data, dict):
        decision = triage_data.get("decision", "approved").lower()
        reasoning = triage_data.get("reasoning", "Reviewed via triage portal.")
    else:
        decision = "approved"
        reasoning = "Default approved on resume."

    invoice_state.human_decision = decision
    invoice_state.human_reasoning = reasoning

    step = DecisionStep(
        step_index=len(invoice_state.decision_trail) + 1,
        node_name="Human Gate",
        action="Interactive Human-in-the-Loop Triage",
        reasoning=f"Human reviewer submitted decision: '{decision.upper()}'. Reasoning: {reasoning}",
        confidence=1.0,
        output_summary={"decision": decision, "reasoning": reasoning}
    )
    invoice_state.decision_trail.append(step)

    res_dict = invoice_state.model_dump()
    yield Event(output=res_dict, state={"invoice_state": res_dict})

@node
def poster_node(ctx: Context, node_input: Any) -> Event:
    """Poster node: executes NetSuite GL posting for approved entries."""
    state_dict = node_input if isinstance(node_input, dict) and "invoice_id" in node_input else ctx.state.get("invoice_state", {})
    invoice_state = InvoiceState(**state_dict)

    if invoice_state.human_decision == "rejected":
        step = DecisionStep(
            step_index=len(invoice_state.decision_trail) + 1,
            node_name="Poster",
            action="Abort NetSuite GL Posting",
            reasoning="Invoice posting aborted because human reviewer rejected the entry.",
            confidence=1.0,
            output_summary={"status": "aborted", "reason": invoice_state.human_reasoning}
        )
        invoice_state.decision_trail.append(step)
        res_dict = invoice_state.model_dump()
        return Event(output=res_dict, state={"invoice_state": res_dict})

    ns_id = f"NS-POST-{random.randint(10000, 99999)}"
    timestamp = datetime.now().isoformat()
    invoice_state.posted_entry_id = ns_id
    invoice_state.posting_timestamp = timestamp

    step = DecisionStep(
        step_index=len(invoice_state.decision_trail) + 1,
        node_name="Poster",
        action="Write Posted GL Entry via NetSuite MCP Backend",
        reasoning=f"Successfully posted GL entry to NetSuite sandbox with Transaction ID '{ns_id}'.",
        confidence=1.0,
        output_summary={
            "netsuite_transaction_id": ns_id,
            "posted_timestamp": timestamp,
            "total_posted_amount": invoice_state.extracted_fields.total_amount
        }
    )
    invoice_state.decision_trail.append(step)

    res_dict = invoice_state.model_dump()
    return Event(output=res_dict, state={"invoice_state": res_dict})
