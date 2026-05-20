from __future__ import annotations

from pathlib import Path

from backend.database.connection import open_connection


def get_performance_metrics(
    session_id: int | None = None,
    database_path: Path | None = None,
) -> dict[str, object]:
    session_filter = ""
    params: tuple[object, ...] = ()
    if session_id is not None:
        session_filter = "WHERE transcript_blocks.session_id = ?"
        params = (session_id,)
    event_filter = ""
    event_params: tuple[object, ...] = ()
    if session_id is not None:
        event_filter = "WHERE session_id = ?"
        event_params = (session_id,)
    with open_connection(database_path) as connection:
        block_rows = connection.execute(
            f"""
            SELECT transcript_blocks.session_id, COUNT(*) AS block_count
            FROM transcript_blocks
            {session_filter}
            GROUP BY transcript_blocks.session_id
            ORDER BY transcript_blocks.session_id ASC
            """,
            params,
        ).fetchall()
        word_rows = connection.execute(
            f"""
            SELECT transcript_blocks.session_id,
                   COUNT(word_objects.id) AS word_count,
                   SUM(
                       CASE
                           WHEN word_objects.confidence < 0.85 THEN 1
                           ELSE 0
                       END
                   ) AS low_confidence_words
            FROM transcript_blocks
            LEFT JOIN word_objects ON word_objects.transcript_block_id = transcript_blocks.id
            {session_filter}
            GROUP BY transcript_blocks.session_id
            ORDER BY transcript_blocks.session_id ASC
            """,
            params,
        ).fetchall()
        event_rows = connection.execute(
            f"""
            SELECT session_id, COUNT(*) AS event_count
            FROM session_events
            {event_filter}
            GROUP BY session_id
            ORDER BY session_id ASC
            """,
            event_params,
        ).fetchall()

    block_map = {int(row["session_id"]): int(row["block_count"]) for row in block_rows}
    word_map = {
        int(row["session_id"]): {
            "word_count": int(row["word_count"] or 0),
            "low_confidence_words": int(row["low_confidence_words"] or 0),
        }
        for row in word_rows
    }
    event_map = {int(row["session_id"]): int(row["event_count"]) for row in event_rows}
    session_ids = sorted(set(block_map) | set(word_map) | set(event_map))
    sessions: list[dict[str, object]] = []
    for current_session_id in session_ids:
        block_count = block_map.get(current_session_id, 0)
        word_count = word_map.get(current_session_id, {}).get("word_count", 0)
        sessions.append(
            {
                "session_id": current_session_id,
                "block_count": block_count,
                "word_count": word_count,
                "low_confidence_words": word_map.get(current_session_id, {}).get(
                    "low_confidence_words", 0
                ),
                "event_count": event_map.get(current_session_id, 0),
                "average_words_per_block": (
                    round(word_count / block_count, 2) if block_count else 0.0
                ),
            }
        )
    largest_session = max(sessions, key=lambda item: item["word_count"], default=None)
    return {
        "session_count": len(sessions),
        "sessions": sessions,
        "largest_session": largest_session,
    }
