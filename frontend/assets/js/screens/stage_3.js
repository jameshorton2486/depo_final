window.stage3Module = {
    init() {
        document.title = 'DEPO-PRO | Workspace';
        initializeWorkspaceState();
        bindWorkspaceEvents();
        renderWorkspaceSummary();
        if (appState.currentSessionId) {
            loadWorkspaceTimeline(appState.currentSessionId).catch(console.error);
        }
    },
};

const workspaceState = {
    timeline: [],
    playback: null,
    asset: null,
    reviewQueue: [],
    auditItems: [],
    selectedReviewFlagId: null,
    activeWordId: null,
    activeBlockId: null,
    searchMatches: [],
    reviewCandidateWords: [],
    reviewCandidateIndex: -1,
    diagnostics: null,
    performance: null,
    keyboardBound: false,
};

function initializeWorkspaceState() {
    document.getElementById('workspaceSessionId').value = appState.currentSessionId || '';
    document.getElementById('workspaceSearch').value = appState.workspaceSearch || '';
    document.getElementById('workspaceReviewer').value = appState.workspaceReviewer || '';
}

function bindWorkspaceEvents() {
    document.getElementById('workspaceLoadButton').addEventListener('click', handleWorkspaceLoad);
    document
        .getElementById('workspacePrevBlockButton')
        .addEventListener('click', () => navigateBlock(-1));
    document
        .getElementById('workspaceNextBlockButton')
        .addEventListener('click', () => navigateBlock(1));
    document.getElementById('workspaceSearch').addEventListener('input', handleWorkspaceSearch);
    document.getElementById('workspaceJumpTime').addEventListener('change', handleJumpToTime);
    document.getElementById('workspaceJumpSpeaker').addEventListener('change', handleJumpToSpeaker);
    document.getElementById('workspaceReviewer').addEventListener('input', handleReviewerChange);
    document
        .getElementById('workspaceResolveAcceptButton')
        .addEventListener('click', () => resolveSelectedReviewItem('accept'));
    document
        .getElementById('workspaceResolveRejectButton')
        .addEventListener('click', () => resolveSelectedReviewItem('reject'));
    document
        .getElementById('workspaceResolveReviewedButton')
        .addEventListener('click', () => resolveSelectedReviewItem('mark_reviewed'));
    document
        .getElementById('workspaceApplyRuleButton')
        .addEventListener('click', () => resolveSelectedReviewItem('resolve', true));
    document
        .getElementById('workspacePlayPauseButton')
        .addEventListener('click', toggleWorkspacePlayback);
    document
        .getElementById('workspaceSeekBackButton')
        .addEventListener('click', () => seekWorkspacePlayback(-5));
    document
        .getElementById('workspaceSeekForwardButton')
        .addEventListener('click', () => seekWorkspacePlayback(5));
    document
        .getElementById('workspaceToggleReviewButton')
        .addEventListener('click', toggleWorkspaceReviewSidebar);
    bindWorkspaceKeyboardShortcuts();
    applyWorkspaceSidebarState();
}

async function handleWorkspaceLoad() {
    const sessionId = Number(
        document.getElementById('workspaceSessionId').value || appState.currentSessionId,
    );
    if (!sessionId) {
        updateWorkspaceStatus('A session id is required to load the workspace.', 'error');
        return;
    }
    await loadWorkspaceTimeline(sessionId);
}

