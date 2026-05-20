window.liveSpeakerView = {
    render(labels) {
        if (!labels.length) {
            return '<p class="muted-copy">No live speakers detected yet.</p>';
        }
        return labels.map((label) => `<span class="issue-flag">${String(label)}</span>`).join('');
    },
};
