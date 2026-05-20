(function attachSpeakerReview(globalScope) {
    function fallbackEscape(value) {
        return String(value)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;')
            .replaceAll("'", '&#39;');
    }

    const reviewSpeakerReview = {
        render(selectedItem) {
            const escapeHtml = globalScope.escapeHtml || fallbackEscape;
            if (!selectedItem) {
                return '<p class="muted-copy">Select a review item to prepare a speaker correction.</p>';
            }
            return `
                <div class="stack-item">
                    <strong>Selected Item</strong>
                    <span>${escapeHtml(selectedItem.issue_category || 'Review item')}</span>
                </div>
                <label class="field-group">
                    <span class="field-label">Corrected Speaker Label</span>
                    <input id="workspaceCorrectedSpeakerLabel" class="text-input" type="text" value="${escapeHtml(selectedItem.speaker_label || '')}">
                </label>
                <label class="field-group">
                    <span class="field-label">Corrected Role</span>
                    <input id="workspaceCorrectedSpeakerRole" class="text-input" type="text" placeholder="attorney / witness / reporter / interpreter">
                </label>
                <button id="workspaceSpeakerCorrectionButton" class="secondary-button" type="button">Apply Speaker Correction</button>
            `;
        },
    };

    globalScope.reviewSpeakerReview = reviewSpeakerReview;
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = reviewSpeakerReview;
    }
})(typeof window !== 'undefined' ? window : globalThis);
