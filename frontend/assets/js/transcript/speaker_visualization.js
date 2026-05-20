(function attachSpeakerVisualization(globalScope) {
    const transcriptSpeakerVisualization = {
        roleForLabel(label) {
            const normalized = String(label || '').toUpperCase();
            if (normalized === 'THE REPORTER') {
                return 'reporter';
            }
            if (normalized === 'THE INTERPRETER') {
                return 'interpreter';
            }
            if (
                normalized.startsWith('MR.') ||
                normalized.startsWith('MS.') ||
                normalized.startsWith('MRS.')
            ) {
                return 'attorney';
            }
            return 'witness';
        },

        blockClass(label) {
            return `speaker-${this.roleForLabel(label)}`;
        },
    };

    globalScope.transcriptSpeakerVisualization = transcriptSpeakerVisualization;
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = transcriptSpeakerVisualization;
    }
})(typeof window !== 'undefined' ? window : globalThis);
