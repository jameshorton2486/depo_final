async function fetchHealth() {
    const response = await fetch('/api/health');
    if (!response.ok) {
        throw new Error(`Health request failed with ${response.status}`);
    }
    const payload = await response.json();
    appState.health = payload;
    return payload;
}

async function parseIntake(payload) {
    const response = await fetch('/api/intake/parse', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error(`Intake parse failed with ${response.status}`);
    }
    return response.json();
}

async function fetchIntake(caseId) {
    const response = await fetch(`/api/intake/${caseId}`);
    if (!response.ok) {
        throw new Error(`Intake fetch failed with ${response.status}`);
    }
    return response.json();
}

async function fetchIntakeCases() {
    const response = await fetch('/api/intake/cases');
    if (!response.ok) {
        throw new Error(`Intake cases fetch failed with ${response.status}`);
    }
    const payload = await response.json();
    appState.intakeCases = payload.items || [];
    return payload;
}

async function persistCaseStage(caseId, stageId) {
    const response = await fetch(`/api/intake/${caseId}/stage`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ stage_id: stageId }),
    });
    if (!response.ok) {
        throw new Error(`Case stage persistence failed with ${response.status}`);
    }
    return response.json();
}

async function transcribePrerecorded(payload) {
    const response = await fetch('/api/transcribe/prerecorded', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error(`Transcription request failed with ${response.status}`);
    }
    return response.json();
}

async function fetchTranscript(sessionId) {
    const response = await fetch(`/api/transcript/${sessionId}`);
    if (!response.ok) {
        throw new Error(`Transcript fetch failed with ${response.status}`);
    }
    return response.json();
}

async function fetchTranscriptTimeline(sessionId) {
    const response = await fetch(`/api/transcript/${sessionId}/timeline`);
    if (!response.ok) {
        throw new Error(`Transcript timeline fetch failed with ${response.status}`);
    }
    return response.json();
}

async function fetchTranscriptWord(sessionId, wordId) {
    const response = await fetch(`/api/transcript/${sessionId}/word/${wordId}`);
    if (!response.ok) {
        throw new Error(`Transcript word fetch failed with ${response.status}`);
    }
    return response.json();
}

async function fetchReviewQueue(sessionId) {
    const response = await fetch(`/api/review/${sessionId}/queue`);
    if (!response.ok) {
        throw new Error(`Review queue fetch failed with ${response.status}`);
    }
    return response.json();
}

async function resolveReviewItem(payload) {
    const response = await fetch('/api/review/resolve', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error(`Review resolve failed with ${response.status}`);
    }
    return response.json();
}

async function fetchReviewAudit(sessionId) {
    const response = await fetch(`/api/review/${sessionId}/audit`);
    if (!response.ok) {
        throw new Error(`Review audit fetch failed with ${response.status}`);
    }
    return response.json();
}

async function exportTranscriptDocx(payload) {
    const response = await fetch('/api/export/docx', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error(`DOCX export failed with ${response.status}`);
    }
    return response.json();
}

async function exportTranscriptTxt(payload) {
    const response = await fetch('/api/export/txt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error(`TXT export failed with ${response.status}`);
    }
    return response.json();
}

async function exportTranscriptPackage(payload) {
    const response = await fetch('/api/export/package', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error(`Package export failed with ${response.status}`);
    }
    return response.json();
}

async function fetchExportHistory(sessionId) {
    const response = await fetch(`/api/export/${sessionId}/history`);
    if (!response.ok) {
        throw new Error(`Export history fetch failed with ${response.status}`);
    }
    return response.json();
}

async function startRealtimeSession(payload) {
    const response = await fetch('/api/realtime/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error(`Realtime start failed with ${response.status}`);
    }
    return response.json();
}

async function stopRealtimeSession(payload) {
    const response = await fetch('/api/realtime/stop', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error(`Realtime stop failed with ${response.status}`);
    }
    return response.json();
}

async function fetchRealtimeStatus(sessionId) {
    const response = await fetch(`/api/realtime/status/${sessionId}`);
    if (!response.ok) {
        throw new Error(`Realtime status failed with ${response.status}`);
    }
    return response.json();
}

async function createReviewAnnotation(payload) {
    const response = await fetch('/api/review/annotation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error(`Annotation create failed with ${response.status}`);
    }
    return response.json();
}

async function createReviewObjection(payload) {
    const response = await fetch('/api/review/objection', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error(`Objection create failed with ${response.status}`);
    }
    return response.json();
}

async function createReviewExhibitLink(payload) {
    const response = await fetch('/api/review/exhibit-link', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error(`Exhibit link failed with ${response.status}`);
    }
    return response.json();
}

async function fetchReviewDashboard(sessionId) {
    const response = await fetch(`/api/review/${sessionId}/dashboard`);
    if (!response.ok) {
        throw new Error(`Review dashboard failed with ${response.status}`);
    }
    return response.json();
}

async function fetchReviewNavigation(sessionId) {
    const response = await fetch(`/api/review/${sessionId}/navigation`);
    if (!response.ok) {
        throw new Error(`Review navigation failed with ${response.status}`);
    }
    return response.json();
}

async function fetchSystemHealth() {
    const response = await fetch('/api/system/health');
    if (!response.ok) {
        throw new Error(`System health failed with ${response.status}`);
    }
    const payload = await response.json();
    appState.systemHealth = payload;
    return payload;
}

async function fetchSystemDiagnostics(sessionId = null) {
    const suffix = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
    const response = await fetch(`/api/system/diagnostics${suffix}`);
    if (!response.ok) {
        throw new Error(`System diagnostics failed with ${response.status}`);
    }
    const payload = await response.json();
    appState.systemDiagnostics = payload;
    return payload;
}

async function fetchSystemPerformance(sessionId = null) {
    const suffix = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
    const response = await fetch(`/api/system/performance${suffix}`);
    if (!response.ok) {
        throw new Error(`System performance failed with ${response.status}`);
    }
    const payload = await response.json();
    appState.systemPerformance = payload;
    return payload;
}

async function runSystemRecovery(payload) {
    const response = await fetch('/api/system/recovery', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error(`System recovery failed with ${response.status}`);
    }
    return response.json();
}
