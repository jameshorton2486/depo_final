from __future__ import annotations

from pathlib import Path

from backend.database.connection import open_connection
from backend.database.repositories.transcript_repo import get_timeline_for_session
from backend.review.confidence_service import classify_confidence
from backend.review.issue_classifier import classify_block_issues, classify_word_issues


def ensure_review_queue(
    session_id: int,
    database_path: Path | None = None,
) -> list[dict[str, object]]:
    timeline_models = get_timeline_for_session(session_id, database_path)
    timeline = []
    for block in timeline_models:
        payload = block.model_dump(mode="json")
        payload["confidence_class"] = classify_confidence(payload.get("confidence"))
        for word in payload.get("words", []):
            word["confidence_class"] = classify_confidence(word.get("confidence"))
        timeline.append(payload)
    _create_missing_flags(timeline, session_id, database_path)
    return list_review_queue(session_id, database_path)


def list_review_queue(
    session_id: int,
    database_path: Path | None = None,
) -> list[dict[str, object]]:
    with open_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT
                review_flags.*,
                word_objects.word_text,
                word_objects.modified_text,
                word_objects.start_time,
                word_objects.end_time,
                word_objects.confidence,
                transcript_blocks.block_type,
                transcript_blocks.block_index,
                transcript_blocks.speaker_index,
                speaker_segments.speaker_label
            FROM review_flags
            LEFT JOIN word_objects
                ON word_objects.id = review_flags.word_object_id
            LEFT JOIN transcript_blocks
                ON transcript_blocks.id = COALESCE(
                    review_flags.transcript_block_id,
                    word_objects.transcript_block_id
                )
            LEFT JOIN speaker_segments
                ON speaker_segments.id = COALESCE(
                    review_flags.speaker_segment_id,
                    transcript_blocks.speaker_segment_id
                )
            WHERE review_flags.session_id = ?
            ORDER BY
                CASE review_flags.status WHEN 'open' THEN 0 WHEN 'reviewed' THEN 1 ELSE 2 END,
                transcript_blocks.block_index ASC,
                word_objects.word_index ASC,
                review_flags.id ASC
            """,
            (session_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def _create_missing_flags(
    timeline: list[dict[str, object]],
    session_id: int,
    database_path: Path | None,
) -> None:
    with open_connection(database_path) as connection:
        existing_keys = {
            (
                row["word_object_id"],
                row["transcript_block_id"],
                row["speaker_segment_id"],
                row["issue_category"],
            )
            for row in connection.execute(
                """
                SELECT word_object_id, transcript_block_id, speaker_segment_id, issue_category
                FROM review_flags
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchall()
        }

        for block in timeline:
            block_issues = classify_block_issues(block)
            for issue in block_issues:
                key = (None, block["id"], block.get("speaker_segment_id"), issue.value)
                if key in existing_keys:
                    continue
                connection.execute(
                    """
                    INSERT INTO review_flags (
                        session_id,
                        transcript_block_id,
                        speaker_segment_id,
                        issue_category,
                        confidence_level,
                        original_value,
                        current_value
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        block["id"],
                        block.get("speaker_segment_id"),
                        issue.value,
                        block.get("confidence_class"),
                        block.get("raw_text"),
                        block.get("working_text") or block.get("raw_text"),
                    ),
                )
                existing_keys.add(key)

            for word in block.get("words", []):
                issues = classify_word_issues(word, block)
                for issue in issues:
                    key = (word["id"], block["id"], block.get("speaker_segment_id"), issue.value)
                    if key in existing_keys:
                        continue
                    connection.execute(
                        """
                        INSERT INTO review_flags (
                            session_id,
                            word_object_id,
                            transcript_block_id,
                            speaker_segment_id,
                            issue_category,
                            confidence_level,
                            original_value,
                            current_value
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            session_id,
                            word["id"],
                            block["id"],
                            block.get("speaker_segment_id"),
                            issue.value,
                            word.get("confidence_class"),
                            word.get("word_text"),
                            word.get("modified_text") or word.get("word_text"),
                        ),
                    )
                    existing_keys.add(key)
        connection.commit()
