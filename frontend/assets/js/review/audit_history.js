(function attachAuditHistory(globalScope) {
    function fallbackEscape(value) {
        return String(value)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    const reviewAuditHistory = {
        render(items) {
            const escapeHtml = globalScope.escapeHtml || fallbackEscape;
            if (!items.length) {
                return '<p class="muted-copy">No audit events have been recorded yet.</p>';
            }
            return items
                .slice(0, 20)
                .map(
                    (item) => `
                    <div class="audit-row">
                        <strong>${escapeHtml(item.action_type)}</strong>
                        <span>${escapeHtml(item.issue_category || item.entity_type)}</span>
                        <span>${escapeHtml(item.reviewer || 'Unknown reviewer')}</span>
                    </div>
                `,
                )
                .join('');
        },
    };

    globalScope.reviewAuditHistory = reviewAuditHistory;
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = reviewAuditHistory;
    }
})(typeof window !== 'undefined' ? window : globalThis);
