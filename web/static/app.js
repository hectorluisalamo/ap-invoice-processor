let activeSessionId = null;
let pollInterval = null;
let lastRenderedTrailLen = -1; // only re-render/auto-scroll the audit trail when a step is actually added
let currentInvoice = null;

// Playback animation state
let currentTrail = [];
let currentStatus = 'idle';
let currentPausedAtGate = false;
let currentInvoiceState = null;
let playbackIndex = 0;
let playbackTimeout = null;

document.addEventListener('DOMContentLoaded', () => {
    fetchInvoices();

    document.getElementById('btn-approve').addEventListener('click', () => submitTriage('approved'));
    document.getElementById('btn-reject').addEventListener('click', () => submitTriage('rejected'));
    document.getElementById('btn-run-custom').addEventListener('click', startCustomWorkflowRun);
});

async function fetchInvoices() {
    try {
        const res = await fetch('/api/invoices');
        const invoices = await res.json();
        renderInvoiceList(invoices);
    } catch (e) {
        console.error('Error fetching invoices:', e);
    }
}

function renderInvoiceList(invoices) {
    const container = document.getElementById('invoice-list');
    container.innerHTML = '';

    invoices.forEach(inv => {
        const card = document.createElement('div');
        card.className = 'invoice-item-card';
        card.id = `inv-card-${inv.id}`;

        const typeLabel = inv.test_case_type.replace(/_/g, ' ');

        card.innerHTML = `
            <div class="inv-card-top">
                <span>${inv.id}</span>
                <span>$${inv.ground_truth.total_amount.toFixed(2)}</span>
            </div>
            <div class="inv-card-vendor">${inv.ground_truth.vendor_name}</div>
            <span class="inv-card-type type-${inv.test_case_type}">${typeLabel}</span>
        `;

        card.addEventListener('click', () => selectInvoice(inv));
        container.appendChild(card);
    });
}

function selectInvoice(inv) {
    currentInvoice = inv;
    document.querySelectorAll('.invoice-item-card').forEach(c => c.classList.remove('active'));
    document.getElementById(`inv-card-${inv.id}`).classList.add('active');

    const detailsCard = document.getElementById('invoice-details-card');
    detailsCard.innerHTML = `
        <h3 style="margin-bottom: 8px;">Selected Payload: ${inv.id}</h3>
        <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">${inv.description}</p>
        <pre style="background: rgba(0,0,0,0.3); padding: 12px; border-radius: 6px; font-family: var(--font-mono); font-size: 11px; white-space: pre-wrap;">${inv.raw_text}</pre>
        <button id="btn-start-run" class="btn btn-run">⚡ Run ADK Workflow Graph</button>
    `;

    document.getElementById('btn-start-run').addEventListener('click', () => startWorkflowRun(inv.id));
}

async function startWorkflowRun(invoiceId) {
    resetWorkflowUI();
    updateStatusBadge('running', 'Processing...');

    // Reset playback animation states
    currentTrail = [];
    currentStatus = 'running';
    currentPausedAtGate = false;
    currentInvoiceState = null;
    playbackIndex = 0;
    lastRenderedTrailLen = -1;
    if (playbackTimeout) {
        clearTimeout(playbackTimeout);
        playbackTimeout = null;
    }

    try {
        const res = await fetch('/api/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ invoice_id: invoiceId })
        });
        const data = await res.json();
        activeSessionId = data.session_id;

        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(pollSessionState, 800);

        // Start playback animation loop
        playNextStep();
    } catch (e) {
        console.error('Error starting run:', e);
        updateStatusBadge('idle', 'Error');
    }
}

