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
    summary.textContent = `${appState.currentStage} of ${STAGES.length}`;
    indicator.innerHTML = STAGES.map(
        (stage) => `
        <div class="pipeline-step${stage.id === appState.currentStage ? ' active' : ''}">
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
}
