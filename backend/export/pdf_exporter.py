from __future__ import annotations

from pathlib import Path


def write_pdf_foundation(rendered_document: dict[str, object], output_path: Path) -> Path:
    lines = ["DEPO-PRO TRANSCRIPT EXPORT", "", *rendered_document["lines"][:40]]
    escaped = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines]
    stream_lines = ["BT", "/F1 10 Tf", "72 760 Td"]
    for index, line in enumerate(escaped):
        if index:
            stream_lines.append("0 -14 Td")
        stream_lines.append(f"({line}) Tj")
    stream_lines.append("ET")
    stream = "\n".join(stream_lines).encode("utf-8")

    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        (
            b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
        ),
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        f"5 0 obj << /Length {len(stream)} >> stream\n".encode("utf-8")
        + stream
        + b"\nendstream endobj\n",
    ]

    header = b"%PDF-1.4\n"
    offsets = []
    cursor = len(header)
    for obj in objects:
        offsets.append(cursor)
        cursor += len(obj)
    xref_offset = cursor
    xref = [b"xref\n0 6\n0000000000 65535 f \n"]
    xref.extend(f"{offset:010d} 00000 n \n".encode("utf-8") for offset in offsets)
    trailer = (
        b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(xref_offset).encode("utf-8")
        + b"\n%%EOF\n"
    )
    output_path.write_bytes(header + b"".join(objects) + b"".join(xref) + trailer)
    return output_path
