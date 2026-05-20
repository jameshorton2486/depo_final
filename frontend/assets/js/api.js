async function fetchHealth() {
    const response = await fetch('/api/health');
    if (!response.ok) {
        throw new Error(`Health request failed with ${response.status}`);
    }
    const payload = await response.json();
    appState.health = payload;
    return payload;
}
