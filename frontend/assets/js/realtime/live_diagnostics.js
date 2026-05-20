window.liveDiagnosticsView = {
    render(status) {
        return `
            <div class="stack-item"><strong>Status</strong><span>${escapeHtml(status.stream_status || 'idle')}</span></div>
            <div class="stack-item"><strong>Packets</strong><span>${escapeHtml(String(status.packet_count || 0))}</span></div>
            <div class="stack-item"><strong>Latency</strong><span>${escapeHtml(String(status.last_latency_ms || 0))} ms</span></div>
            <div class="stack-item"><strong>Clients</strong><span>${escapeHtml(String(status.connected_clients || 0))}</span></div>
        `;
    },
};
