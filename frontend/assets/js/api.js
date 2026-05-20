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
