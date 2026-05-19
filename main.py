"""
Depo-Pro desktop launcher.

Opens the HTML workspace at ui/index.html in a native window via PyWebView.
The HTML is fully static in Phase A — no backend yet.
"""
import os

import webview

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(PROJECT_ROOT, "ui", "index.html")

WINDOW_TITLE = "Depo-Pro"
WINDOW_WIDTH = 1600
WINDOW_HEIGHT = 1000
MIN_WIDTH = 1280
MIN_HEIGHT = 800


def main() -> None:
    if not os.path.isfile(HTML_PATH):
        raise FileNotFoundError(f"Expected HTML shell at {HTML_PATH}")

    webview.create_window(
        title=WINDOW_TITLE,
        url=HTML_PATH,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=(MIN_WIDTH, MIN_HEIGHT),
    )
    webview.start(debug=True)


if __name__ == "__main__":
    main()
