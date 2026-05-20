(function attachIssueFlags(globalScope) {
    function fallbackEscape(value) {
        return String(value)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    const reviewIssueFlags = {
        render(issueCategory, status) {
            const escapeHtml = globalScope.escapeHtml || fallbackEscape;
            return `
                <span class="issue-flag issue-${escapeHtml(String(issueCategory || '').toLowerCase())}">
                    ${escapeHtml(issueCategory || 'UNCATEGORIZED')}
                </span>
                <span class="source-badge">${escapeHtml(status || 'open')}</span>
            `;
        },
    };

    globalScope.reviewIssueFlags = reviewIssueFlags;
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = reviewIssueFlags;
    }
})(typeof window !== 'undefined' ? window : globalThis);
