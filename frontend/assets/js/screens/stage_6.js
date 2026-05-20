window.stage6Module = {
    init() {
        document.title = 'DEPO-PRO | Export';
        initializeExportState();
        bindExportEvents();
        if (appState.exportSessionId || appState.currentSessionId) {
            loadExportHistory(appState.exportSessionId || appState.currentSessionId).catch(
                console.error,
            );
        }
    },
};

function initializeExportState() {
    document.getElementById('exportSessionId').value =
        appState.exportSessionId || appState.currentSessionId || '';
}

function bindExportEvents() {
    document.getElementById('exportDocxButton').addEventListener('click', () => {
        runExport('docx').catch(console.error);
    });
    document.getElementById('exportTxtButton').addEventListener('click', () => {
        runExport('txt').catch(console.error);
    });
    document.getElementById('exportPackageButton').addEventListener('click', () => {
        runExport('package').catch(console.error);
    });
}

async function runExport(kind) {
    const sessionId = Number(document.getElementById('exportSessionId').value || 0);
    if (!sessionId) {
        updateExportStatus('A session id is required for export.', 'error');
        return;
    }
    appState.exportSessionId = sessionId;
    persistState();

    const payload = {
        session_id: sessionId,
        include_pdf: document.getElementById('exportIncludePdf').checked,
        include_fillers: document.getElementById('exportIncludeFillers').checked,
        package_label: document.getElementById('exportPackageLabel').value.trim() || null,
    };
    updateExportStatus(
        `Running ${kind.toUpperCase()} export for session ${sessionId}...`,
        'working',
    );

    let result;
    if (kind === 'docx') {
        result = await exportTranscriptDocx(payload);
    } else if (kind === 'txt') {
        result = await exportTranscriptTxt(payload);
    } else {
        result = await exportTranscriptPackage(payload);
    }
    renderExportResult(result);
    await loadExportHistory(sessionId);
    updateExportStatus(
        `${kind.toUpperCase()} export completed for session ${sessionId}.`,
        'success',
    );
}

async function loadExportHistory(sessionId) {
    const payload = await fetchExportHistory(sessionId);
    renderExportHistory(payload.items || []);
    document.getElementById('exportHistoryBadge').textContent = payload.items?.length
        ? `${payload.items.length} export runs`
        : 'No export history';
}

function renderExportResult(result) {
    document.getElementById('exportPreview').innerHTML = `
        <div class="stack-item"><strong>Manifest</strong><span>${escapeHtml(result.manifest.export_type)}</span></div>
        <div class="stack-item"><strong>Certificate</strong><span>${escapeHtml(String(result.manifest.transcript_metadata.certificate_lines))} lines</span></div>
        <div class="stack-item"><strong>Page Count</strong><span>${escapeHtml(String(result.manifest.transcript_metadata.page_count))}</span></div>
    `;
    document.getElementById('exportFiles').innerHTML = (result.files || [])
        .map(
            (filePath) => `
            <div class="stack-item">
                <strong>${escapeHtml(filePath.split(/[\\/]/).pop() || filePath)}</strong>
                <span>${escapeHtml(filePath)}</span>
            </div>
        `,
        )
        .join('');
}

function renderExportHistory(items) {
    const target = document.getElementById('exportHistoryList');
    if (!items.length) {
        target.innerHTML = '<p class="muted-copy">No prior export manifests loaded.</p>';
        return;
    }
    target.innerHTML = items
        .map(
            (item) => `
            <div class="audit-row">
                <strong>${escapeHtml(item.export_type.toUpperCase())}</strong>
                <span>${escapeHtml(item.generated_at)}</span>
                <span>${escapeHtml(String(item.transcript_metadata.block_count || 0))} blocks</span>
            </div>
        `,
        )
        .join('');
}

function updateExportStatus(message, state) {
    const element = document.getElementById('exportStatus');
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
