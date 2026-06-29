# Implementation Plan v2 - Remediation & Production Enhancement Pass

This implementation plan documents the Round 2 engineering and remediation pass based on comprehensive repository code review.

## Round 2 Remediation Objectives

### 1. ADK 2.3.0 Native Resumption Protocol (MUST-FIX)
- Refactor workflow resumption in `server.py`, `cli_demo.py`, and `nodes.py` to replace invalid `run_async(resume_inputs=...)` keyword calls with native ADK 2.3.0 `state_delta` update propagation.

### 2. Concept Count Alignment & MCP Disclosures (MUST-FIX)
- Remove unbuilt MCP server backend claims. Accurately state **3 core named competition concepts** (ADK 2.0 Workflow Graph, Agent Skill `SKILL.md`, Security & HITL Safety Rails) + Antigravity orchestration.

### 3. Dynamic SKILL.md Markdown Table Parsing (SHOULD-FIX)
- Update `skill_loader.py` with regex table parsing to extract vendor-to-GL mapping tables directly from `SKILL.md` at runtime.

### 4. Statistical Benchmark Expansion (N=50)
- Expand `generate_synthetic_data.py` to generate a 50-invoice dataset for statistical rigor.

### 5. Repository Packaging & Reproducibility
- Create root `LICENSE` (Apache 2.0) and `requirements.txt` with pinned versions (`google-adk==2.3.0`).
- Remove internal strategy documents from public repo tracking.
