window.stage4Module = {
    init() {
        document.title = 'DEPO-PRO | Legal Review';
        initializeLegalReviewState();
        bindLegalReviewEvents();
        if (appState.currentSessionId) {
            loadLegalReview(appState.currentSessionId).catch(console.error);
        }
    },
};

function initializeLegalReviewState() {
    document.getElementById('legalReviewSessionId').value = appState.currentSessionId || '';
    document.getElementById('legalReviewAuthor').value = appState.workspaceReviewer || '';
}

function bindLegalReviewEvents() {
    document
        .getElementById('legalReviewLoadButton')
        .addEventListener('click', handleLegalReviewLoad);
    document
        .getElementById('annotationCreateButton')
        .addEventListener('click', handleAnnotationCreate);
    document
        .getElementById('objectionCreateButton')
        .addEventListener('click', handleObjectionCreate);
    document.getElementById('exhibitLinkButton').addEventListener('click', handleExhibitLink);
}

async function handleLegalReviewLoad() {
    const sessionId = Number(
        document.getElementById('legalReviewSessionId').value || appState.currentSessionId,
    );
    if (!sessionId) {
        updateLegalReviewStatus('A session id is required.', 'error');
        return;
    }
    await loadLegalReview(sessionId);
}

async function loadLegalReview(sessionId) {
    updateLegalReviewStatus(
        `Loading legal review workspace for session ${sessionId}...`,
        'working',
    );
    const [timelinePayload, dashboardPayload, navigationPayload] = await Promise.all([
        fetchTranscriptTimeline(sessionId),
        fetchReviewDashboard(sessionId),
        fetchReviewNavigation(sessionId),
    ]);
    appState.currentSessionId = sessionId;
    persistState();
    renderLegalReviewDashboard(dashboardPayload.counts || {});
    renderLegalNavigation(navigationPayload.items || []);
    renderLegalAnnotations(dashboardPayload.annotations || []);
    renderLegalObjections(dashboardPayload.objections || []);
    renderLegalExhibits(dashboardPayload.linked_exhibits || []);
    renderLegalInterpreted(dashboardPayload.interpreted_segments || []);
    renderLegalIssues(dashboardPayload.issues || []);
    seedBlockIds(timelinePayload.timeline || []);
    updateLegalReviewStatus(`Legal review loaded for session ${sessionId}`, 'success');
}

function seedBlockIds(blocks) {
    const firstBlockId = blocks[0]?.id || '';
    if (!document.getElementById('annotationBlockId').value) {
        document.getElementById('annotationBlockId').value = firstBlockId;
    }
    if (!document.getElementById('objectionBlockId').value) {
        document.getElementById('objectionBlockId').value = firstBlockId;
    }
    if (!document.getElementById('exhibitBlockId').value) {
        document.getElementById('exhibitBlockId').value = firstBlockId;
    }
}

async function handleAnnotationCreate() {
    const payload = {
        session_id: Number(document.getElementById('legalReviewSessionId').value),
        transcript_block_id: Number(document.getElementById('annotationBlockId').value),
        annotation_type: document.getElementById('annotationType').value.trim() || 'BOOKMARK',
        annotation_text: document.getElementById('annotationText').value.trim(),
        bookmark_label: document.getElementById('annotationBookmarkLabel').value.trim() || null,
        issue_category: document.getElementById('annotationIssueCategory').value.trim() || null,
        author: document.getElementById('legalReviewAuthor').value.trim(),
    };
    await createReviewAnnotation(payload);
    await loadLegalReview(payload.session_id);
}

async function handleObjectionCreate() {
    const payload = {
        session_id: Number(document.getElementById('legalReviewSessionId').value),
        transcript_block_id: Number(document.getElementById('objectionBlockId').value),
        category: document.getElementById('objectionCategory').value.trim() || 'FORM',
        objection_text: document.getElementById('objectionText').value.trim(),
        reviewer: document.getElementById('legalReviewAuthor').value.trim(),
    };
    await createReviewObjection(payload);
    await loadLegalReview(payload.session_id);
}

async function handleExhibitLink() {
    const payload = {
        session_id: Number(document.getElementById('legalReviewSessionId').value),
        transcript_block_id: Number(document.getElementById('exhibitBlockId').value),
        exhibit_label: document.getElementById('exhibitLabel').value.trim(),
        exhibit_description: document.getElementById('exhibitDescription').value.trim() || null,
        created_by: document.getElementById('legalReviewAuthor').value.trim(),
    };
    await createReviewExhibitLink(payload);
    await loadLegalReview(payload.session_id);
}

function renderLegalReviewDashboard(counts) {
    document.getElementById('legalReviewDashboardGrid').innerHTML =
        legalReviewDashboardView.render(counts);
}

function renderLegalNavigation(items) {
    const target = document.getElementById('legalNavigationList');
    target.innerHTML = legalReviewNavigationView.render(items);
    target.querySelectorAll('[data-nav-block-id]').forEach((button) => {
        button.addEventListener('click', () => {
            const blockId = button.dataset.navBlockId;
            document.getElementById('annotationBlockId').value = blockId;
            document.getElementById('objectionBlockId').value = blockId;
            document.getElementById('exhibitBlockId').value = blockId;
        });
    });
}

function renderLegalAnnotations(items) {
    document.getElementById('legalAnnotationsList').innerHTML =
        legalReviewAnnotations.render(items);
}

function renderLegalObjections(items) {
    document.getElementById('legalObjectionsList').innerHTML = legalReviewObjections.render(items);
}

function renderLegalExhibits(items) {
    document.getElementById('legalExhibitsList').innerHTML = legalReviewExhibitPanel.render(items);
}

function renderLegalInterpreted(items) {
    document.getElementById('legalInterpretedList').innerHTML =
        legalReviewInterpretedView.render(items);
}

function renderLegalIssues(items) {
    document.getElementById('legalIssuesList').innerHTML = legalReviewIssueManagement.render(items);
}

function updateLegalReviewStatus(message, state) {
    const element = document.getElementById('legalReviewStatus');
    element.textContent = message;
    element.dataset.state = state;
}
