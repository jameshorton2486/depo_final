async function loadStage(stageId) {
    const screenRoot = document.getElementById('screenRoot');
    if (!SCREEN_FILES[stageId]) {
        screenRoot.innerHTML = '<p>Unknown stage.</p>';
        return;
    }

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
    persistState();
    screenRoot.innerHTML = html;
    renderStageNav();
    renderPipeline();
    updateWorkspaceHeader();

    const module = SCREEN_MODULES[stageId];
    if (module && typeof module.init === 'function') {
        module.init();
    }
}

async function bootstrapApp() {
    applyTheme();
    bindGlobalUi();
    renderStageNav();
    renderPipeline();
    updateWorkspaceHeader();

    try {
        await fetchHealth();
    } catch (error) {
        console.error(error);
    }

    await loadStage(appState.currentStage);
}

window.addEventListener('DOMContentLoaded', () => {
    bootstrapApp().catch((error) => {
        const screenRoot = document.getElementById('screenRoot');
        screenRoot.innerHTML = `<div class="placeholder-card"><h4>Startup error</h4><p>${error.message}</p></div>`;
    });
});
