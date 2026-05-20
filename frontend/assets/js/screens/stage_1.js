window.stage1Module = {
    init() {
        document.title = 'DEPO-PRO | Intake';
        bindStageOneEvents();
        renderIntakeEditableFields();
        loadPersistedCases().catch(console.error);
        if (appState.currentCaseId) {
            loadPersistedIntake(appState.currentCaseId).catch(console.error);
        }
    },
};

function bindStageOneEvents() {
    document.getElementById('intakeParseButton').addEventListener('click', handleIntakeParse);
    document.getElementById('intakeReloadButton').addEventListener('click', handleIntakeReload);
    document
        .getElementById('intakeCasesRefreshButton')
        .addEventListener('click', () => loadPersistedCases().catch(console.error));
    document
        .getElementById('intakeDiagnosticsRefreshButton')
        .addEventListener('click', () => refreshSystemPanels().catch(console.error));
    document.getElementById('intakeCaseSelect').addEventListener('change', handleCaseSelection);
    document.getElementById('keytermSort').addEventListener('change', () => {
        if (appState.currentCaseId) {
            loadPersistedIntake(appState.currentCaseId).catch(console.error);
        }
    });
}

async function handleIntakeParse() {
    updateIntakeStatus('Parsing intake materials...', 'working');
    try {
        const fileInput = document.getElementById('intakeFile');
        const selectedFile = fileInput.files[0];
        const payload = {
            case_id: appState.currentCaseId || null,
            pasted_text: document.getElementById('intakePastedText').value.trim() || null,
            intake_metadata: {
                source_document:
                    document.getElementById('intakeSourceDocument').value.trim() ||
                    (selectedFile ? selectedFile.name : 'Pasted Intake'),
                case_style: document.getElementById('intakeCaseStyle').value.trim() || null,
                cause_number: document.getElementById('intakeCauseNumber').value.trim() || null,
                deponent_name: document.getElementById('intakeDeponentName').value.trim() || null,
            },
        };
        if (selectedFile) {
            payload.file_name = selectedFile.name;
            payload.file_content_base64 = await readFileAsBase64(selectedFile);
        }
        const result = await parseIntake(payload);
        appState.currentCaseId = result.case_id;
        appState.currentCaseState = result.case_state || null;
        appState.currentCaseStage = result.case_state?.stage_id || 1;
        persistState();
        renderIntakeResult(result);
        renderPipeline();
        renderTranscriptLayersPanel();
        await refreshSystemPanels();
        await loadPersistedCases();
        updateIntakeStatus(`Parsed and persisted case ${result.case_id}`, 'success');
    } catch (error) {
        updateIntakeStatus(error.message, 'error');
        console.error(error);
    }
}

async function handleIntakeReload() {
    if (!appState.currentCaseId) {
        updateIntakeStatus('No persisted case id is stored yet.', 'idle');
        return;
    }
    await loadPersistedIntake(appState.currentCaseId);
}

async function loadPersistedIntake(caseId) {
    updateIntakeStatus(`Loading case ${caseId}...`, 'working');
    const result = await fetchIntake(caseId);
    appState.currentCaseId = caseId;
    appState.currentCaseState = result.case_state || null;
    appState.currentCaseStage = result.case_state?.stage_id || appState.currentCaseStage;
    appState.currentSessionId = result.case_state?.latest_session_id || appState.currentSessionId;
    persistState();
    renderPersistedIntake(result);
    renderPipeline();
    renderTranscriptLayersPanel();
    await refreshSystemPanels();
    updateIntakeStatus(`Loaded persisted case ${caseId}`, 'success');
}

async function loadPersistedCases() {
    const payload = await fetchIntakeCases();
    const target = document.getElementById('intakeCaseSelect');
    const selected = String(appState.currentCaseId || '');
    target.innerHTML = `
        <option value="">Select a persisted case</option>
        ${(payload.items || [])
            .map(
                (item) => `
                <option value="${item.case.id}" ${String(item.case.id) === selected ? 'selected' : ''}>
                    ${escapeHtml(item.case.case_name)} · ${escapeHtml(item.case_state.stage_label)} · ${escapeHtml(String(item.session_count))} sessions
                </option>
            `,
            )
            .join('')}
    `;
}

async function handleCaseSelection(event) {
    const caseId = Number(event.target.value || 0);
    if (!caseId) {
        return;
    }
    await loadPersistedIntake(caseId);
}

