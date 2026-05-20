from __future__ import annotations

from pathlib import Path

from backend.database.connection import open_connection
from backend.database.models.transcript_models import (
    TranscriptBlockCreate,
    TranscriptBlockRecord,
    WordObjectCreate,
    WordObjectRecord,
)


def create_transcript_block(
    payload: TranscriptBlockCreate,
    database_path: Path | None = None,
) -> TranscriptBlockRecord:
    with open_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO transcript_blocks (
                session_id,
                speaker_segment_id,
                block_index,
                block_type,
                speaker_index,
                raw_text,
                working_text,
                start_time,
                end_time,
                confidence,
                is_edited
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.session_id,
                payload.speaker_segment_id,
                payload.block_index,
                payload.block_type.value,
                payload.speaker_index,
                payload.raw_text,
                payload.working_text,
                payload.start_time,
                payload.end_time,
                payload.confidence,
                int(payload.is_edited),
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM transcript_blocks WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return TranscriptBlockRecord.model_validate(dict(row))


def insert_word_object(
    payload: WordObjectCreate,
    database_path: Path | None = None,
) -> WordObjectRecord:
    with open_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO word_objects (
                transcript_block_id,
                word_index,
                word_text,
                modified_text,
                start_time,
                end_time,
                confidence,
                is_filler
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.transcript_block_id,
                payload.word_index,
                payload.word_text,
                payload.modified_text,
                payload.start_time,
                payload.end_time,
                payload.confidence,
                int(payload.is_filler),
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM word_objects WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return WordObjectRecord.model_validate(dict(row))


def get_blocks_for_session(
    session_id: int,
    database_path: Path | None = None,
) -> list[TranscriptBlockRecord]:
    with open_connection(database_path) as connection:
        rows = connection.execute(
            "SELECT * FROM transcript_blocks WHERE session_id = ? ORDER BY block_index ASC, id ASC",
            (session_id,),
        ).fetchall()
    return [TranscriptBlockRecord.model_validate(dict(row)) for row in rows]
