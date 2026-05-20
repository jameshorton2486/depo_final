(function attachTranscriptRenderer(globalScope) {
    function fallbackEscape(value) {
        return String(value)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    const transcriptRenderer = {
        formatTimestamp(value) {
            if (typeof value !== 'number' || Number.isNaN(value)) {
                return '00:00.00';
            }
            const minutes = Math.floor(value / 60);
            const seconds = value - minutes * 60;
            return `${String(minutes).padStart(2, '0')}:${seconds.toFixed(2).padStart(5, '0')}`;
        },

        renderWord(word, context) {
            const confidence = globalScope.transcriptConfidence.classify(word.confidence);
            const speakerRole = globalScope.transcriptSpeakerVisualization.roleForLabel(
                context.speaker_label,
            );
            const escapeHtml = globalScope.escapeHtml || fallbackEscape;
            return `
                <button
                    class="transcript-word confidence-${confidence} speaker-word-${speakerRole}${word.review_candidate ? ' review-candidate' : ''}"
                    type="button"
                    data-word-id="${word.id}"
                    data-block-id="${context.id}"
                    data-start-time="${word.start_time}"
                    data-end-time="${word.end_time}"
                    data-confidence-class="${confidence}"
                    title="${escapeHtml(this.formatTimestamp(word.start_time))}"
                >
                    ${escapeHtml(word.word_text)}
                </button>
            `;
        },

        renderBlock(block) {
            const speakerClass = globalScope.transcriptSpeakerVisualization.blockClass(
                block.speaker_label,
            );
            const blockConfidence = globalScope.transcriptConfidence.classify(block.confidence);
            const escapeHtml = globalScope.escapeHtml || fallbackEscape;
            return `
                <article class="workspace-transcript-block ${speakerClass}" data-block-id="${block.id}" data-speaker-label="${escapeHtml(block.speaker_label || '')}">
                    <div class="panel-header">
                        <div>
                            <p class="panel-label">${escapeHtml(block.speaker_label || `Speaker ${Number(block.speaker_index || 0) + 1}`)}</p>
                            <h4>${escapeHtml(block.block_type)}</h4>
                        </div>
                        <div class="meta-stack">
                            <span class="source-badge">${escapeHtml(this.formatTimestamp(block.start_time))} - ${escapeHtml(this.formatTimestamp(block.end_time))}</span>
                            <span class="confidence-chip ${blockConfidence}">${escapeHtml(`${Math.round((block.confidence || 0) * 100)}% confidence`)}</span>
                        </div>
                    </div>
                    <div class="workspace-word-grid">
                        ${(block.words || []).map((word) => this.renderWord(word, block)).join('')}
                    </div>
                </article>
            `;
        },
    };

    globalScope.transcriptRenderer = transcriptRenderer;
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = transcriptRenderer;
    }
})(typeof window !== 'undefined' ? window : globalThis);
