from __future__ import annotations

from pathlib import Path

from backend.database.connection import open_connection


def list_colloquy_groups(
    session_id: int,
    database_path: Path | None = None,
) -> list[dict[str, object]]:
    with open_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT
                transcript_blocks.id,
                transcript_blocks.block_index,
                transcript_blocks.block_type,
                transcript_blocks.start_time,
                transcript_blocks.end_time,
                transcript_blocks.raw_text,
                speaker_segments.speaker_label
            FROM transcript_blocks
            LEFT JOIN speaker_segments
                ON speaker_segments.id = transcript_blocks.speaker_segment_id
            WHERE transcript_blocks.session_id = ?
              AND transcript_blocks.block_type IN (
                'COLLOQUY',
                'PROCEEDINGS',
                'REPORTER_STATEMENT',
                'OBJECTION',
                'INTERPRETER_STATEMENT'
              )
            ORDER BY transcript_blocks.block_index ASC
            """,
            (session_id,),
        ).fetchall()

    groups: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    for row in rows:
        label = row["speaker_label"] or row["block_type"]
        if current and current["speaker_label"] == label:
            current["block_ids"].append(row["id"])
            current["end_time"] = row["end_time"]
            current["text"].append(row["raw_text"])
            continue
        current = {
            "speaker_label": label,
            "block_ids": [row["id"]],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "text": [row["raw_text"]],
        }
        groups.append(current)
    for group in groups:
        group["text"] = " ".join(group["text"]).strip()
    return groups
