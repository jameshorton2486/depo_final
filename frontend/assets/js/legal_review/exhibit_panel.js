window.legalReviewExhibitPanel = {
    render(items) {
        if (!items.length) {
            return '<p class="muted-copy">No transcript-linked exhibits yet.</p>';
        }
        return items
            .map(
                (item) => `
                <div class="audit-row">
                    <strong>${escapeHtml(item.exhibit_label)}</strong>
                    <span>${escapeHtml(item.exhibit_description || 'No description')}</span>
                    <span>Block ${escapeHtml(String(item.transcript_block_id))}</span>
                </div>
            `,
            )
            .join('');
    },
};