async function loadWorkspaceTimeline(sessionId) {
    updateWorkspaceStatus(`Loading transcript workspace for session ${sessionId}...`, 'working');
    const [payload, queuePayload, auditPayload, diagnosticsPayload, performancePayload] =
        await Promise.all([
            fetchTranscriptTimeline(sessionId),
            fetchReviewQueue(sessionId),
            fetchReviewAudit(sessionId),
            fetchSystemDiagnostics(sessionId),
            fetchSystemPerformance(sessionId),
        ]);
    appState.currentSessionId = sessionId;
    persistState();

    workspaceState.timeline = payload.timeline || [];
    workspaceState.playback = payload.playback || null;
    workspaceState.asset = payload.asset || null;
    workspaceState.reviewQueue = queuePayload.items || [];
    workspaceState.auditItems = auditPayload.items || [];
    workspaceState.diagnostics = diagnosticsPayload;
    workspaceState.performance = performancePayload;
    workspaceState.selectedReviewFlagId = workspaceState.reviewQueue[0]?.id || null;
    workspaceState.activeWordId = null;
    workspaceState.activeBlockId = workspaceState.timeline[0]?.id || null;

    renderWorkspaceMedia(payload);
    renderWorkspaceSummary(payload);
    renderWorkspaceTranscript(payload.timeline || []);
    renderReviewCandidates(payload.timeline || []);
    renderWorkspaceReviewQueue();
    renderWorkspaceSelectedReviewItem();
    renderWorkspaceSpeakerReview();
    renderWorkspaceAuditHistory();
    renderWorkspaceConfidencePanel(payload.confidence_summary || {});
    renderWorkspaceDiagnostics();
    renderNavigationMeta();
    document.getElementById('workspaceSessionBadge').textContent = `Session ${sessionId}`;
    updateWorkspaceStatus(`Workspace loaded for session ${sessionId}`, 'success');
    showNotification(`Workspace diagnostics refreshed for session ${sessionId}.`, 'success');
}

function renderWorkspaceMedia(payload) {
    const target = document.getElementById('workspaceMediaRoot');
    const mediaUrl = payload?.playback?.media_url;
    if (!mediaUrl || !payload.asset) {
        target.innerHTML = '<p>No media asset is available for this session.</p>';
        return;
    }
    const mediaTag = payload.asset.asset_type === 'video' ? 'video' : 'audio';
    target.innerHTML = `
        <div class="stack-item">
            <strong>${escapeHtml(payload.asset.file_name || 'Transcript media')}</strong>
            <${mediaTag} id="workspaceMediaPlayer" class="media-preview" controls preload="metadata" src="${mediaUrl}"></${mediaTag}>
        </div>
    `;
    const player = document.getElementById('workspaceMediaPlayer');
    player.addEventListener('timeupdate', syncWorkspacePlayback);
}

function renderWorkspaceSummary(payload = null) {
    const confidenceSummary = payload?.confidence_summary || { high: 0, medium: 0, low: 0 };
    const playback = payload?.playback ||
        workspaceState.playback || { duration: 0, word_timeline: [] };
    const rows = [
        renderWorkspaceMetric(
            'Blocks',
            String((payload?.timeline || workspaceState.timeline || []).length),
        ),
        renderWorkspaceMetric('Words', String(playback.word_timeline?.length || 0)),
        renderWorkspaceMetric(
            'Duration',
            transcriptRenderer.formatTimestamp(playback.duration || 0),
        ),
        renderWorkspaceMetric('High Confidence', String(confidenceSummary.high || 0)),
        renderWorkspaceMetric('Medium Confidence', String(confidenceSummary.medium || 0)),
        renderWorkspaceMetric('Low Confidence', String(confidenceSummary.low || 0)),
    ];
    document.getElementById('workspaceSummaryGrid').innerHTML = rows.join('');
}

function renderWorkspaceMetric(label, value) {
    return `
        <div class="result-card summary-metric">
            <p class="panel-label">${escapeHtml(label)}</p>
            <h4>${escapeHtml(value)}</h4>
        </div>
    `;
}

function renderWorkspaceTranscript(blocks) {
    const target = document.getElementById('workspaceTranscriptRoot');
    if (!blocks.length) {
        target.innerHTML =
            '<div class="placeholder-card compact"><p>No transcript timeline is available for this session.</p></div>';
        return;
    }
    target.innerHTML = blocks.map((block) => transcriptRenderer.renderBlock(block)).join('');
    target.querySelectorAll('[data-word-id]').forEach((button) => {
        button.addEventListener('click', () => handleWordSeek(button));
    });
}