async function startCustomWorkflowRun() {
    const vendor = document.getElementById('custom-vendor').value.trim();
    const amountRaw = document.getElementById('custom-amount').value.trim();
    const po = document.getElementById('custom-po').value.trim();
    const lineItem = document.getElementById('custom-line-item').value.trim();
    const errorBox = document.getElementById('custom-error');

    const amount = parseFloat(amountRaw);
    if (!vendor || !lineItem || !amountRaw || isNaN(amount) || amount <= 0) {
        errorBox.innerText = 'Vendor name, a positive total amount, and a line-item description are required.';
        errorBox.classList.remove('hidden');
        return;
    }
    errorBox.classList.add('hidden');

    // Deselect any pre-baked card so the UI reflects the custom run.
    document.querySelectorAll('.invoice-item-card').forEach(c => c.classList.remove('active'));
    currentInvoice = null;

    resetWorkflowUI();
    updateStatusBadge('running', 'Processing...');

    // Reset playback animation states
    currentTrail = [];
    currentStatus = 'running';
    currentPausedAtGate = false;
    currentInvoiceState = null;
    playbackIndex = 0;
    lastRenderedTrailLen = -1;
    if (playbackTimeout) {
        clearTimeout(playbackTimeout);
        playbackTimeout = null;
    }

    try {
        const res = await fetch('/api/run-custom', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                vendor_name: vendor,
                total_amount: amount,
                po_number: po || null,
                line_item_description: lineItem
            })
        });
        const data = await res.json();
        activeSessionId = data.session_id;

        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(pollSessionState, 800);

        // Start playback animation loop
        playNextStep();
    } catch (e) {
        console.error('Error starting custom run:', e);
        updateStatusBadge('idle', 'Error');
    }
}

