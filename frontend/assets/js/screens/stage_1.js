window.stage1Module = {
    init() {
        document.title = 'DEPO-PRO | Intake';
        bindStageOneEvents();
        renderIntakeEditableFields();
        if (appState.currentCaseId) {
            loadPersistedIntake(appState.currentCaseId).catch(console.error);
        }
    },
};

function bindStageOneEvents() {
    document.getElementById('intakeParseButton').addEventListener('click', handleIntakeParse);
    document.getElementById('intakeReloadButton').addEventListener('click', handleIntakeReload);
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
        persistState();
        renderIntakeResult(result);
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
    renderPersistedIntake(result);
    updateIntakeStatus(`Loaded persisted case ${caseId}`, 'success');
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
    const attorneyPreview = (result.attorneys || []).map((entry) => ({
        full_name: entry.attorney.full_name,
        law_firm: entry.attorney.represented_party || entry.case_attorney.represented_party_name,
        speaker_label: entry.case_attorney.speaker_label,
        parser_confidence: entry.case_attorney.parser_confidence,
        extracted_from: entry.case_attorney.extracted_from,
    }));
    renderIntakeEditableFields(result);
    renderSummaryGrid(result.case, result.parties, attorneyPreview, result.session);
    renderSpeakerLabels(attorneyPreview);
    renderKeyterms(result.keyterms);
    renderPhonetics(result.phonetics);
    renderProvenance(result.provenance, result.case, result.session);
    document.getElementById('intakeCaseIdBadge').textContent = `Case ${result.case_id}`;
    document.getElementById('intakeSourceDocument').value = result.provenance.source_document || '';
}

function renderPersistedIntake(result) {
    renderIntakeEditableFields({ case: result.case, sessions: result.sessions });
    const attorneys = (result.attorneys || []).map((entry) => ({
        full_name: entry.attorney.full_name,
        law_firm: entry.attorney.represented_party || entry.case_attorney.represented_party_name,
        speaker_label: entry.case_attorney.speaker_label,
        parser_confidence: entry.case_attorney.parser_confidence,
        extracted_from: entry.case_attorney.extracted_from,
    }));
    renderSummaryGrid(result.case, result.parties, attorneys, result.sessions?.[0] || {});
    renderSpeakerLabels(attorneys);
    renderKeyterms(result.keyterms || { keyterms: [] });
    renderPhonetics(result.phonetics || { generated: [], manual_overrides: [] });
    renderProvenance(
        {
            source_document: result.case.source_document,
            extracted_from: result.case.extracted_from,
            parser: 'persisted_intake',
        },
        result.case,
        result.sessions?.[0] || {},
    );
    document.getElementById('intakeCaseIdBadge').textContent = `Case ${result.case.id}`;
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
        ${renderSummaryCard('Attorneys', attorneys.map((attorney) => summariseField(attorney.full_name, attorney.law_firm || attorney.represented_party, attorney.parser_confidence, attorney.extracted_from)).join(''))}
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

function renderSpeakerLabels(attorneys) {
    document.getElementById('speakerLabelPreview').innerHTML = attorneys.length
        ? attorneys
              .map(
                  (attorney) => `
            <div class="stack-item">
                <strong>${escapeHtml(attorney.full_name || 'Unknown Attorney')}</strong>
                <span>${escapeHtml(attorney.speaker_label || 'Ambiguous')}</span>
            </div>
        `,
              )
              .join('')
        : '<p class="muted-copy">No attorneys extracted yet.</p>';
}

function renderKeyterms(keytermsPayload) {
    const terms = keytermsPayload.keyterms || [];
    document.getElementById('keytermPreview').innerHTML = terms.length
        ? terms
              .slice(0, 18)
              .map((term) => `<span class="keyterm-pill">${escapeHtml(term.term)}</span>`)
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

function renderProvenance(provenance, caseData, sessionData) {
    document.getElementById('provenancePreview').innerHTML = `
        <div class="stack-item"><strong>Source</strong><span>${escapeHtml(provenance.source_document || 'Unknown')}</span></div>
        <div class="stack-item"><strong>Extracted From</strong><span>${escapeHtml(provenance.extracted_from || caseData.extracted_from || 'Unknown')}</span></div>
        <div class="stack-item"><strong>Parser</strong><span>${escapeHtml(provenance.parser || 'deterministic')}</span></div>
        <div class="stack-item"><strong>Session Confidence</strong><span>${formatConfidence(sessionData.parser_confidence)}</span></div>
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
