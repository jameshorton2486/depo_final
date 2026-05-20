window.liveBufferStore = {
    snapshot(payload) {
        return {
            timeline: payload.timeline || [],
            wordTimeline: payload.word_timeline || [],
            speakerLabels: payload.speaker_labels || [],
            packetCount: payload.packet_count || 0,
            lastLatencyMs: payload.last_latency_ms || 0,
            status: payload.stream_status || 'idle',
        };
    },
    append(state, block) {
        state.timeline = [...state.timeline, block];
        state.wordTimeline = [
            ...state.wordTimeline,
            ...(block.words || []).map((word) => ({
                wordId: word.id,
                blockId: block.id,
                startTime: word.start_time,
                endTime: word.end_time,
                speakerLabel: block.speaker_label,
                wordText: word.word_text,
                confidence: word.confidence,
            })),
        ];
        if (block.speaker_label && !state.speakerLabels.includes(block.speaker_label)) {
            state.speakerLabels = [...state.speakerLabels, block.speaker_label];
        }
        return state;
    },
};
