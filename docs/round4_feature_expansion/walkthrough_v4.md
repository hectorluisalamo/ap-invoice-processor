# Walkthrough: Branched Graph, Sequential Animation & UI Lockout Fix

This document summarizes the changes made to the accounts payable invoice processor dashboard to resolve all requested issues.

## Accomplishments

1. **Non-Linear Branched Node Graph (Grid Fork)**
   - Converted the `.pipeline-visualizer` container in [style.css](../../web/static/style.css) to a two-row, eleven-column CSS Grid.
   - Positioned the standard nodes (`Intake`, `Extractor`, `GL-Coder`, `Validator`, `Poster`) along Row 1.
   - Placed the `Human Gate` node on Row 2, centered under the main line.
   - Created L-shaped branch connector lines (`#conn-branch-left`, `#conn-branch-right`) to draw paths leading to and from the Human Gate.
   - Introduced a dashed `#conn-bypass` line labeled "Auto-Post" to represent the direct path.
   - **Cache-Busting & Fallback order:** Swapped the HTML declaration order so that the `Human Gate` elements are declared *before* the `Poster` element. If the browser caches the old CSS and falls back to a linear layout, it logically renders as `Validator -> Human Gate -> Poster` (instead of the backwards `Poster -> Human Gate`). Added `?v=2.1` query version parameters to the stylesheet and script links to force cache clearing.

2. **Sequential Lighting Animation (Path Visualization)**
   - Implemented a playback queue in [app.js](../../web/static/app.js) that animates the workflow node-by-node with a 600ms delay.
   - Highlighted the active node and the specific connector paths (bypass vs. human gate) as they execute.
   - Dynamically evolved the live shared state card (e.g. showing "Parsing..." and "GL Pending" and then filling them in as the corresponding playback node lights up).

3. **UI Selection Lockout Fix**
   - Correctly terminated the uvicorn polling interval when a session reaches an `'aborted'` (rejected) or `'error'` final state.
   - Released the UI controls, allowing users to immediately click and run any other invoice on the left-hand panel after a triage rejection.
   - **Polling Robustness:** Clears the polling interval immediately if the server returns a non-200 status (like `404 Not Found` when uvicorn restarts and clears the session memory) or if a network error occurs. This prevents stale browser tabs from infinitely polling uvicorn.

---

## How to Verify Locally

1. **Launch the Server:**
   ```bash
   PYTHONPATH=. uvicorn web.server:web_app --reload --port 8000
   ```

2. **Test Scenario A: Auto-Post (No Human Intervention)**
   - Select `INV-2026-001` (Type: `clean auto post`).
   - Click **Run ADK Workflow Graph**.
   - **Observation:** The nodes light up in sequence (`Intake` -> `Extractor` -> `GL-Coder` -> `Validator` -> `Poster`). The dashed `Auto-Post` line lights up, while the `Human Gate` remains faded.

3. **Test Scenario B: Human Review & Rejection**
   - Select `INV-2026-005` (Type: `high dollar ceiling`).
   - Click **Run ADK Workflow Graph**.
   - **Observation:** Nodes light up to `Validator`, then the branch line leads down to `Human Gate` and pauses.
   - Click **Reject Invoice**.
   - **Observation:** The animation resumes and terminates at `Poster`, highlighting the aborted state.
   - Immediately click `INV-2026-003` or another invoice on the left panel. It should successfully select the invoice details card and not get reverted.
