window.legalReviewNavigationView = {
    render(items) {
        if (!items.length) {
            return '<p class="muted-copy">No legal navigation anchors available.</p>';
        }
        return items
            .map(
                (item) => `
                <button class="review-candidate-row" type="button" data-nav-block-id="${escapeHtml(String(item.transcript_block_id || ''))}">
                    <strong>${escapeHtml(item.nav_type)}</strong>
                    <span>${escapeHtml(item.nav_label)}</span>
                </button>
            `,
            )
            .join('');
    },
};
