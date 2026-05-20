from __future__ import annotations

from pathlib import Path


def write_txt_export(rendered_document: dict[str, object], output_path: Path) -> Path:
    content = (
        "\n".join(
            [
                *rendered_document["certificate_lines"],
                "",
                "TRANSCRIPT",
                "",
                *rendered_document["lines"],
                "",
                "EXHIBIT INDEX",
                *[
                    f"{entry['label']} - {entry['description']}"
                    for entry in rendered_document["exhibit_index"]
                ],
            ]
        ).strip()
        + "\n"
    )
    output_path.write_text(content, encoding="utf-8")
    return output_path