function renderIntakeEditableFields(data = null) {
    const target = document.getElementById('intakeEditableFields');
    const caseData = data?.case || {};
    const sessionData = data?.session || data?.sessions?.[0] || {};
    target.innerHTML = `
        <div class="panel-header">
            <div>
                <p class="panel-label">Editable Extracted Fields</p>
                <h4>Review before transcript ingestion</h4>
            </div>
        </div>
        <div class="editable-grid">
            ${renderEditableField('Case Style', caseData.case_style || caseData.caption || '')}
            ${renderEditableField('Cause Number', caseData.cause_number || '')}
            ${renderEditableField('Jurisdiction', caseData.jurisdiction || '')}
            ${renderEditableField('Venue', caseData.venue || '')}
            ${renderEditableField('Deponent', sessionData.deponent_name || '')}
            ${renderEditableField('Location', sessionData.location_address || sessionData.location || '')}
        </div>
    `;
}

function renderEditableField(label, value) {
    return `
        <label class="field-group">
            <span class="field-label">${label}</span>
            <input class="text-input" type="text" value="${escapeHtml(value)}">
        </label>
    `;
}

function renderIntakeResult(result) {
    renderIntakeEditableFields(result);
    renderSummaryGrid(result.case, result.parties, result.attorneys || [], result.session);
    renderSpeakerLabels(result.speaker_labels || []);
    renderKeyterms(result.keyterms);
    renderPhonetics(result.phonetics);
    renderProvenance(result.provenance_entries || []);
    renderCaseState(result.case_state || {});
    document.getElementById('intakeCaseIdBadge').textContent = `Case ${result.case_id}`;
    document.getElementById('intakeSourceDocument').value = result.provenance.source_document || '';
}

function renderPersistedIntake(result) {
    renderIntakeEditableFields({ case: result.case, sessions: result.sessions });
    renderSummaryGrid(
        result.case,
        result.parties,
        result.attorneys || [],
        result.sessions?.[0] || {},
    );
    renderSpeakerLabels(result.speaker_labels || []);
    renderKeyterms(result.keyterms || { keyterms: [] });
    renderPhonetics(result.phonetics || { generated: [], manual_overrides: [] });
    renderProvenance(result.provenance_entries || []);
    renderCaseState(result.case_state || {});
    document.getElementById('intakeCaseIdBadge').textContent = `Case ${result.case.id}`;
    document.getElementById('intakeCaseSelect').value = String(result.case.id);
}

function renderSummaryGrid(caseData, parties, attorneys, sessionData) {
    document.getElementById('intakeSummaryGrid').innerHTML = `
        ${renderSummaryCard('Case', [
            summariseField(
                'Case Style',
                caseData.case_style || caseData.caption,
                caseData.parser_confidence,
                caseData.extracted_from,
            ),
            summariseField(
                'Cause Number',
                caseData.cause_number,
                caseData.parser_confidence,
                caseData.extracted_from,
            ),
            summariseField(
                'Court',
                caseData.district_division || caseData.venue,
                caseData.parser_confidence,
                caseData.extracted_from,
            ),
        ])}
        ${renderSummaryCard('Parties', parties.map((party) => summariseField(party.party_type || party.side, party.party_name, party.parser_confidence, party.extracted_from)).join(''))}
        ${renderSummaryCard(
            'Attorneys',
            attorneys
                .map((entry) => {
                    const attorney = entry.attorney || entry;
                    const caseAttorney = entry.case_attorney || {};
                    return summariseField(
                        attorney.full_name,
                        caseAttorney.represented_party_name || attorney.represented_party,
                        caseAttorney.parser_confidence || attorney.parser_confidence,
                        caseAttorney.extracted_from || attorney.extracted_from,
                    );
                })
                .join(''),
        )}
        ${renderSummaryCard('Session', [
            summariseField(
                'Deponent',
                sessionData.deponent_name,
                sessionData.parser_confidence,
                sessionData.extracted_from,
            ),
            summariseField(
                'Date',
                sessionData.session_date,
                sessionData.parser_confidence,
                sessionData.extracted_from,
            ),
            summariseField(
                'Location',
                sessionData.location_address || sessionData.location,
                sessionData.parser_confidence,
                sessionData.extracted_from,
            ),
        ])}
    `;
}

function renderSummaryCard(title, body) {
    return `<div class="result-card"><h4>${title}</h4>${Array.isArray(body) ? body.join('') : body}</div>`;
}

