const STAGES = [
    { id: 1, key: 'intake', title: 'Intake', description: 'Case intake and source registration' },
    { id: 2, key: 'transcripts', title: 'Transcripts', description: 'Transcript asset intake' },
    { id: 3, key: 'workspace', title: 'Workspace', description: 'Review workspace shell' },
    { id: 4, key: 'insertions', title: 'Insertions', description: 'Corrections and insertions' },
    { id: 5, key: 'certify', title: 'Certify', description: 'Certification preparation' },
    { id: 6, key: 'export', title: 'Export', description: 'Output and delivery' },
];

const SCREEN_FILES = {
    1: 'screens/stage_1_intake.html',
    2: 'screens/stage_2_transcripts.html',
    3: 'screens/stage_3_workspace.html',
    4: 'screens/stage_4_insertions.html',
    5: 'screens/stage_5_certify.html',
    6: 'screens/stage_6_export.html',
};

const SCREEN_MODULES = {
    1: window.stage1Module,
    2: window.stage2Module,
    3: window.stage3Module,
    4: window.stage4Module,
    5: window.stage5Module,
    6: window.stage6Module,
};

const appState = {
    currentStage: Number(window.localStorage.getItem('depo-pro-stage') || 1),
    theme: window.localStorage.getItem('depo-pro-theme') || 'dark',
    currentCaseId: Number(window.localStorage.getItem('depo-pro-case-id') || 0),
    currentSessionId: Number(window.localStorage.getItem('depo-pro-session-id') || 0),
    exportSessionId: Number(window.localStorage.getItem('depo-pro-export-session-id') || 0),
    realtimeMeetingId: window.localStorage.getItem('depo-pro-realtime-meeting-id') || '',
    workspaceSearch: window.localStorage.getItem('depo-pro-workspace-search') || '',
    workspaceReviewer: window.localStorage.getItem('depo-pro-workspace-reviewer') || '',
    reviewSidebarCollapsed: window.localStorage.getItem('depo-pro-review-sidebar') === '1',
    currentCaseStage: Number(window.localStorage.getItem('depo-pro-case-stage') || 1),
    intakeCases: [],
    currentCaseState: null,
    transcriptLayerState: null,
    panelCollapse: (() => {
        try {
            return JSON.parse(window.localStorage.getItem('depo-pro-panel-collapse') || '{}');
        } catch (_error) {
            return {};
        }
    })(),
    screenCache: {},
    health: null,
    systemHealth: null,
    systemDiagnostics: null,
    systemPerformance: null,
    notification: null,
};

function persistState() {
    window.localStorage.setItem('depo-pro-stage', String(appState.currentStage));
    window.localStorage.setItem('depo-pro-theme', appState.theme);
    window.localStorage.setItem('depo-pro-case-id', String(appState.currentCaseId || 0));
    window.localStorage.setItem('depo-pro-session-id', String(appState.currentSessionId || 0));
    window.localStorage.setItem(
        'depo-pro-export-session-id',
        String(appState.exportSessionId || 0),
    );
    window.localStorage.setItem('depo-pro-realtime-meeting-id', appState.realtimeMeetingId || '');
    window.localStorage.setItem('depo-pro-workspace-search', appState.workspaceSearch || '');
    window.localStorage.setItem('depo-pro-workspace-reviewer', appState.workspaceReviewer || '');
    window.localStorage.setItem(
        'depo-pro-review-sidebar',
        appState.reviewSidebarCollapsed ? '1' : '0',
    );
    window.localStorage.setItem('depo-pro-case-stage', String(appState.currentCaseStage || 1));
    window.localStorage.setItem(
        'depo-pro-panel-collapse',
        JSON.stringify(appState.panelCollapse || {}),
    );
}
