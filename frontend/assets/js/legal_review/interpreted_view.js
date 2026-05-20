window.legalReviewInterpretedView = {
    render(items) {
        if (!items.length) {
            return '<p class="muted-copy">No interpreted segments detected in this session.</p>';
        }
        return items
            .map(
                (item) => `
                <div class="audit-row">
                    <strong>${escapeHtml(item.interpreter_label || 'THE INTERPRETER')}</strong>
                    <span>${escapeHtml(`${item.source_language || 'Unknown'} -> ${item.target_language || 'English'}`)}</span>
                    <span>${escapeHtml(item.interpreted_text || '')}</span>
                </div>
            `,
            )
            .join('');
    },
};