function summariseField(label, value, confidence, provenance) {
    return `
        <div class="summary-row">
            <div>
                <strong>${escapeHtml(label || 'Field')}</strong>
                <p>${escapeHtml(value || 'Not extracted')}</p>
            </div>
            <div class="meta-stack">
                <span class="confidence-badge">${formatConfidence(confidence)}</span>
                <span class="source-badge">${escapeHtml(provenance || 'Unknown')}</span>
            </div>
        </div>
    `;
}

function renderSpeakerLabels(speakers) {
    document.getElementById('speakerLabelPreview').innerHTML = speakers.length
        ? speakers
              .map(
                  (speaker) => `
            <div class="summary-row">
                <div>
                    <strong>${escapeHtml(speaker.speaker_label || 'Ambiguous')}</strong>
                    <p>${escapeHtml(speaker.full_name || 'System label')}</p>
                </div>
                <div class="meta-stack">
                    <span class="source-badge">${escapeHtml(speaker.role || 'role')}</span>
                    <span class="confidence-badge">${formatConfidence(speaker.confidence)}</span>
                </div>
            </div>
        `,
              )
              .join('')
        : '<p class="muted-copy">No attorneys extracted yet.</p>';
}

function renderKeyterms(keytermsPayload) {
    const terms = keytermsPayload.keyterms || [];
    const sortMode = document.getElementById('keytermSort').value;
    const sortedTerms = [...terms].sort((left, right) => {
        if (sortMode === 'category') {
            return `${left.category}:${left.term}`.localeCompare(`${right.category}:${right.term}`);
        }
        return Number(right.weight || 0) - Number(left.weight || 0);
    });
    document.getElementById('keytermPreview').innerHTML = terms.length
        ? sortedTerms
              .slice(0, 18)
              .map(
                  (term) =>
                      `<span class="keyterm-pill" title="${escapeHtml(`${term.category} · ${term.source} · boost ${term.weight}`)}">${escapeHtml(term.term)}</span>`,
              )
              .join('')
        : '<p class="muted-copy">Keyterms will appear after parsing.</p>';
}

function renderPhonetics(phoneticsPayload) {
    const generated = phoneticsPayload.generated || [];
    const manual = phoneticsPayload.manual_overrides || [];
    const rows = [
        ...manual.map((item) => `${item.term}: ${item.pronunciation}`),
        ...generated.map((item) => `${item.term}: ${item.pronunciation_hint}`),
    ];
    document.getElementById('phoneticPreview').innerHTML = rows.length
        ? rows
              .map((row) => `<div class="stack-item"><span>${escapeHtml(row)}</span></div>`)
              .join('')
        : '<p class="muted-copy">No pronunciation-sensitive names detected yet.</p>';
}

function renderProvenance(entries) {
    document.getElementById('provenancePreview').innerHTML = entries.length
        ? entries
              .map(
                  (entry) => `
            <div class="summary-row">
                <div>
                    <strong>${escapeHtml(entry.label || 'Source')}</strong>
                    <p>${escapeHtml(entry.source_document || 'Unknown source')}</p>
                </div>
                <div class="meta-stack">
                    <span class="source-badge">${escapeHtml(entry.extracted_from || 'Unknown')}</span>
                    <span class="confidence-badge">${formatConfidence(entry.parser_confidence)}</span>
                    <span class="source-badge">${entry.manual_override ? 'Manual override' : 'Parser derived'}</span>
                </div>
            </div>
        `,
              )
              .join('')
        : '<p class="muted-copy">No provenance entries yet.</p>';
}

function renderCaseState(caseState) {
    document.getElementById('intakeCaseStateGrid').innerHTML = `
        ${renderSummaryCard('Pipeline', [
            summariseField('Current Stage', caseState.stage_label, null, caseState.stage_key),
            summariseField('Sessions', String(caseState.session_count || 0), null, 'persisted'),
            summariseField('Review State', caseState.review_state, null, 'derived'),
        ])}
        ${renderSummaryCard('Readiness', [
            summariseField(
                'Export Ready',
                caseState.is_export_ready ? 'Yes' : 'No',
                null,
                'derived',
            ),
            summariseField(
                'Latest Session',
                caseState.latest_session_id ? String(caseState.latest_session_id) : 'None',
                null,
                'persisted',
            ),
        ])}
    `;
}

function updateIntakeStatus(message, state) {
    const element = document.getElementById('intakeStatus');
    element.textContent = message;
    element.dataset.state = state;
}

function formatConfidence(value) {
    if (typeof value !== 'number') {
        return 'Confidence n/a';
    }
    return `${Math.round(value * 100)}% confidence`;
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
