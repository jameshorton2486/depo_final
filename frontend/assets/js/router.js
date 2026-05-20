async function loadStage(stageId) {
    const screenRoot = document.getElementById('screenRoot');
    if (!SCREEN_FILES[stageId]) {
        screenRoot.innerHTML = '<p>Unknown stage.</p>';
        return;
    }
    screenRoot.setAttribute('aria-busy', 'true');
    showNotification(`Loading Stage ${stageId}...`, 'working');

    let html = appState.screenCache[stageId];
    if (!html) {
        const response = await fetch(SCREEN_FILES[stageId]);
        if (!response.ok) {
            throw new Error(`Failed to load ${SCREEN_FILES[stageId]}`);
        }
        html = await response.text();
        appState.screenCache[stageId] = html;
    }

    appState.currentStage = stageId;
    appState.currentCaseStage = stageId;
    persistState();
    screenRoot.innerHTML = html;
    renderStageNav();
    renderPipeline();
    updateWorkspaceHeader();
    screenRoot.setAttribute('aria-busy', 'false');

    const module = SCREEN_MODULES[stageId];
    if (module && typeof module.init === 'function') {
        module.init();
    }
    if (appState.currentCaseId) {
        try {
            const persisted = await persistCaseStage(appState.currentCaseId, stageId);
            appState.currentCaseState = persisted.case_state || appState.currentCaseState;
            renderPipeline();
            renderTranscriptLayersPanel();
        } catch (error) {
            console.error(error);
        }
    }
    showNotification(`Stage ${stageId} ready.`, 'success');
}

async function bootstrapApp() {
    applyTheme();
    bindGlobalUi();
    renderStageNav();
    renderPipeline();
    updateWorkspaceHeader();

    try {
        await fetchHealth();
        const systemHealth = await fetchSystemHealth();
        updateSystemHealthBadge(systemHealth);
        if (appState.currentCaseId) {
            const intake = await fetchIntake(appState.currentCaseId);
            appState.currentCaseState = intake.case_state || null;
            appState.currentCaseStage = intake.case_state?.stage_id || appState.currentCaseStage;
            if (intake.case_state?.latest_session_id) {
                appState.currentSessionId = intake.case_state.latest_session_id;
            }
            if (appState.currentCaseStage) {
                appState.currentStage = appState.currentCaseStage;
            }
            persistState();
        }
        await refreshSystemPanels();
    } catch (error) {
        console.error(error);
        showNotification(error.message, 'error');
    }

    await loadStage(appState.currentStage);
}

window.addEventListener('DOMContentLoaded', () => {
    bootstrapApp().catch((error) => {
        const screenRoot = document.getElementById('screenRoot');
        screenRoot.innerHTML = `<div class="placeholder-card"><h4>Startup error</h4><p>${error.message}</p></div>`;
    });
});
