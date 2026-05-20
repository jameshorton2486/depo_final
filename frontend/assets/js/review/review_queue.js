(function attachReviewQueue(globalScope) {
    function fallbackEscape(value) {
        return String(value)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    const reviewQueue = {
        render(items) {
            const escapeHtml = globalScope.escapeHtml || fallbackEscape;
            if (!items.length) {
                return '<p class="muted-copy">No open review items.</p>';
            }
            return items
                .map(
                    (item) => `
                    <button
                        class="review-queue-item"
                        type="button"
                        data-flag-id="${item.id}"
                        data-word-id="${item.word_object_id || ''}"
                        data-speaker-segment-id="${item.speaker_segment_id || ''}"
                    >
                        <div class="action-row">
                            <strong>${escapeHtml(item.word_text || item.original_value || item.issue_category)}</strong>
                            <span class="confidence-chip ${escapeHtml(item.confidence_level || 'medium')}">${escapeHtml(item.confidence_level || 'n/a')}</span>
                        </div>
                        <div class="badge-row">
                            ${globalScope.reviewIssueFlags.render(item.issue_category, item.status)}
                        </div>
                        <p class="muted-copy">${escapeHtml(item.speaker_label || item.block_type || 'Transcript item')}</p>
                    </button>
                `,
                )
                .join('');
        },
    };

    globalScope.reviewQueue = reviewQueue;
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = reviewQueue;
    }
})(typeof window !== 'undefined' ? window : globalThis);
