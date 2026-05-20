(function attachConfidencePanel(globalScope) {
    function fallbackEscape(value) {
        return String(value)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    const reviewConfidencePanel = {
        render(summary) {
            const escapeHtml = globalScope.escapeHtml || fallbackEscape;
            return `
                <div class="stack-item"><strong>High</strong><span>${escapeHtml(String(summary.high || 0))}</span></div>
                <div class="stack-item"><strong>Medium</strong><span>${escapeHtml(String(summary.medium || 0))}</span></div>
                <div class="stack-item"><strong>Low</strong><span>${escapeHtml(String(summary.low || 0))}</span></div>
            `;
        },
    };

    globalScope.reviewConfidencePanel = reviewConfidencePanel;
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = reviewConfidencePanel;
    }
})(typeof window !== 'undefined' ? window : globalThis);
