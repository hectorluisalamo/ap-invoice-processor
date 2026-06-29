import pytest
from google.adk.agents.context import Context
from ap_invoice_processor.nodes import intake_node, extractor_node, gl_coder_node, policy_validator_node
from ap_invoice_processor.models import InvoiceState, LineItem

class DummySession:
    id = "test-session-123"

class DummyContext:
    def __init__(self):
        self.state = {}
        self.session = DummySession()
        self.node_path = "Workflow/test"
        self.node = None
        self.run_id = "run-1"
        self.attempt_count = 1
        self.resume_inputs = {}
        self.interrupt_ids = []
        self.output = None
        self.route = None

def test_intake_node():
    ctx = DummyContext()
    raw_input = {"id": "INV-TEST-001", "raw_text": "Vendor: Staples\nTotal: $100.00"}
    event = intake_node._func(ctx, raw_input)
    assert event.output["invoice_id"] == "INV-TEST-001"
    assert len(event.output["decision_trail"]) == 1

def test_gl_coder_node():
    ctx = DummyContext()
    state = InvoiceState(invoice_id="INV-TEST-002")
    state.extracted_fields.vendor_name = "Amazon Web Services"
    state.extracted_fields.line_items = [LineItem(description="Cloud EC2", unit_price=500.0, amount=500.0)]
    event = gl_coder_node._func(ctx, state.model_dump())
    line = event.output["extracted_fields"]["line_items"][0]
    assert line["gl_account"] == "6000"

def test_policy_validator_auto_post():
    ctx = DummyContext()
    state = InvoiceState(invoice_id="INV-TEST-003")
    state.extracted_fields.vendor_name = "Amazon Web Services"
    state.extracted_fields.invoice_number = "INV-TEST-003"
    state.extracted_fields.total_amount = 450.00
    event = policy_validator_node._func(ctx, state.model_dump())
    assert event.actions.route == "auto_post"

def test_policy_validator_high_dollar():
    ctx = DummyContext()
    state = InvoiceState(invoice_id="INV-TEST-004")
    state.extracted_fields.vendor_name = "Apple Hardware Direct"
    state.extracted_fields.invoice_number = "INV-TEST-004"
    state.extracted_fields.total_amount = 6500.00  # > $5,000 ceiling
    event = policy_validator_node._func(ctx, state.model_dump())
    assert event.actions.route == "human_review"
    assert event.output["validation_flags"]["exceeds_auto_post_ceiling"] is True
