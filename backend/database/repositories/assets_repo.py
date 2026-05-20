from __future__ import annotations

from pathlib import Path

from backend.database.connection import open_connection
from backend.database.models.transcript_models import TranscriptAssetCreate, TranscriptAssetRecord


def create_transcript_asset(
    payload: TranscriptAssetCreate,
    database_path: Path | None = None,
) -> TranscriptAssetRecord:
    with open_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO transcript_assets (
                session_id,
                asset_type,
                file_name,
                file_path,
                source_format,
                deepgram_json_path,
                keyterms_path,
                preprocessing_metadata_path,
                snr_value,
                utt_split_value,
                is_primary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.session_id,
                payload.asset_type,
                payload.file_name,
                payload.file_path,
                payload.source_format,
                payload.deepgram_json_path,
                payload.keyterms_path,
                payload.preprocessing_metadata_path,
                payload.snr_value,
                payload.utt_split_value,
                int(payload.is_primary),
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM transcript_assets WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return TranscriptAssetRecord.model_validate(dict(row))


def get_assets_for_session(
    session_id: int,
    database_path: Path | None = None,
) -> list[TranscriptAssetRecord]:
    with open_connection(database_path) as connection:
        rows = connection.execute(
            "SELECT * FROM transcript_assets WHERE session_id = ? ORDER BY id ASC",
            (session_id,),
        ).fetchall()
    return [TranscriptAssetRecord.model_validate(dict(row)) for row in rows]
