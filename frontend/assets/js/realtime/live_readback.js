window.liveReadback = {
    filter(blocks, query) {
        const normalized = String(query || '')
            .trim()
            .toLowerCase();
        if (!normalized) {
            return blocks;
        }
        return blocks.filter(
            (block) =>
                String(block.raw_text || '')
                    .toLowerCase()
                    .includes(normalized) ||
                String(block.speaker_label || '')
                    .toLowerCase()
                    .includes(normalized),
        );
    },
};
