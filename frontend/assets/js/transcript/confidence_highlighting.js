(function attachConfidenceHighlighting(globalScope) {
    const transcriptConfidence = {
        thresholds: {
            high: 0.95,
            medium: 0.85,
        },

        classify(confidence) {
            if (typeof confidence !== 'number' || Number.isNaN(confidence)) {
                return 'medium';
            }
            if (confidence >= this.thresholds.high) {
                return 'high';
            }
            if (confidence >= this.thresholds.medium) {
                return 'medium';
            }
            return 'low';
        },

        isReviewCandidate(confidence) {
            return this.classify(confidence) === 'low';
        },
    };

    globalScope.transcriptConfidence = transcriptConfidence;
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = transcriptConfidence;
    }
})(typeof window !== 'undefined' ? window : globalThis);
