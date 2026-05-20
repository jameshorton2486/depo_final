from __future__ import annotations

from pathlib import Path

from backend.database.connection import open_connection


def check_session_integrity(
    session_id: int,
    database_path: Path | None = None,
) -> dict[str, object]:
    issues: list[dict[str, object]] = []
    stats = {
        "block_count": 0,
        "word_count": 0,
        "speaker_segment_count": 0,
    }
    with open_connection(database_path) as connection:
        blocks = connection.execute(
            """
            SELECT
                id,
                speaker_segment_id,
                block_index,
                speaker_index,
                start_time,
                end_time,
                confidence
            FROM transcript_blocks
            WHERE session_id = ?
            ORDER BY block_index ASC, id ASC
            """,
            (session_id,),
        ).fetchall()
        stats["block_count"] = len(blocks)
        words = connection.execute(
            """
            SELECT
                word_objects.id,
                word_objects.transcript_block_id,
                word_objects.word_index,
                word_objects.start_time,
                word_objects.end_time,
                word_objects.confidence
            FROM word_objects
            INNER JOIN transcript_blocks
                ON transcript_blocks.id = word_objects.transcript_block_id
            WHERE transcript_blocks.session_id = ?
            ORDER BY transcript_block_id ASC, word_index ASC, word_objects.id ASC
            """,
            (session_id,),
        ).fetchall()
        stats["word_count"] = len(words)
        segments = connection.execute(
            """
            SELECT id, start_time, end_time, confidence
            FROM speaker_segments
            WHERE session_id = ?
            ORDER BY start_time ASC, id ASC
            """,
            (session_id,),
        ).fetchall()
        stats["speaker_segment_count"] = len(segments)

        orphaned_blocks = connection.execute(
            """
            SELECT transcript_blocks.id
            FROM transcript_blocks
            LEFT JOIN sessions ON sessions.id = transcript_blocks.session_id
            WHERE transcript_blocks.session_id = ? AND sessions.id IS NULL
            """,
            (session_id,),
        ).fetchall()

    previous_block_end = None
    previous_block_index = None
    for block in blocks:
        if block["start_time"] > block["end_time"]:
            issues.append(
                _issue(
                    "INVALID_BLOCK_RANGE",
                    "Transcript block start_time exceeds end_time.",
                    entity_id=block["id"],
                )
            )
        confidence = block["confidence"]
        if confidence is not None and not 0 <= float(confidence) <= 1:
            issues.append(
                _issue(
                    "INVALID_BLOCK_CONFIDENCE",
                    "Transcript block confidence must be between 0 and 1.",
                    entity_id=block["id"],
                )
            )
        if previous_block_end is not None and float(block["start_time"]) < float(
            previous_block_end
        ):
            issues.append(
                _issue(
                    "OVERLAPPING_BLOCKS",
                    "Transcript blocks overlap in time order.",
                    entity_id=block["id"],
                    details={
                        "previous_block_index": previous_block_index,
                        "current_block_index": block["block_index"],
                    },
                )
            )
        previous_block_end = block["end_time"]
        previous_block_index = block["block_index"]
        if block["speaker_segment_id"] is None:
            issues.append(
                _issue(
                    "MISSING_SPEAKER_SEGMENT",
                    "Transcript block does not reference a speaker segment.",
                    entity_id=block["id"],
                )
            )

    words_by_block: dict[int, list[object]] = {}
    for word in words:
        words_by_block.setdefault(int(word["transcript_block_id"]), []).append(word)
        if word["start_time"] > word["end_time"]:
            issues.append(
                _issue(
                    "INVALID_WORD_RANGE",
                    "Word timestamp ordering is invalid.",
                    entity_id=word["id"],
                )
            )
        confidence = word["confidence"]
        if confidence is not None and not 0 <= float(confidence) <= 1:
            issues.append(
                _issue(
                    "INVALID_WORD_CONFIDENCE",
                    "Word confidence must be between 0 and 1.",
                    entity_id=word["id"],
                )
            )

    for block_id, block_words in words_by_block.items():
        expected_index = 0
        for word in block_words:
            if int(word["word_index"]) != expected_index:
                issues.append(
                    _issue(
                        "MISSING_WORD_INDEX",
                        "Word indexes are not contiguous within the transcript block.",
                        entity_id=block_id,
                        details={
                            "expected_index": expected_index,
                            "actual_index": word["word_index"],
                        },
                    )
                )
                expected_index = int(word["word_index"])
            expected_index += 1

    for segment in segments:
        if segment["start_time"] > segment["end_time"]:
            issues.append(
                _issue(
                    "INVALID_SPEAKER_RANGE",
                    "Speaker segment start_time exceeds end_time.",
                    entity_id=segment["id"],
                )
            )
        confidence = segment["confidence"]
        if confidence is not None and not 0 <= float(confidence) <= 1:
            issues.append(
                _issue(
                    "INVALID_SPEAKER_CONFIDENCE",
                    "Speaker segment confidence must be between 0 and 1.",
                    entity_id=segment["id"],
                )
            )

    for row in orphaned_blocks:
        issues.append(
            _issue(
                "ORPHANED_TRANSCRIPT_BLOCK",
                "Transcript block is not linked to a valid session.",
                entity_id=row["id"],
            )
        )

    return {
        "session_id": session_id,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "stats": stats,
    }


def scan_transcript_integrity(database_path: Path | None = None) -> dict[str, object]:
    with open_connection(database_path) as connection:
        session_rows = connection.execute("SELECT id FROM sessions ORDER BY id ASC").fetchall()
    reports = [check_session_integrity(int(row["id"]), database_path) for row in session_rows]
    issue_count = sum(int(report["issue_count"]) for report in reports)
    return {
        "ok": issue_count == 0,
        "session_count": len(reports),
        "issue_count": issue_count,
        "reports": reports,
    }


def _issue(
    code: str,
    message: str,
    *,
    entity_id: int,
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "code": code,
        "message": message,
        "entity_id": entity_id,
        "details": details or {},
    }
