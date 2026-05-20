(function attachPlaybackSync(globalScope) {
    const transcriptPlaybackSync = {
        findActiveWord(wordTimeline, currentTime) {
            return (
                wordTimeline.find(
                    (word) => currentTime >= word.start_time && currentTime <= word.end_time,
                ) || null
            );
        },

        seekPlayer(player, timeSeconds) {
            if (!player || typeof timeSeconds !== 'number' || Number.isNaN(timeSeconds)) {
                return null;
            }
            player.currentTime = Math.max(0, timeSeconds);
            return player.currentTime;
        },

        activeState(wordTimeline, currentTime) {
            const activeWord = this.findActiveWord(wordTimeline, currentTime);
            return {
                activeWordId: activeWord ? activeWord.word_id : null,
                activeBlockId: activeWord ? activeWord.block_id : null,
            };
        },
    };

    globalScope.transcriptPlaybackSync = transcriptPlaybackSync;
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = transcriptPlaybackSync;
    }
})(typeof window !== 'undefined' ? window : globalThis);
