window.legalReviewDashboardView = {
    render(counts) {
        const entries = Object.entries(counts || {});
        if (!entries.length) {
            return '<p class="muted-copy">No legal review metrics available.</p>';
        }
        return entries
            .map(
                ([label, value]) => `
                <div class="result-card summary-metric">
                    <p class="panel-label">${escapeHtml(label)}</p>
                    <h4>${escapeHtml(String(value))}</h4>
                </div>
            `,
            )
            .join('');
    },
};
