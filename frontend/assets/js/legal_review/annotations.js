window.legalReviewAnnotations = {
    render(items) {
        if (!items.length) {
            return '<p class="muted-copy">No transcript annotations yet.</p>';
        }
        return items
            .map(
                (item) => `
                <div class="audit-row">
                    <strong>${escapeHtml(item.annotation_type)}</strong>
                    <span>${escapeHtml(item.annotation_text)}</span>
                    <span>${escapeHtml(item.bookmark_label || item.author)}</span>
                </div>
            `,
            )
            .join('');
    },
};
