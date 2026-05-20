window.stage1Module = {
    init() {
        document.title = 'DEPO-PRO | Intake';
        bindStageOneEvents();
        renderIntakeEditableFields();
        CollapsiblePanels.init();
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
    document.getElementById('intakeCaseSelect').value = String(result.case.id);
}

function renderSummaryGrid(caseData, parties, attorneys, sessionData) {
    const rows = [];
    if (caseData.case_style || caseData.caption) {
        rows.push(
            compactEntityRow(
                'Case',
                caseData.case_style || caseData.caption,
                caseData.parser_confidence,
            ),
        );
    }
    if (caseData.cause_number) {
        rows.push(compactEntityRow('Cause', caseData.cause_number, caseData.parser_confidence));
    }
    if (caseData.district_division || caseData.venue) {
        rows.push(
            compactEntityRow(
                'Court',
                caseData.district_division || caseData.venue,
                caseData.parser_confidence,
            ),
        );
    }
    parties.forEach((party) => {
        if (!party.party_name) return;
        rows.push(
            compactEntityRow(
                party.party_type || party.side || 'Party',
                party.party_name,
                party.parser_confidence,
            ),
        );
    });
    attorneys.forEach((entry) => {
        const attorney = entry.attorney || entry;
        const caseAttorney = entry.case_attorney || {};
        if (!attorney.full_name) return;
        rows.push(
            compactEntityRow(
                'Attorney',
                attorney.full_name,
                caseAttorney.parser_confidence || attorney.parser_confidence,
                caseAttorney.represented_party_name || attorney.represented_party,
            ),
        );
        if (attorney.firm_name) {
            rows.push(compactEntityRow('Firm', attorney.firm_name));
        }
        if (attorney.email) {
            rows.push(compactEntityRow('Email', attorney.email));
        }
    });
    if (sessionData.deponent_name) {
        rows.push(
            compactEntityRow('Witness', sessionData.deponent_name, sessionData.parser_confidence),
        );
    }
    if (sessionData.session_date) {
        rows.push(compactEntityRow('Date', sessionData.session_date));
    }
    if (sessionData.location_address || sessionData.location) {
        rows.push(
            compactEntityRow('Location', sessionData.location_address || sessionData.location),
        );
    }

    const target = document.getElementById('intakeSummaryGrid');
    target.innerHTML = rows.length
        ? rows.join('')
        : '<p class="empty-state-minimized">No entities extracted yet.</p>';
    CollapsiblePanels.update('parsed-entities', {
        count: rows.length,
        isEmpty: rows.length === 0,
    });
}

function compactEntityRow(label, value, confidence, meta) {
    const metaParts = [];
    if (typeof confidence === 'number') {
        metaParts.push(`${Math.round(confidence * 100)}%`);
    }
    if (meta) {
        metaParts.push(meta);
    }
    return `
        <div class="compact-row">
            <span class="compact-label">${escapeHtml(label || 'Field')}</span>
            <span class="compact-value" title="${escapeHtml(value || '')}">${escapeHtml(value || 'Not extracted')}</span>
            <span class="compact-meta">${escapeHtml(metaParts.join(' · '))}</span>
        </div>
    `;
}

function renderSpeakerLabels(speakers) {
    const target = document.getElementById('speakerLabelPreview');
    const valid = speakers.filter((speaker) => speaker.speaker_label || speaker.full_name);
    target.innerHTML = valid.length
        ? valid
              .map((speaker) => {
                  const role = (speaker.role || '').toLowerCase();
                  const label = speaker.speaker_label || speaker.full_name || 'Ambiguous';
                  const title = speaker.full_name ? `${label} · ${speaker.full_name}` : label;
                  return `<span class="compact-chip" data-role="${escapeHtml(role)}" title="${escapeHtml(title)}">${escapeHtml(label)}</span>`;
              })
              .join('')
        : '<p class="empty-state-minimized">No speakers mapped yet.</p>';
    CollapsiblePanels.update('speaker-labels', {
        count: valid.length,
        isEmpty: valid.length === 0,
    });
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
    const target = document.getElementById('keytermPreview');
    target.innerHTML = terms.length
        ? sortedTerms
              .slice(0, 24)
              .map(
                  (term) =>
                      `<span class="keyterm-pill" title="${escapeHtml(`${term.category} · ${term.source} · boost ${term.weight}`)}">${escapeHtml(term.term)}</span>`,
              )
              .join('')
        : '<p class="empty-state-minimized">No keyterms generated.</p>';
    CollapsiblePanels.update('keyterm-preview', {
        count: terms.length,
        isEmpty: terms.length === 0,
    });
}

function renderPhonetics(phoneticsPayload) {
    const generated = phoneticsPayload.generated || [];
    const manual = phoneticsPayload.manual_overrides || [];
    const rows = [
        ...manual.map((item) => ({
            label: 'Manual',
            term: item.term,
            value: item.pronunciation,
        })),
        ...generated.map((item) => ({
            label: 'Generated',
            term: item.term,
            value: item.pronunciation_hint,
        })),
    ];
    const target = document.getElementById('phoneticPreview');
    target.innerHTML = rows.length
        ? rows
              .map(
                  (row) => `
            <div class="compact-row">
                <span class="compact-label">${escapeHtml(row.label)}</span>
                <span class="compact-value" title="${escapeHtml(`${row.term}: ${row.value}`)}">${escapeHtml(row.term)}</span>
                <span class="compact-meta">${escapeHtml(row.value || '')}</span>
            </div>
        `,
              )
              .join('')
        : '<p class="empty-state-minimized">No pronunciation hints yet.</p>';
    CollapsiblePanels.update('phonetic-seeds', {
        count: rows.length,
        isEmpty: rows.length === 0,
    });
}

function renderProvenance(entries) {
    const target = document.getElementById('provenancePreview');
    target.innerHTML = entries.length
        ? entries
              .map((entry) => {
                  const conf =
                      typeof entry.parser_confidence === 'number'
                          ? `${Math.round(entry.parser_confidence * 100)}%`
                          : '';
                  const flag = entry.manual_override ? 'Manual' : 'Parsed';
                  return `
            <div class="compact-row">
                <span class="compact-label">${escapeHtml(flag)}</span>
                <span class="compact-value" title="${escapeHtml(entry.source_document || '')}">${escapeHtml(entry.label || entry.source_document || 'Source')}</span>
                <span class="compact-meta">${escapeHtml([entry.extracted_from, conf].filter(Boolean).join(' · '))}</span>
            </div>
        `;
              })
              .join('')
        : '<p class="empty-state-minimized">No provenance entries.</p>';
    CollapsiblePanels.update('provenance', {
        count: entries.length,
        isEmpty: entries.length === 0,
    });
}

function renderCaseState(caseState) {
    const rows = [];
    if (caseState.stage_label) {
        rows.push(compactStateRow('Stage', caseState.stage_label, caseState.stage_key));
    }
    rows.push(compactStateRow('Sessions', String(caseState.session_count || 0), 'persisted'));
    if (caseState.review_state) {
        rows.push(compactStateRow('Review', caseState.review_state, 'derived'));
    }
    rows.push(
        compactStateRow('Export', caseState.is_export_ready ? 'Ready' : 'Not Ready', 'derived'),
    );
    if (caseState.latest_session_id) {
        rows.push(compactStateRow('Latest', `#${caseState.latest_session_id}`, 'persisted'));
    }
    const target = document.getElementById('intakeCaseStateGrid');
    target.innerHTML = rows.length
        ? rows.join('')
        : '<p class="empty-state-minimized">Case state not loaded.</p>';
    CollapsiblePanels.update('case-state', {
        count: rows.length,
        isEmpty: !caseState.stage_label,
    });
}

function compactStateRow(label, value, meta) {
    return `
        <div class="compact-row">
            <span class="compact-label">${escapeHtml(label)}</span>
            <span class="compact-value">${escapeHtml(value || '—')}</span>
            <span class="compact-meta">${escapeHtml(meta || '')}</span>
        </div>
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
