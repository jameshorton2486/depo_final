from __future__ import annotations

from pathlib import Path

from backend.database.connection import open_connection
from backend.database.models.transcript_models import (
    SpeakerSegmentCreate,
    SpeakerSegmentRecord,
    TranscriptBlockCreate,
    TranscriptBlockRecord,
    TranscriptTimelineBlock,
    TranscriptTimelineWord,
    WordObjectCreate,
    WordObjectRecord,
)


def clear_transcript_for_session(
    session_id: int,
    database_path: Path | None = None,
) -> None:
    with open_connection(database_path) as connection:
        connection.execute("DELETE FROM transcript_blocks WHERE session_id = ?", (session_id,))
        connection.execute("DELETE FROM speaker_segments WHERE session_id = ?", (session_id,))
        connection.commit()


def create_speaker_segment(
    payload: SpeakerSegmentCreate,
    database_path: Path | None = None,
) -> SpeakerSegmentRecord:
    with open_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO speaker_segments (
                session_id,
                transcript_asset_id,
                speaker_index,
                speaker_label,
                start_time,
                end_time,
                confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.session_id,
                payload.transcript_asset_id,
                payload.speaker_index,
                payload.speaker_label,
                payload.start_time,
                payload.end_time,
                payload.confidence,
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM speaker_segments WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return SpeakerSegmentRecord.model_validate(dict(row))


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


def get_speaker_segments_for_session(
    session_id: int,
    database_path: Path | None = None,
) -> list[SpeakerSegmentRecord]:
    with open_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM speaker_segments
            WHERE session_id = ?
            ORDER BY start_time ASC, id ASC
            """,
            (session_id,),
        ).fetchall()
    return [SpeakerSegmentRecord.model_validate(dict(row)) for row in rows]


def get_word_objects_for_session(
    session_id: int,
    database_path: Path | None = None,
) -> list[WordObjectRecord]:
    with open_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT word_objects.*
            FROM word_objects
            INNER JOIN transcript_blocks
                ON transcript_blocks.id = word_objects.transcript_block_id
            WHERE transcript_blocks.session_id = ?
            ORDER BY transcript_blocks.block_index ASC,
                     word_objects.word_index ASC,
                     word_objects.id ASC
            """,
            (session_id,),
        ).fetchall()
    return [WordObjectRecord.model_validate(dict(row)) for row in rows]


def get_word_object(
    word_id: int,
    database_path: Path | None = None,
) -> dict[str, object]:
    with open_connection(database_path) as connection:
        row = connection.execute(
            """
            SELECT
                word_objects.*,
                transcript_blocks.session_id,
                transcript_blocks.block_type,
                transcript_blocks.speaker_index,
                transcript_blocks.speaker_segment_id,
                speaker_segments.speaker_label
            FROM word_objects
            INNER JOIN transcript_blocks
                ON transcript_blocks.id = word_objects.transcript_block_id
            LEFT JOIN speaker_segments
                ON speaker_segments.id = transcript_blocks.speaker_segment_id
            WHERE word_objects.id = ?
            """,
            (word_id,),
        ).fetchone()
    if row is None:
        raise LookupError(f"Word {word_id} was not found.")
    payload = dict(row)
    payload["block_type"] = str(payload["block_type"])
    return payload


def get_timeline_for_session(
    session_id: int,
    database_path: Path | None = None,
) -> list[TranscriptTimelineBlock]:
    with open_connection(database_path) as connection:
        block_rows = connection.execute(
            """
            SELECT
                transcript_blocks.*,
                speaker_segments.speaker_label
            FROM transcript_blocks
            LEFT JOIN speaker_segments
                ON speaker_segments.id = transcript_blocks.speaker_segment_id
            WHERE transcript_blocks.session_id = ?
            ORDER BY transcript_blocks.block_index ASC, transcript_blocks.id ASC
            """,
            (session_id,),
        ).fetchall()
        word_rows = connection.execute(
            """
            SELECT
                word_objects.*,
                transcript_blocks.block_type,
                transcript_blocks.speaker_index,
                speaker_segments.speaker_label
            FROM word_objects
            INNER JOIN transcript_blocks
                ON transcript_blocks.id = word_objects.transcript_block_id
            LEFT JOIN speaker_segments
                ON speaker_segments.id = transcript_blocks.speaker_segment_id
            WHERE transcript_blocks.session_id = ?
            ORDER BY transcript_blocks.block_index ASC,
                     word_objects.word_index ASC,
                     word_objects.id ASC
            """,
            (session_id,),
        ).fetchall()

    words_by_block: dict[int, list[TranscriptTimelineWord]] = {}
    for row in word_rows:
        payload = dict(row)
        block_id = int(payload["transcript_block_id"])
        payload["block_type"] = str(payload["block_type"])
        words_by_block.setdefault(block_id, []).append(
            TranscriptTimelineWord.model_validate(payload)
        )

    timeline: list[TranscriptTimelineBlock] = []
    for row in block_rows:
        payload = dict(row)
        payload["words"] = words_by_block.get(int(payload["id"]), [])
        timeline.append(TranscriptTimelineBlock.model_validate(payload))
    return timeline


def update_word_modified_text(
    word_id: int,
    modified_text: str | None,
    database_path: Path | None = None,
) -> WordObjectRecord:
    with open_connection(database_path) as connection:
        connection.execute(
            "UPDATE word_objects SET modified_text = ? WHERE id = ?",
            (modified_text, word_id),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM word_objects WHERE id = ?", (word_id,)).fetchone()
    if row is None:
        raise LookupError(f"Word {word_id} was not found.")
    return WordObjectRecord.model_validate(dict(row))


def rebuild_block_working_text(
    transcript_block_id: int,
    database_path: Path | None = None,
) -> TranscriptBlockRecord:
    with open_connection(database_path) as connection:
        words = connection.execute(
            """
            SELECT word_text, modified_text
            FROM word_objects
            WHERE transcript_block_id = ?
            ORDER BY word_index ASC, id ASC
            """,
            (transcript_block_id,),
        ).fetchall()
        if not words:
            raise LookupError(f"Transcript block {transcript_block_id} was not found.")
        working_text = " ".join(
            str(word["modified_text"] or word["word_text"]).strip() for word in words
        ).strip()
        connection.execute(
            """
            UPDATE transcript_blocks
            SET working_text = ?, is_edited = ?, confidence = confidence
            WHERE id = ?
            """,
            (working_text or None, int(bool(working_text)), transcript_block_id),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM transcript_blocks WHERE id = ?",
            (transcript_block_id,),
        ).fetchone()
    if row is None:
        raise LookupError(f"Transcript block {transcript_block_id} was not found.")
    return TranscriptBlockRecord.model_validate(dict(row))


def update_block_working_text(
    transcript_block_id: int,
    working_text: str | None,
    database_path: Path | None = None,
) -> TranscriptBlockRecord:
    with open_connection(database_path) as connection:
        connection.execute(
            """
            UPDATE transcript_blocks
            SET working_text = ?, is_edited = ?
            WHERE id = ?
            """,
            (working_text, int(bool(working_text)), transcript_block_id),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM transcript_blocks WHERE id = ?",
            (transcript_block_id,),
        ).fetchone()
    if row is None:
        raise LookupError(f"Transcript block {transcript_block_id} was not found.")
    return TranscriptBlockRecord.model_validate(dict(row))
