"""Depo-Pro desktop launcher (Phase A.1)."""
import http.server
import os
import socketserver
import threading
import time

import webview

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
UI_ROOT = os.path.join(PROJECT_ROOT, "ui")
PORT = 47853  # Arbitrary, unlikely to collide

WINDOW_TITLE = "Depo-Pro"
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 1000
MIN_WIDTH = 1280
MIN_HEIGHT = 800


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Silence per-request log spam


def start_local_server():
    handler = lambda *a, **kw: QuietHandler(*a, directory=UI_ROOT, **kw)
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


def main() -> None:
    index_path = os.path.join(UI_ROOT, "index.html")
    if not os.path.isfile(index_path):
        raise FileNotFoundError(f"Expected HTML shell at {index_path}")

    start_local_server()
    time.sleep(0.3)  # Give the server a beat to bind

    webview.create_window(
        title=WINDOW_TITLE,
        url=f"http://127.0.0.1:{PORT}/index.html",
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=(MIN_WIDTH, MIN_HEIGHT),
    )
    webview.start(debug=True)


if __name__ == "__main__":
    main()
