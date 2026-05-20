function applyTheme() {
    document.body.dataset.theme = appState.theme;
    persistState();
}

function toggleTheme() {
    appState.theme = appState.theme === 'dark' ? 'light' : 'dark';
    applyTheme();
}

function renderStageNav() {
    const nav = document.getElementById('stageNav');
    nav.innerHTML = STAGES.map(
        (stage) => `
        <button class="stage-button${stage.id === appState.currentStage ? ' active' : ''}" type="button" data-stage="${stage.id}">
            <span class="stage-number">${stage.id}</span>
            <span class="stage-copy">
                <span class="stage-title">${stage.title}</span>
                <span class="stage-meta">${stage.description}</span>
            </span>
            <span class="stage-meta">${String(stage.id).padStart(2, '0')}</span>
        </button>
    `,
    ).join('');

    nav.querySelectorAll('[data-stage]').forEach((button) => {
        button.addEventListener('click', () => loadStage(Number(button.dataset.stage)));
    });
}

function renderPipeline() {
    const indicator = document.getElementById('pipelineIndicator');
    const summary = document.getElementById('pipelineSummary');
    const stageState =
        appState.currentCaseState?.stage_id || appState.currentCaseStage || appState.currentStage;
    summary.textContent = `${stageState} of ${STAGES.length}`;
    indicator.innerHTML = STAGES.map(
        (stage) => `
        <div class="pipeline-step${resolvePipelineClass(stage.id)}">
            <span class="pipeline-dot">${stage.id}</span>
            <span class="stage-meta">${stage.title}</span>
        </div>
    `,
    ).join('');
}

function updateWorkspaceHeader() {
    const current = STAGES.find((stage) => stage.id === appState.currentStage);
    document.getElementById('workspaceTitle').textContent = `Stage ${current.id}: ${current.title}`;
}

function bindGlobalUi() {
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
    const refreshButton = document.getElementById('systemHealthRefresh');
    if (refreshButton) {
        refreshButton.addEventListener('click', () => refreshSystemPanels().catch(console.error));
    }
}

function updateSystemHealthBadge(payload = null) {
    const badge = document.getElementById('systemHealthBadge');
    const summary = document.getElementById('systemHealthSummary');
    if (!badge || !summary) {
        return;
    }
    if (!payload) {
        badge.textContent = 'Health unknown';
        badge.dataset.state = 'idle';
        summary.textContent = 'Diagnostics not loaded yet.';
        return;
    }
    badge.textContent = payload.status === 'ok' ? 'System healthy' : 'Needs review';
    badge.dataset.state = payload.status === 'ok' ? 'success' : 'working';
    summary.textContent = `${payload.session_count || 0} sessions scanned, ${payload.integrity_issue_count || 0} integrity issues.`;
}

async function refreshSystemPanels() {
    const [healthPayload, diagnosticsPayload] = await Promise.all([
        fetchSystemHealth(),
        fetchSystemDiagnostics(appState.currentSessionId || null),
    ]);
    updateSystemHealthBadge(healthPayload);
    const summary = diagnosticsPayload.summary || {};
    appState.transcriptLayerState = {
        raw_status: appState.currentSessionId
            ? 'Persisted transcript present'
            : 'Awaiting transcript',
        working_status: appState.currentStage >= 3 ? 'Review workflow available' : 'Locked',
        review_state: appState.currentCaseState?.review_state || 'pending',
        export_readiness: appState.currentCaseState?.is_export_ready ? 'Ready' : 'Blocked',
        session_count: appState.currentCaseState?.session_count || 0,
        integrity_issue_count: summary.integrity_issue_count || 0,
    };
    renderTranscriptLayersPanel();
    renderSystemHealthDetails(summary);
}

function renderTranscriptLayersPanel() {
    const state = appState.transcriptLayerState || {};
    const summary = document.getElementById('transcriptLayerSummary');
    const target = document.getElementById('transcriptLayerGrid');
    if (!summary || !target) {
        return;
    }
    summary.textContent = appState.currentCaseId
        ? `Case ${appState.currentCaseId}`
        : 'No case loaded.';
    target.innerHTML = `
        <div class="stack-item"><strong>RAW</strong><span>${escapeHtml(state.raw_status || 'Not started')}</span></div>
        <div class="stack-item"><strong>WORKING</strong><span>${escapeHtml(state.working_status || 'Pending')}</span></div>
        <div class="stack-item"><strong>Review</strong><span>${escapeHtml(state.review_state || 'pending')}</span></div>
        <div class="stack-item"><strong>Export</strong><span>${escapeHtml(state.export_readiness || 'Blocked')}</span></div>
        <div class="stack-item"><strong>Sessions</strong><span>${escapeHtml(String(state.session_count || 0))}</span></div>
        <div class="stack-item"><strong>Integrity</strong><span>${escapeHtml(String(state.integrity_issue_count || 0))} issues</span></div>
    `;
}

function renderSystemHealthDetails(summary) {
    const target = document.getElementById('systemHealthDetails');
    if (!target) {
        return;
    }
    target.innerHTML = `
        <div class="stack-item"><strong>Sessions Scanned</strong><span>${escapeHtml(String(summary.sessions_scanned || 0))}</span></div>
        <div class="stack-item"><strong>Orphans</strong><span>${escapeHtml(String(summary.orphan_transcript_count || 0))}</span></div>
        <div class="stack-item"><strong>Missing Assets</strong><span>${escapeHtml(String(summary.missing_asset_count || 0))}</span></div>
        <div class="stack-item"><strong>Export Failures</strong><span>${escapeHtml(String(summary.export_failure_count || 0))}</span></div>
        <div class="stack-item"><strong>Realtime</strong><span>${escapeHtml(summary.realtime_reconnect_count ? 'Warning' : 'Healthy')}</span></div>
        <div class="stack-item"><strong>Database</strong><span>${escapeHtml(summary.database_health || 'Unknown')}</span></div>
    `;
}

function resolvePipelineClass(stageId) {
    const currentStage =
        appState.currentCaseState?.stage_id || appState.currentCaseStage || appState.currentStage;
    if (stageId === currentStage) {
        return ' active';
    }
    if (stageId < currentStage) {
        return ' completed';
    }
    if (stageId === currentStage + 1) {
        return ' available';
    }
    return ' blocked';
}

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

function showNotification(message, state = 'idle') {
    const root = document.getElementById('notificationToast');
    if (!root) {
        return;
    }
    appState.notification = { message, state };
    root.textContent = message;
    root.dataset.state = state;
    root.hidden = false;
    window.clearTimeout(showNotification.timeoutId);
    showNotification.timeoutId = window.setTimeout(() => {
        root.hidden = true;
    }, 3200);
}