async function pollSessionState() {
    if (!activeSessionId) return;

    try {
        const res = await fetch(`/api/sessions/${activeSessionId}`);
        if (!res.ok) {
            console.warn(`Stopping poll because session endpoint returned status ${res.status}`);
            if (pollInterval) {
                clearInterval(pollInterval);
                pollInterval = null;
            }
            activeSessionId = null;
            return;
        }
        const state = await res.json();

        currentStatus = state.status;
        currentPausedAtGate = state.is_paused_at_gate;
        if (state.invoice_state) {
            currentInvoiceState = state.invoice_state;
            currentTrail = state.invoice_state.decision_trail || [];
        }
    } catch (e) {
        console.error('Error polling session:', e);
        if (pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
        activeSessionId = null;
    }
}

function playNextStep() {
    if (!activeSessionId) return;

    if (playbackIndex < currentTrail.length) {
        const step = currentTrail[playbackIndex];

        // Determine visited nodes and active node
        const visitedNodes = new Set();
        for (let i = 0; i < playbackIndex; i++) {
            visitedNodes.add(currentTrail[i].node_name);
        }
        const activeNode = step.node_name;

        // Update pipeline layout
        updatePipelineVisualizer(visitedNodes, activeNode, false);

        // Update the audit trail up to this step
        renderAuditTrail(currentTrail.slice(0, playbackIndex + 1));

        // Render intermediate live details
        renderLiveDetailsForStep(playbackIndex);

        playbackIndex++;
        playbackTimeout = setTimeout(playNextStep, 600);
    } else {
        // Caught up with actual polled trail. Check if we need to wait or finish.
        if (currentPausedAtGate) {
            updateStatusBadge('paused', 'Paused at Human Gate');
            showTriageDesk(currentInvoiceState);

            // Highlight Human Gate as active
            const visitedNodes = new Set(currentTrail.map(s => s.node_name));
            visitedNodes.delete('Human Gate');
            updatePipelineVisualizer(visitedNodes, 'Human Gate', false);

            if (pollInterval) {
                clearInterval(pollInterval);
                pollInterval = null;
            }
        } else if (currentStatus === 'completed' || currentStatus === 'aborted' || currentStatus === 'error') {
            // End of workflow reached!
            const visitedNodes = new Set(currentTrail.map(s => s.node_name));
            updatePipelineVisualizer(visitedNodes, null, true);

            // Render final trail and details
            renderAuditTrail(currentTrail);
            renderLiveDetails(currentInvoiceState);

            if (currentStatus === 'completed') {
                updateStatusBadge('completed', 'Completed & Posted');
            } else if (currentStatus === 'aborted') {
                updateStatusBadge('aborted', 'Posting Aborted');
                const badge = document.getElementById('session-status-badge');
                if (badge) {
                    badge.className = 'status-badge paused'; // Red/Warning badge
                }
            } else {
                updateStatusBadge('idle', 'Error');
            }

            // Clear intervals and timeouts
            if (pollInterval) {
                clearInterval(pollInterval);
                pollInterval = null;
            }
            activeSessionId = null;
        } else {
            // Workflow still running, wait for more steps
            playbackTimeout = setTimeout(playNextStep, 200);
        }
    }
}

function updatePipelineVisualizer(visitedNodes, activeNode, isFinal) {
    const nodes = ['Intake', 'Extractor', 'GL-Coder', 'Policy-Validator', 'Human Gate', 'Poster'];

    nodes.forEach(nodeName => {
        const elem = document.getElementById(`node-${nodeName}`);
        if (!elem) return;

        elem.classList.remove('active', 'completed');
        if (nodeName === activeNode) {
            elem.classList.add('active');
        } else if (visitedNodes.has(nodeName)) {
            elem.classList.add('completed');
        }
    });

    const conn1 = document.getElementById('conn-1');
    const conn2 = document.getElementById('conn-2');
    const conn3 = document.getElementById('conn-3');
    const connBypass = document.getElementById('conn-bypass');
    const connBranchLeft = document.getElementById('conn-branch-left');
    const connBranchRight = document.getElementById('conn-branch-right');

    const toggleClass = (elem, stateClass) => {
        if (!elem) return;
        elem.classList.remove('active', 'completed');
        if (stateClass) elem.classList.add(stateClass);
    };

    // conn-1 (Intake -> Extractor)
    if (visitedNodes.has('Extractor')) toggleClass(conn1, 'completed');
    else if (activeNode === 'Extractor') toggleClass(conn1, 'active');
    else toggleClass(conn1, null);

    // conn-2 (Extractor -> GL-Coder)
    if (visitedNodes.has('GL-Coder')) toggleClass(conn2, 'completed');
    else if (activeNode === 'GL-Coder') toggleClass(conn2, 'active');
    else toggleClass(conn2, null);

    // conn-3 (GL-Coder -> Policy-Validator)
    if (visitedNodes.has('Policy-Validator')) toggleClass(conn3, 'completed');
    else if (activeNode === 'Policy-Validator') toggleClass(conn3, 'active');
    else toggleClass(conn3, null);

    // conn-bypass (Validator -> Poster bypass)
    const isBypassPath = visitedNodes.has('Policy-Validator') && !visitedNodes.has('Human Gate') && activeNode !== 'Human Gate';
    if (isBypassPath) {
        if (visitedNodes.has('Poster')) toggleClass(connBypass, 'completed');
        else if (activeNode === 'Poster') toggleClass(connBypass, 'active');
        else toggleClass(connBypass, null);
    } else {
        toggleClass(connBypass, null);
    }

    // conn-branch-left (Validator -> Human Gate)
    if (visitedNodes.has('Human Gate')) toggleClass(connBranchLeft, 'completed');
    else if (activeNode === 'Human Gate') toggleClass(connBranchLeft, 'active');
    else toggleClass(connBranchLeft, null);

    // conn-branch-right (Human Gate -> Poster)
    if (visitedNodes.has('Human Gate')) {
        if (visitedNodes.has('Poster')) toggleClass(connBranchRight, 'completed');
        else if (activeNode === 'Poster') toggleClass(connBranchRight, 'active');
        else toggleClass(connBranchRight, null);
    } else {
        toggleClass(connBranchRight, null);
    }
}

function showTriageDesk(invoiceState) {
    const desk = document.getElementById('triage-desk');
    desk.classList.remove('hidden');

    const flagsContainer = document.getElementById('triage-flags-list');
    flagsContainer.innerHTML = '';

    if (invoiceState && invoiceState.validation_flags) {
        const flags = invoiceState.validation_flags;
        const list = [];
        if (flags.duplicate_found) list.push('Duplicate Invoice');
        if (flags.exceeds_auto_post_ceiling) list.push('Exceeds $5,000 Ceiling');
        if (flags.low_confidence_fields) list.push('Low Confidence Fields');
        if (flags.unknown_vendor) list.push('Unknown Vendor');
        if (!flags.po_matched) list.push('PO Mismatch');

        list.forEach(flag => {
            const span = document.createElement('span');
            span.className = 'flag-chip';
            span.innerText = `⚠️ ${flag}`;
            flagsContainer.appendChild(span);
        });
    }
}

function hideTriageDesk() {
    document.getElementById('triage-desk').classList.add('hidden');
}

async function submitTriage(decision) {
    if (!activeSessionId) return;

    const reasoning = document.getElementById('triage-reason').value;
    try {
        hideTriageDesk();
        updateStatusBadge('running', 'Resuming Workflow...');

        // Re-start polling and playback since it was cleared when we paused at human gate
        currentStatus = 'running';
        currentPausedAtGate = false;

        await fetch(`/api/sessions/${activeSessionId}/triage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ decision, reasoning })
        });

        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(pollSessionState, 800);

        if (playbackTimeout) clearTimeout(playbackTimeout);
        playNextStep();
    } catch (e) {
        console.error('Error submitting triage:', e);
    }
}

function renderAuditTrail(trail) {
    const container = document.getElementById('audit-trail-container');
    document.getElementById('trail-count').innerText = `${trail.length} Steps`;

    // Only re-render when the step count changes, so the poll doesn't interrupt manual scrolling.
    if (trail.length === lastRenderedTrailLen) return;
    const trailGrew = trail.length > lastRenderedTrailLen;
    lastRenderedTrailLen = trail.length;

    if (trail.length === 0) {
        container.innerHTML = '<div class="empty-trail">No active workflow trail.</div>';
        return;
    }

    container.innerHTML = '';
    trail.forEach(step => {
        const div = document.createElement('div');
        div.className = 'trail-step-item';
        div.innerHTML = `
            <div class="trail-step-header">
                <span class="trail-step-node">Step ${step.step_index}: ${step.node_name}</span>
                <span style="font-size: 11px; color: var(--text-muted);">${step.confidence ? (step.confidence * 100).toFixed(0) + '% Conf' : ''}</span>
            </div>
            <div class="trail-step-desc"><strong>${step.action}</strong></div>
            <div class="trail-step-reason">${step.reasoning}</div>
        `;
        container.appendChild(div);
    });
    // Follow to the newest step only when a step was actually added — never fight a manual scroll.
    if (trailGrew) container.scrollTop = container.scrollHeight;
}

function renderLiveDetails(state) {
    if (!state) return;
    const card = document.getElementById('invoice-details-card');
    let postedBadge = '';

    if (state.posted_entry_id) {
        postedBadge = `<div style="background: rgba(16, 185, 129, 0.2); border: 1px solid var(--success-green); color: var(--success-green); padding: 10px; border-radius: 6px; font-weight: 700; margin-top: 12px;">🏦 NetSuite Posted Transaction: ${state.posted_entry_id}</div>`;
    } else if (state.human_decision === 'rejected') {
        postedBadge = `<div style="background: rgba(239, 68, 68, 0.2); border: 1px solid var(--danger-red); color: var(--danger-red); padding: 10px; border-radius: 6px; font-weight: 700; margin-top: 12px;">❌ Posting Aborted: Human Rejected Entry</div>`;
    }

    let glSummary = '';
    if (state.extracted_fields && state.extracted_fields.line_items) {
        glSummary = state.extracted_fields.line_items.map(item => `
            <div style="font-size: 12px; display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <span>${item.description} ($${item.amount.toFixed(2)})</span>
                <span style="font-family: var(--font-mono); color: var(--accent-cyan);">GL ${item.gl_account || 'Pending'} (${item.department || ''})</span>
            </div>
        `).join('');
    }

    card.innerHTML = `
        <h3 style="margin-bottom: 8px;">Live Shared State: ${state.invoice_id}</h3>
        <div style="font-size: 13px; margin-bottom: 8px;">Vendor: <strong>${state.extracted_fields.vendor_name || 'N/A'}</strong> | Total: <strong>$${state.extracted_fields.total_amount ? state.extracted_fields.total_amount.toFixed(2) : '0.00'}</strong></div>
        <div style="margin-top: 12px;">
            <h4 style="font-size: 12px; color: var(--text-muted); margin-bottom: 6px;">GL Coded Line Items:</h4>
            ${glSummary}
        </div>
        ${postedBadge}
    `;
}

function renderLiveDetailsForStep(stepIndex) {
    if (!currentInvoiceState) return;

    const card = document.getElementById('invoice-details-card');

    // Find what steps have been completed up to stepIndex
    const processedNodes = new Set();
    for (let i = 0; i <= stepIndex; i++) {
        if (currentTrail[i]) {
            processedNodes.add(currentTrail[i].node_name);
        }
    }

    let postedBadge = '';
    if (processedNodes.has('Poster')) {
        if (currentInvoiceState.posted_entry_id) {
            postedBadge = `<div style="background: rgba(16, 185, 129, 0.2); border: 1px solid var(--success-green); color: var(--success-green); padding: 10px; border-radius: 6px; font-weight: 700; margin-top: 12px;">🏦 NetSuite Posted Transaction: ${currentInvoiceState.posted_entry_id}</div>`;
        } else if (currentInvoiceState.human_decision === 'rejected') {
            postedBadge = `<div style="background: rgba(239, 68, 68, 0.2); border: 1px solid var(--danger-red); color: var(--danger-red); padding: 10px; border-radius: 6px; font-weight: 700; margin-top: 12px;">❌ Posting Aborted: Human Rejected Entry</div>`;
        }
    }

    let glSummary = '';
    if (processedNodes.has('GL-Coder') && currentInvoiceState.extracted_fields && currentInvoiceState.extracted_fields.line_items) {
        glSummary = currentInvoiceState.extracted_fields.line_items.map(item => `
            <div style="font-size: 12px; display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <span>${item.description} ($${item.amount.toFixed(2)})</span>
                <span style="font-family: var(--font-mono); color: var(--accent-cyan);">GL ${item.gl_account || 'Pending'} (${item.department || ''})</span>
            </div>
        `).join('');
    } else if (currentInvoiceState.extracted_fields && currentInvoiceState.extracted_fields.line_items) {
        glSummary = currentInvoiceState.extracted_fields.line_items.map(item => `
            <div style="font-size: 12px; display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <span>${item.description} ($${item.amount.toFixed(2)})</span>
                <span style="font-family: var(--font-mono); color: var(--text-muted);">GL Pending</span>
            </div>
        `).join('');
    }

    const vendor = processedNodes.has('Extractor') ? (currentInvoiceState.extracted_fields.vendor_name || 'N/A') : 'Parsing...';
    const total = processedNodes.has('Extractor') ? `$${currentInvoiceState.extracted_fields.total_amount ? currentInvoiceState.extracted_fields.total_amount.toFixed(2) : '0.00'}` : 'Calculating...';

    card.innerHTML = `
        <h3 style="margin-bottom: 8px;">Live Shared State: ${currentInvoiceState.invoice_id}</h3>
        <div style="font-size: 13px; margin-bottom: 8px;">Vendor: <strong>${vendor}</strong> | Total: <strong>${total}</strong></div>
        <div style="margin-top: 12px;">
            <h4 style="font-size: 12px; color: var(--text-muted); margin-bottom: 6px;">GL Coded Line Items:</h4>
            ${glSummary}
        </div>
        ${postedBadge}
    `;
}

function updateStatusBadge(type, text) {
    const badge = document.getElementById('session-status-badge');
    if (badge) {
        badge.className = `status-badge ${type}`;
        badge.innerText = text;
    }
}

function resetWorkflowUI() {
    document.querySelectorAll('.node-step').forEach(n => n.classList.remove('active', 'completed'));
    document.querySelectorAll('.pipeline-connector').forEach(c => c.classList.remove('active', 'completed'));
    document.querySelectorAll('.branch-connector').forEach(c => c.classList.remove('active', 'completed'));
    hideTriageDesk();
}
