window.liveTranscriptRenderer = {
    render(blocks) {
        if (!blocks.length) {
            return '<div class="placeholder-card compact"><p>No live transcript blocks yet.</p></div>';
        }
        return blocks
            .map(
                (block) => `
                <article class="transcript-block-card">
                    <div class="panel-header">
                        <div>
                            <p class="panel-label">${escapeHtml(block.speaker_label || 'Speaker')}</p>
                            <h4>${escapeHtml(block.block_type || 'COLLOQUY')}</h4>
                        </div>
                        <span class="source-badge">${escapeHtml(formatRange(block.start_time, block.end_time))}</span>
                    </div>
                    <p class="lead">${escapeHtml(block.raw_text || '')}</p>
                </article>
            `,
            )
            .join('');
    },
};

function formatRange(start, end) {
    return `${Number(start || 0).toFixed(2)}s - ${Number(end || 0).toFixed(2)}s`;
}

function escapeHtml(value) {
    return String(value)
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}
