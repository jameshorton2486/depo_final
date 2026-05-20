window.legalReviewIssueManagement = {
    render(items) {
        if (!items.length) {
            return '<p class="muted-copy">No advanced review issues are open.</p>';
        }
        return items
            .map(
                (item) => `
                <div class="audit-row">
                    <strong>${escapeHtml(item.review_category)}</strong>
                    <span>${escapeHtml(item.issue_status)}</span>
                    <span>${escapeHtml(item.note || 'No note')}</span>
                </div>
            `,
            )
            .join('');
    },
};
