window.stage2Module = {
    init() {
        document.title = 'DEPO-PRO | Transcripts';
        bindTranscriptEvents();
        seedTranscriptFields();
        renderTranscriptSummary();
        renderTranscriptDiagnostics();
        renderTranscriptViewer();
        if (appState.currentSessionId) {
            loadTranscript(appState.currentSessionId).catch(console.error);
        }
    },
};

function bindTranscriptEvents() {
    document
        .getElementById('transcriptStartButton')
        .addEventListener('click', handleTranscriptionStart);
    document
        .getElementById('transcriptReloadButton')
        .addEventListener('click', handleTranscriptReload);
    document.getElementById('transcriptFile').addEventListener('change', handleTranscriptPreview);
}

function seedTranscriptFields() {
    document.getElementById('transcriptCaseId').value = appState.currentCaseId || '';
    document.getElementById('transcriptSessionId').value = appState.currentSessionId || '';
}

async function handleTranscriptionStart() {
    const fileInput = document.getElementById('transcriptFile');
    const selectedFile = fileInput.files[0];
    const caseId = Number(
        document.getElementById('transcriptCaseId').value || appState.currentCaseId,
    );
    const sessionIdValue = Number(document.getElementById('transcriptSessionId').value || 0);
    if (!caseId) {
        updateTranscriptStatus('Case id is required before transcription.', 'error');
        return;
    }
    if (!selectedFile) {
        updateTranscriptStatus('Select an audio or video asset first.', 'error');
        return;
    }

    updateTranscriptStatus('Running preprocessing and prerecorded transcription...', 'working');
    renderTranscriptProgress('Running', 'Pending', 'Pending');

    try {
        const payload = {
            case_id: caseId,
            session_id: sessionIdValue || null,
            file_name: selectedFile.name,
            file_content_base64: await readFileAsBase64(selectedFile),
            intake_metadata: {},
        };
        const result = await transcribePrerecorded(payload);
        appState.currentCaseId = caseId;
        appState.currentSessionId = result.session_id;
        persistState();
        document.getElementById('transcriptSessionId').value = result.session_id;
        renderTranscriptionResult(result);
        await loadTranscript(result.session_id);
        updateTranscriptStatus(`Transcript persisted for session ${result.session_id}`, 'success');
        renderTranscriptProgress('Complete', 'Complete', 'Complete');
    } catch (error) {
        updateTranscriptStatus(error.message, 'error');
        renderTranscriptProgress('Failed', 'Failed', 'Failed');
        console.error(error);
    }
}

async function handleTranscriptReload() {
    const sessionId = Number(
        document.getElementById('transcriptSessionId').value || appState.currentSessionId,
    );
    if (!sessionId) {
        updateTranscriptStatus('No session id is available to reload.', 'idle');
        return;
    }
    await loadTranscript(sessionId);
}

async function loadTranscript(sessionId) {
    updateTranscriptStatus(`Loading transcript for session ${sessionId}...`, 'working');
    const payload = await fetchTranscript(sessionId);
    appState.currentSessionId = sessionId;
    persistState();
    renderTranscriptBundle(payload);
    updateTranscriptStatus(`Loaded transcript for session ${sessionId}`, 'success');
}

function handleTranscriptPreview(event) {
    const file = event.target.files[0];
    const previewRoot = document.getElementById('transcriptMediaPreview');
    if (!file) {
        previewRoot.innerHTML =
            '<p>Select an audio or video asset to preview it here before transcription.</p>';
        return;
    }
    const objectUrl = URL.createObjectURL(file);
    const mediaTag = file.type.startsWith('video/')
        ? `<video controls class="media-preview" src="${objectUrl}"></video>`
        : `<audio controls class="media-preview" src="${objectUrl}"></audio>`;
    previewRoot.innerHTML = `
        <div class="stack-item">
            <strong>${escapeHtml(file.name)}</strong>
            <span>${escapeHtml(file.type || 'unknown media type')}</span>
            ${mediaTag}
        </div>
    `;
}

function renderTranscriptionResult(result) {
    renderTranscriptSummary(result.asset, result.preprocessing, result.transcript_summary);
    renderTranscriptDiagnostics(result.preprocessing);
    document.getElementById('transcriptSessionBadge').textContent = `Session ${result.session_id}`;
}

function renderTranscriptBundle(payload = null) {
    const asset = payload?.assets?.[0] || null;
    renderTranscriptSummary(
        asset,
        asset
            ? { estimated_snr_db: asset.snr_value, calibrated_utt_split: asset.utt_split_value }
            : null,
        {
            block_count: payload?.transcript_blocks?.length || 0,
            word_count: payload?.word_objects?.length || 0,
            speaker_count: payload?.speaker_segments?.length || 0,
            duration: payload?.transcript_blocks?.at(-1)?.end_time || null,
        },
    );
    renderTranscriptViewer(payload?.transcript_blocks || []);
    document.getElementById('transcriptSessionBadge').textContent = payload
        ? `Session ${payload.session.id}`
        : 'No session loaded';
}

