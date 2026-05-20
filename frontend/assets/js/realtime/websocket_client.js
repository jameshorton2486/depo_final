window.realtimeWebSocketClient = {
    connect(sessionId, handlers) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const socket = new WebSocket(
            `${protocol}//${window.location.host}/ws/transcript/${sessionId}`,
        );
        socket.addEventListener('open', () => handlers.onOpen?.());
        socket.addEventListener('close', () => handlers.onClose?.());
        socket.addEventListener('message', (event) => {
            handlers.onMessage?.(JSON.parse(event.data));
        });
        return socket;
    },
};