function renderWorkspaceReviewQueue() {
    const target = document.getElementById('workspaceReviewQueue');
    target.innerHTML = reviewQueue.render(workspaceState.reviewQueue);
    target.querySelectorAll('[data-flag-id]').forEach((button) => {
        button.addEventListener('click', () => selectReviewItem(Number(button.dataset.flagId)));
    });
}

function renderWorkspaceSelectedReviewItem() {
    const item = getSelectedReviewItem();
    const target = document.getElementById('workspaceSelectedReviewItem');
    if (!item) {
        target.innerHTML = '<p class="muted-copy">No review item selected.</p>';
        return;
    }
    target.innerHTML = `
        <div class="stack-item">
            <strong>${escapeHtml(item.issue_category)}</strong>
            <span>${escapeHtml(item.word_text || item.original_value || 'Review item')}</span>
            <span>${escapeHtml(item.speaker_label || item.block_type || 'Transcript item')}</span>
        </div>
    `;
}

function renderWorkspaceSpeakerReview() {
    const target = document.getElementById('workspaceSpeakerReview');
    target.innerHTML = reviewSpeakerReview.render(getSelectedReviewItem());
    const button = document.getElementById('workspaceSpeakerCorrectionButton');
    if (button) {
        button.addEventListener('click', handleSpeakerCorrection);
    }
}

function renderWorkspaceAuditHistory() {
    document.getElementById('workspaceAuditHistory').innerHTML = reviewAuditHistory.render(
        workspaceState.auditItems,
    );
}

function renderWorkspaceConfidencePanel(summary) {
    document.getElementById('workspaceConfidencePanel').innerHTML =
        reviewConfidencePanel.render(summary);
}

function renderWorkspaceDiagnostics() {
    const diagnostics = workspaceState.diagnostics || {};
    const integrity = diagnostics.integrity || {};
    const assets = diagnostics.assets || {};
    const performanceSession =
        (workspaceState.performance?.sessions || []).find(
            (item) => Number(item.session_id) === Number(appState.currentSessionId),
        ) || null;
    document.getElementById('workspaceSystemBadge').textContent = integrity.ok
        ? 'Integrity OK'
        : `${integrity.issue_count || 0} issues`;
    document.getElementById('workspaceDiagnosticsGrid').innerHTML = [
        renderWorkspaceMetric('Integrity Issues', String(integrity.issue_count || 0)),
        renderWorkspaceMetric('Missing Files', String(assets.missing_file_count || 0)),
        renderWorkspaceMetric('Corrupted JSON', String(assets.corrupted_json_count || 0)),
        renderWorkspaceMetric(
            'Avg Words / Block',
            String(performanceSession?.average_words_per_block || 0),
        ),
        renderWorkspaceMetric('Session Events', String(performanceSession?.event_count || 0)),
        renderWorkspaceMetric(
            'Low Confidence Words',
            String(performanceSession?.low_confidence_words || 0),
        ),
    ].join('');
}

async function handleWordSeek(button) {
    const sessionId = appState.currentSessionId;
    const wordId = Number(button.dataset.wordId);
    const payload = await fetchTranscriptWord(sessionId, wordId);
    const player = document.getElementById('workspaceMediaPlayer');
    transcriptPlaybackSync.seekPlayer(player, Number(payload.seek_time || payload.start_time || 0));
    workspaceState.activeWordId = wordId;
    workspaceState.activeBlockId = Number(button.dataset.blockId);
    renderActivePlaybackState();
    renderNavigationMeta(payload);
    updateWorkspaceStatus(
        `Seeked to ${transcriptRenderer.formatTimestamp(Number(payload.seek_time || 0))}`,
        'success',
    );
    showNotification(
        `Seeked to ${transcriptRenderer.formatTimestamp(Number(payload.seek_time || 0))}`,
        'success',
    );
}

