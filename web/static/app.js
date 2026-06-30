let activeSessionId = null;
let pollInterval = null;
let lastRenderedTrailLen = -1; // only re-render/auto-scroll the audit trail when a step is actually added
let currentInvoice = null;

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

    try {
        const res = await fetch('/api/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ invoice_id: invoiceId })
        });
        const data = await res.json();
        activeSessionId = data.session_id;

        lastRenderedTrailLen = -1; // reset so the new run's trail renders from scratch
        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(pollSessionState, 800);
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

        lastRenderedTrailLen = -1; // reset so the new run's trail renders from scratch
        if (pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(pollSessionState, 800);
    } catch (e) {
        console.error('Error starting custom run:', e);
        updateStatusBadge('idle', 'Error');
    }
}

async function pollSessionState() {
    if (!activeSessionId) return;

    try {
        const res = await fetch(`/api/sessions/${activeSessionId}`);
        const state = await res.json();

        updatePipelineVisualizer(state.current_node, state.status);
        
        if (state.invoice_state) {
            renderAuditTrail(state.invoice_state.decision_trail || []);
            renderLiveDetails(state.invoice_state);
        }

        if (state.is_paused_at_gate) {
            updateStatusBadge('paused', 'Paused at Human Gate');
            showTriageDesk(state.invoice_state);
        } else {
            hideTriageDesk();
            if (state.status === 'completed') {
                updateStatusBadge('completed', 'Completed & Posted');
                clearInterval(pollInterval);
            }
        }
    } catch (e) {
        console.error('Error polling session:', e);
    }
}

function updatePipelineVisualizer(currentNode, status) {
    const nodes = ['Intake', 'Extractor', 'GL-Coder', 'Policy-Validator', 'Human Gate', 'Poster'];
    const currentIndex = nodes.indexOf(currentNode);

    nodes.forEach((nodeName, index) => {
        const elem = document.getElementById(`node-${nodeName}`);
        if (!elem) return;

        elem.classList.remove('active', 'completed');
        if (index < currentIndex || status === 'completed') {
            elem.classList.add('completed');
        } else if (index === currentIndex) {
            elem.classList.add('active');
        }
    });
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
        await fetch(`/api/sessions/${activeSessionId}/triage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ decision, reasoning })
        });
        hideTriageDesk();
        updateStatusBadge('running', 'Resuming Workflow...');
    } catch (e) {
        console.error('Error submitting triage:', e);
    }
}

function renderAuditTrail(trail) {
    const container = document.getElementById('audit-trail-container');
    document.getElementById('trail-count').innerText = `${trail.length} Steps`;

    // Only re-render when the step count changes, so the 800ms poll doesn't interrupt manual scrolling.
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

function updateStatusBadge(type, text) {
    const badge = document.getElementById('session-status-badge');
    badge.className = `status-badge ${type}`;
    badge.innerText = text;
}

function resetWorkflowUI() {
    document.querySelectorAll('.node-step').forEach(n => n.classList.remove('active', 'completed'));
    hideTriageDesk();
}
