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
    activeWordId: null,
    activeBlockId: null,
    searchMatches: [],
};

function initializeWorkspaceState() {
    document.getElementById('workspaceSessionId').value = appState.currentSessionId || '';
    document.getElementById('workspaceSearch').value = appState.workspaceSearch || '';
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
    const payload = await fetchTranscriptTimeline(sessionId);
    appState.currentSessionId = sessionId;
    persistState();

    workspaceState.timeline = payload.timeline || [];
    workspaceState.playback = payload.playback || null;
    workspaceState.asset = payload.asset || null;
    workspaceState.activeWordId = null;
    workspaceState.activeBlockId = workspaceState.timeline[0]?.id || null;

    renderWorkspaceMedia(payload);
    renderWorkspaceSummary(payload);
    renderWorkspaceTranscript(payload.timeline || []);
    renderReviewCandidates(payload.timeline || []);
    renderNavigationMeta();
    document.getElementById('workspaceSessionBadge').textContent = `Session ${sessionId}`;
    updateWorkspaceStatus(`Workspace loaded for session ${sessionId}`, 'success');
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

function updateWorkspaceStatus(message, state) {
    const element = document.getElementById('workspaceStatus');
    element.textContent = message;
    element.dataset.state = state;
}