function syncWorkspacePlayback() {
    const player = document.getElementById('workspaceMediaPlayer');
    if (!player || !workspaceState.playback?.word_timeline) {
        return;
    }
    const activeState = transcriptPlaybackSync.activeState(
        workspaceState.playback.word_timeline,
        player.currentTime,
    );
    workspaceState.activeWordId = activeState.activeWordId;
    workspaceState.activeBlockId = activeState.activeBlockId;
    renderActivePlaybackState();
    renderNavigationMeta();
}

function renderActivePlaybackState() {
    document.querySelectorAll('.transcript-word.active').forEach((element) => {
        element.classList.remove('active');
    });
    document.querySelectorAll('.workspace-transcript-block.active-block').forEach((element) => {
        element.classList.remove('active-block');
    });

    if (workspaceState.activeWordId) {
        const activeWord = document.querySelector(
            `[data-word-id="${String(workspaceState.activeWordId)}"]`,
        );
        if (activeWord) {
            activeWord.classList.add('active');
            document.getElementById('workspaceActiveWordBadge').textContent =
                activeWord.textContent.trim();
        }
    } else {
        document.getElementById('workspaceActiveWordBadge').textContent = 'No active word';
    }

    if (workspaceState.activeBlockId) {
        const activeBlock = document.querySelector(
            `[data-block-id="${String(workspaceState.activeBlockId)}"]`,
        );
        if (activeBlock) {
            activeBlock.classList.add('active-block');
            activeBlock.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
    }
}

function handleWorkspaceSearch(event) {
    const query = event.target.value;
    appState.workspaceSearch = query;
    persistState();
    const filtered = transcriptNavigation.filterBlocks(workspaceState.timeline, query);
    workspaceState.searchMatches = filtered.map((block) => block.id);
    renderWorkspaceTranscript(filtered);
    renderReviewCandidates(filtered);
    renderNavigationMeta();
}

function handleReviewerChange(event) {
    appState.workspaceReviewer = event.target.value.trim();
    persistState();
}

function handleJumpToTime(event) {
    const targetTime = Number(event.target.value);
    const block = transcriptNavigation.jumpToTime(workspaceState.timeline, targetTime);
    if (!block) {
        updateWorkspaceStatus('No transcript block matches that time.', 'error');
        return;
    }
    workspaceState.activeBlockId = block.id;
    renderWorkspaceTranscript([block]);
    renderActivePlaybackState();
    updateWorkspaceStatus(`Jumped to ${transcriptRenderer.formatTimestamp(targetTime)}`, 'success');
}

function handleJumpToSpeaker(event) {
    const block = transcriptNavigation.jumpToSpeaker(workspaceState.timeline, event.target.value);
    if (!block) {
        updateWorkspaceStatus('No transcript block matches that speaker label.', 'error');
        return;
    }
    workspaceState.activeBlockId = block.id;
    renderWorkspaceTranscript([block]);
    renderActivePlaybackState();
    updateWorkspaceStatus(`Jumped to ${block.speaker_label || 'speaker'}`, 'success');
}

function navigateBlock(direction) {
    if (!workspaceState.activeBlockId) {
        return;
    }
    const nextBlock = transcriptNavigation.neighborBlock(
        workspaceState.timeline,
        workspaceState.activeBlockId,
        direction,
    );
    if (!nextBlock) {
        return;
    }
    workspaceState.activeBlockId = nextBlock.id;
    renderWorkspaceTranscript(workspaceState.timeline);
    renderActivePlaybackState();
    renderNavigationMeta();
}

function renderReviewCandidates(blocks) {
    const target = document.getElementById('workspaceReviewCandidates');
    const candidates = blocks
        .flatMap((block) =>
            (block.words || [])
                .filter((word) => word.review_candidate)
                .map((word) => ({
                    word,
                    speakerLabel: block.speaker_label,
                })),
        )
        .slice(0, 18);
    workspaceState.reviewCandidateWords = candidates;
    workspaceState.reviewCandidateIndex = candidates.length ? 0 : -1;
    target.innerHTML = candidates.length
        ? candidates
              .map(
                  ({ word, speakerLabel }) => `
                <button class="review-candidate-row" type="button" data-word-id="${word.id}" data-start-time="${word.start_time}">
                    <strong>${escapeHtml(word.word_text)}</strong>
                    <span>${escapeHtml(speakerLabel || 'Speaker')}</span>
                </button>
            `,
              )
              .join('')
        : '<p class="muted-copy">No low-confidence words identified in the current view.</p>';
    target.querySelectorAll('[data-word-id]').forEach((button) => {
        button.addEventListener('click', () => {
            const player = document.getElementById('workspaceMediaPlayer');
            transcriptPlaybackSync.seekPlayer(player, Number(button.dataset.startTime));
            const wordButton = document.querySelector(
                `[data-word-id="${String(button.dataset.wordId)}"]`,
            );
            if (wordButton) {
                wordButton.click();
            }
        });
    });
}

function renderNavigationMeta(wordPayload = null) {
    const activeBlock =
        workspaceState.timeline.find((block) => block.id === workspaceState.activeBlockId) || null;
    const searchCount = workspaceState.searchMatches.length || workspaceState.timeline.length || 0;
    document.getElementById('workspaceNavigationMeta').innerHTML = `
        <div class="stack-item"><strong>Current Block</strong><span>${escapeHtml(activeBlock ? String(activeBlock.block_index) : 'None')}</span></div>
        <div class="stack-item"><strong>Current Speaker</strong><span>${escapeHtml(wordPayload?.speaker_label || activeBlock?.speaker_label || 'None')}</span></div>
        <div class="stack-item"><strong>Search Matches</strong><span>${escapeHtml(String(searchCount))}</span></div>
    `;
}

function selectReviewItem(flagId) {
    workspaceState.selectedReviewFlagId = flagId;
    renderWorkspaceSelectedReviewItem();
    renderWorkspaceSpeakerReview();
    const item = getSelectedReviewItem();
    if (item?.word_object_id) {
        const wordButton = document.querySelector(
            `[data-word-id="${String(item.word_object_id)}"]`,
        );
        if (wordButton) {
            wordButton.click();
        }
    }
}

function getSelectedReviewItem() {
    return (
        workspaceState.reviewQueue.find(
            (item) => item.id === workspaceState.selectedReviewFlagId,
        ) || null
    );
}

async function resolveSelectedReviewItem(action, applyDeterministicRules = false) {
    const item = getSelectedReviewItem();
    const reviewer = String(document.getElementById('workspaceReviewer').value || '').trim();
    if (!item) {
        updateWorkspaceStatus('Select a review item first.', 'error');
        return;
    }
    if (!reviewer) {
        updateWorkspaceStatus(
            'Reviewer identity is required before resolving review items.',
            'error',
        );
        return;
    }
    const note = document.getElementById('workspaceReviewerNote').value.trim() || null;
    await resolveReviewItem({
        session_id: appState.currentSessionId,
        review_flag_id: item.id,
        action,
        reviewer,
        note,
        apply_deterministic_rules: applyDeterministicRules,
    });
    await loadWorkspaceTimeline(appState.currentSessionId);
    updateWorkspaceStatus(`Review item ${item.id} resolved.`, 'success');
    showNotification(`Review item ${item.id} resolved.`, 'success');
}

async function handleSpeakerCorrection() {
    const item = getSelectedReviewItem();
    const reviewer = String(document.getElementById('workspaceReviewer').value || '').trim();
    if (!item) {
        updateWorkspaceStatus('Select a review item first.', 'error');
        return;
    }
    if (!reviewer) {
        updateWorkspaceStatus('Reviewer identity is required before speaker correction.', 'error');
        return;
    }
    const correctedSpeakerLabel =
        document.getElementById('workspaceCorrectedSpeakerLabel')?.value.trim() || '';
    const correctedRole =
        document.getElementById('workspaceCorrectedSpeakerRole')?.value.trim() || null;
    const note = document.getElementById('workspaceReviewerNote').value.trim() || null;
    if (!correctedSpeakerLabel) {
        updateWorkspaceStatus('Corrected speaker label is required.', 'error');
        return;
    }
    await resolveReviewItem({
        session_id: appState.currentSessionId,
        review_flag_id: item.id,
        action: 'resolve',
        reviewer,
        note,
        corrected_speaker_label: correctedSpeakerLabel,
        corrected_role: correctedRole,
    });
    await loadWorkspaceTimeline(appState.currentSessionId);
    updateWorkspaceStatus(`Speaker correction applied to review item ${item.id}.`, 'success');
    showNotification(`Speaker correction applied to item ${item.id}.`, 'success');
}

function toggleWorkspacePlayback() {
    const player = document.getElementById('workspaceMediaPlayer');
    if (!player) {
        updateWorkspaceStatus('No media player is available for playback controls.', 'error');
        return;
    }
    if (player.paused) {
        player.play().catch(console.error);
        showNotification('Playback started.', 'success');
        return;
    }
    player.pause();
    showNotification('Playback paused.', 'idle');
}

function seekWorkspacePlayback(deltaSeconds) {
    const player = document.getElementById('workspaceMediaPlayer');
    if (!player) {
        updateWorkspaceStatus('No media player is available for seeking.', 'error');
        return;
    }
    const target = Math.max(0, Number(player.currentTime || 0) + deltaSeconds);
    transcriptPlaybackSync.seekPlayer(player, target);
    showNotification(`Seeked to ${transcriptRenderer.formatTimestamp(target)}.`, 'success');
}

function toggleWorkspaceReviewSidebar() {
    appState.reviewSidebarCollapsed = !appState.reviewSidebarCollapsed;
    persistState();
    applyWorkspaceSidebarState();
}

function applyWorkspaceSidebarState() {
    const sidebar = document.getElementById('workspaceReviewSidebar');
    if (!sidebar) {
        return;
    }
    sidebar.dataset.collapsed = appState.reviewSidebarCollapsed ? 'true' : 'false';
}

function bindWorkspaceKeyboardShortcuts() {
    if (workspaceState.keyboardBound) {
        return;
    }
    workspaceState.keyboardBound = true;
    document.addEventListener('keydown', handleWorkspaceShortcut);
}

function handleWorkspaceShortcut(event) {
    const target = event.target;
    if (
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        target instanceof HTMLSelectElement
    ) {
        return;
    }
    if (appState.currentStage !== 3) {
        return;
    }
    if (event.code === 'Space') {
        event.preventDefault();
        toggleWorkspacePlayback();
        return;
    }
    if (event.key === 'ArrowLeft') {
        event.preventDefault();
        seekWorkspacePlayback(-5);
        return;
    }
    if (event.key === 'ArrowRight') {
        event.preventDefault();
        seekWorkspacePlayback(5);
        return;
    }
    if (event.key === '[') {
        event.preventDefault();
        jumpReviewCandidate(-1);
        return;
    }
    if (event.key === ']') {
        event.preventDefault();
        jumpReviewCandidate(1);
        return;
    }
    if (event.key.toLowerCase() === 'g') {
        event.preventDefault();
        document.getElementById('workspaceJumpSpeaker')?.focus();
        return;
    }
    if (event.key.toLowerCase() === 'r') {
        event.preventDefault();
        toggleWorkspaceReviewSidebar();
    }
}

function jumpReviewCandidate(direction) {
    if (!workspaceState.reviewCandidateWords.length) {
        updateWorkspaceStatus('No flagged words are available in the current view.', 'idle');
        return;
    }
    workspaceState.reviewCandidateIndex =
        (workspaceState.reviewCandidateIndex +
            direction +
            workspaceState.reviewCandidateWords.length) %
        workspaceState.reviewCandidateWords.length;
    const candidate = workspaceState.reviewCandidateWords[workspaceState.reviewCandidateIndex];
    const button = document.querySelector(`[data-word-id="${String(candidate.word.id)}"]`);
    if (button) {
        button.click();
    }
}

function updateWorkspaceStatus(message, state) {
    const element = document.getElementById('workspaceStatus');
    element.textContent = message;
    element.dataset.state = state;
}

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}
