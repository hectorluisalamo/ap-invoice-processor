# Implementation Plan - Dynamic Workflow Fork, Playback Animations, and UI Lockout Fix

This plan details the changes required to transition the linear workflow graph into a dynamic fork (displaying the bypass vs. human gate path), animate the nodes lighting up in sequence to show the path of a given invoice, and fix the UI lockout bug where users cannot select other invoices after a rejection.

## Proposed Changes

### Front-End Structure & Visuals

#### [MODIFY] [index.html](../../web/static/index.html)
- Restructure the pipeline visualizer element (`.pipeline-visualizer`) to separate the direct "Auto-Post" bypass path from the "Human Gate" path.
- Add branch connector divs (`#conn-branch-left`, `#conn-branch-right`) and a bypass connector div (`#conn-bypass`).

#### [MODIFY] [style.css](../../web/static/style.css)
- Convert `.pipeline-visualizer` to a CSS Grid layout with 11 columns and 2 rows to display the fork:
  - Row 1: Intake, Extractor, GL-Coder, Validator, Bypass Line, Poster.
  - Row 2: Human Gate (centered under the bypass line).
- Style the branch connectors with left/right and bottom borders to create elegant L-shaped paths leading down to and up from the Human Gate.
- Style the bypass connector as a dashed line with a centered text label "Auto-Post".
- Add active and completed state colors/animations for all connectors (green for completed, blue with a drop shadow/glow for active/running).

### Front-End Orchestration & Animation Playback

#### [MODIFY] [app.js](../../web/static/app.js)
- Implement a step-by-step **Playback Animation System** that sequentially highlights the active node and paths with a realistic delay (e.g., 600ms per step) until it catches up with the actual backend decision trail.
- Update the live details card dynamically during playback to show fields as they are processed (e.g. "Parsing..." initially, then showing GL account mappings after the GL-Coder step).
- Fix the **UI Lockout Bug**:
  - Ensure that `pollInterval` and any playback timers are cleared when the session enters a final state (`completed`, `aborted`, or `error`).
  - Update the status badge appropriately for all final states (including "Posting Aborted").
  - Release any state blocking so users can click on other invoices on the left panel after a rejection.

## Verification Plan

### Automated Verification
- Run the server locally and inspect page loading, visual layouts, and transitions.

### Manual Verification
- **Test Case 1 (Auto-Post Bypass)**: Select a "clean auto post" invoice (e.g., `INV-2026-001`). Run the workflow. Verify:
  - Nodes light up in sequence (`Intake` -> `Extractor` -> `GL-Coder` -> `Validator` -> `Poster`).
  - The bypass connector line (`#conn-bypass`) lights up, while the Human Gate and its connectors remain faded.
  - The workflow completes and displays "Completed & Posted".
  - You can immediately select and run another invoice.
- **Test Case 2 (Human Triage & Rejection)**: Select a "low confidence" or "exceeds ceiling" invoice (e.g., `INV-2026-005`). Run the workflow. Verify:
  - Nodes light up in sequence up to `Validator`, then branch down to `Human Gate`.
  - The workflow pauses at `Human Gate` and shows the triage desk.
  - Click **Reject Invoice**. Verify:
    - The workflow resumes and finishes at `Poster` (showing "Posting Aborted").
    - The nodes are colored appropriately.
    - The polling stops, and the user **can select another invoice** from the left panel.
