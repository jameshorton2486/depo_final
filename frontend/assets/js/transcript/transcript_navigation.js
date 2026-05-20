(function attachTranscriptNavigation(globalScope) {
    const transcriptNavigation = {
        filterBlocks(blocks, query) {
            const normalized = String(query || '')
                .trim()
                .toLowerCase();
            if (!normalized) {
                return blocks;
            }
            return blocks.filter((block) =>
                String(block.search_text || `${block.speaker_label || ''} ${block.raw_text || ''}`)
                    .toLowerCase()
                    .includes(normalized),
            );
        },

        jumpToSpeaker(blocks, speakerLabel) {
            return (
                blocks.find(
                    (block) =>
                        String(block.speaker_label || '').toUpperCase() ===
                        String(speakerLabel || '').toUpperCase(),
                ) || null
            );
        },

        jumpToTime(blocks, targetTime) {
            return (
                blocks.find(
                    (block) =>
                        typeof targetTime === 'number' &&
                        targetTime >= block.start_time &&
                        targetTime <= block.end_time,
                ) || null
            );
        },

        neighborBlock(blocks, currentBlockId, direction) {
            const currentIndex = blocks.findIndex((block) => block.id === currentBlockId);
            if (currentIndex === -1) {
                return null;
            }
            const nextIndex = currentIndex + direction;
            return blocks[nextIndex] || null;
        },
    };

    globalScope.transcriptNavigation = transcriptNavigation;
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = transcriptNavigation;
    }
})(typeof window !== 'undefined' ? window : globalThis);
