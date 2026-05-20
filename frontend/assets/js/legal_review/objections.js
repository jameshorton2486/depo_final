window.legalReviewObjections = {
    render(items) {
        if (!items.length) {
            return '<p class="muted-copy">No objections tagged yet.</p>';
        }
        return items
            .map(
                (item) => `
                <div class="audit-row">
                    <strong>${escapeHtml(item.category)}</strong>
                    <span>${escapeHtml(item.objection_text)}</span>
                    <span>Status: ${escapeHtml(item.status)}</span>
                </div>
            `,
            )
            .join('');
    },
};
