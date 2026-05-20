from __future__ import annotations

from math import ceil


def paginate_lines(lines: list[str], lines_per_page: int = 25) -> list[dict[str, object]]:
    if lines_per_page <= 0:
        raise ValueError("lines_per_page must be positive.")
    pages: list[dict[str, object]] = []
    page_total = ceil(len(lines) / lines_per_page) if lines else 1
    for page_index in range(page_total):
        start = page_index * lines_per_page
        end = start + lines_per_page
        page_lines = lines[start:end]
        pages.append(
            {
                "page_number": page_index + 1,
                "line_start": start + 1,
                "line_end": start + len(page_lines),
                "lines": page_lines,
            }
        )
    return pages
