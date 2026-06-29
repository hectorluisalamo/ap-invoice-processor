from google.adk.workflow import Workflow, START, Edge
from ap_invoice_processor.nodes import (
    intake_node,
    extractor_node,
    gl_coder_node,
    policy_validator_node,
    human_gate_node,
    poster_node
)

edges = [
    (START, intake_node),
    (intake_node, extractor_node),
    (extractor_node, gl_coder_node),
    (gl_coder_node, policy_validator_node),
    Edge(from_node=policy_validator_node, to_node=poster_node, route="auto_post"),
    Edge(from_node=policy_validator_node, to_node=human_gate_node, route="human_review"),
    (human_gate_node, poster_node)
]

root_agent = Workflow(
    name="ap_copilot_workflow",
    edges=edges,
    description="AP Copilot - Autonomous Accounts Payable Invoice Processing Workflow with Human Gate Safety Rail"
)