function renderTranscriptProgress(preprocessing, deepgram, persistence) {
    document.getElementById('transcriptProgress').innerHTML = `
        <div class="stack-item"><strong>Preprocessing</strong><span>${escapeHtml(preprocessing)}</span></div>
        <div class="stack-item"><strong>Deepgram</strong><span>${escapeHtml(deepgram)}</span></div>
        <div class="stack-item"><strong>Layer 3 Persistence</strong><span>${escapeHtml(persistence)}</span></div>
    `;
}

function renderTranscriptSummary(asset = null, preprocessing = null, summary = null) {
    const rows = [
        renderSummaryMetric('Asset', asset?.file_name || 'No asset loaded'),
        renderSummaryMetric('Format', asset?.source_format || 'n/a'),
        renderSummaryMetric(
            'SNR',
            formatNumber(preprocessing?.estimated_snr_db || asset?.snr_value, ' dB'),
        ),
        renderSummaryMetric(
            'utt_split',
            formatNumber(preprocessing?.calibrated_utt_split || asset?.utt_split_value, 's'),
        ),
        renderSummaryMetric('Blocks', String(summary?.block_count || 0)),
        renderSummaryMetric('Words', String(summary?.word_count || 0)),
        renderSummaryMetric('Speakers', String(summary?.speaker_count || 0)),
        renderSummaryMetric('Duration', formatNumber(summary?.duration, 's')),
    ];
    document.getElementById('transcriptSummaryGrid').innerHTML = rows.join('');
}

function renderSummaryMetric(label, value) {
    return `
        <div class="result-card summary-metric">
            <p class="panel-label">${escapeHtml(label)}</p>
            <h4>${escapeHtml(value || 'n/a')}</h4>
        </div>
    `;
}

function renderTranscriptDiagnostics(preprocessing = null) {
    document.getElementById('transcriptDiagnostics').innerHTML = `
        <div class="stack-item"><strong>SNR</strong><span>${escapeHtml(formatNumber(preprocessing?.estimated_snr_db, ' dB') || 'Not calculated')}</span></div>
        <div class="stack-item"><strong>utt_split</strong><span>${escapeHtml(formatNumber(preprocessing?.calibrated_utt_split, 's') || 'Not calibrated')}</span></div>
        <div class="stack-item"><strong>Denoising</strong><span>${escapeHtml(preprocessing?.denoise?.denoise_method || 'Not applied')}</span></div>
    `;
}

function renderTranscriptViewer(blocks = []) {
    const target = document.getElementById('transcriptViewer');
    if (!blocks.length) {
        target.innerHTML =
            '<div class="placeholder-card compact"><p>No transcript blocks persisted yet.</p></div>';
        return;
    }
    target.innerHTML = blocks
        .map(
            (block) => `
            <article class="transcript-block-card">
                <div class="panel-header">
                    <div>
                        <p class="panel-label">${escapeHtml(block.speaker_label || `Speaker ${Number(block.speaker_index || 0) + 1}`)}</p>
                        <h4>${escapeHtml(block.block_type)}</h4>
                    </div>
                    <div class="meta-stack">
                        <span class="source-badge">${escapeHtml(formatRange(block.start_time, block.end_time))}</span>
                        <span class="confidence-chip ${confidenceClass(block.confidence)}">${escapeHtml(formatConfidence(block.confidence))}</span>
                    </div>
                </div>
                <p class="lead">${escapeHtml(block.raw_text)}</p>
                <div class="word-cloud">
                    ${(block.words || [])
                        .map(
                            (word) => `
                            <span class="word-pill ${confidenceClass(word.confidence)}" title="${escapeHtml(formatRange(word.start_time, word.end_time))}">
                                ${escapeHtml(word.word_text)}
                            </span>
                        `,
                        )
                        .join('')}
                </div>
            </article>
        `,
        )
        .join('');
}

function updateTranscriptStatus(message, state) {
    const element = document.getElementById('transcriptStatus');
    element.textContent = message;
    element.dataset.state = state;
}

function formatRange(start, end) {
    return `${formatNumber(start, 's')} - ${formatNumber(end, 's')}`;
}

function formatNumber(value, suffix) {
    if (typeof value !== 'number' || Number.isNaN(value)) {
        return 'n/a';
    }
    return `${value.toFixed(2)}${suffix}`;
}

function formatConfidence(value) {
    if (typeof value !== 'number') {
        return 'Confidence n/a';
    }
    return `${Math.round(value * 100)}% confidence`;
}

function confidenceClass(value) {
    if (typeof value !== 'number') {
        return 'medium';
    }
    if (value >= 0.95) {
        return 'high';
    }
    if (value >= 0.85) {
        return 'medium';
    }
    return 'low';
}

function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result).split(',').pop());
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}
