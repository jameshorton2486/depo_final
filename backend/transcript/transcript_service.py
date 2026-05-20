from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from backend.config import settings
from backend.database.init_db import initialize_database
from backend.database.models.session_models import SessionCreate
from backend.database.models.transcript_models import TranscriptAssetCreate
from backend.database.repositories.assets_repo import (
    create_transcript_asset,
    get_assets_for_session,
)
from backend.database.repositories.cases_repo import get_case
from backend.database.repositories.sessions_repo import (
    create_session,
    get_session,
    list_sessions_for_case,
)
from backend.database.repositories.transcript_repo import (
    clear_transcript_for_session,
    create_speaker_segment,
    create_transcript_block,
    get_speaker_segments_for_session,
    get_timeline_for_session,
    get_word_object,
    get_word_objects_for_session,
    insert_word_object,
)
from backend.deepgram.prerecorded import transcribe_prerecorded
from backend.deepgram.response_parser import parse_deepgram_response
from backend.deepgram.transcript_mapper import map_transcript_payload
from backend.preprocessing.preprocessing_service import preprocess_media
from backend.transcript.block_builder import build_transcript_block
from backend.transcript.raw_storage import store_raw_payloads
from backend.transcript.speaker_builder import build_speaker_segment
from backend.transcript.word_builder import build_word_object


class TranscriptionRequest(BaseModel):
    case_id: int
    session_id: int | None = None
    file_name: str
    file_content_base64: str
    intake_metadata: dict[str, object] = Field(default_factory=dict)


def transcribe_and_persist(
    request: TranscriptionRequest,
    database_path: Path | None = None,
    data_root: Path | None = None,
    mock: bool | None = None,
) -> dict[str, object]:
    initialize_database(database_path)
    case_record = get_case(request.case_id, database_path)
    session_record = _resolve_session(request, case_record.case_name, database_path)
    resolved_data_root = data_root if data_root is not None else settings.data_root

    preprocessing_metadata = preprocess_media(
        case_id=request.case_id,
        file_name=request.file_name,
        file_content_base64=request.file_content_base64,
        data_root=resolved_data_root,
    )
    final_audio_path = Path(str(preprocessing_metadata["final_audio_path"]))
    deepgram_response = transcribe_prerecorded(
        case_id=request.case_id,
        audio_path=final_audio_path,
        utt_split=float(preprocessing_metadata["calibrated_utt_split"]),
        data_root=resolved_data_root,
        mock=mock,
    )
    request_metadata = dict(deepgram_response.get("_request_metadata", {}))
    raw_storage = store_raw_payloads(
        case_id=request.case_id,
        stem=Path(request.file_name).stem,
        raw_response=deepgram_response,
        request_metadata=request_metadata,
        preprocessing_metadata=preprocessing_metadata,
        data_root=resolved_data_root,
    )
    asset_record = create_transcript_asset(
        TranscriptAssetCreate(
            session_id=session_record.id,
            asset_type=_infer_asset_type(request.file_name),
            file_name=request.file_name,
            file_path=str(final_audio_path),
            source_format=Path(request.file_name).suffix.lstrip(".").lower() or "wav",
            deepgram_json_path=str(raw_storage["raw_json_path"]),
            keyterms_path=request_metadata.get("keyterms_path"),
            preprocessing_metadata_path=str(raw_storage["preprocessing_metadata_path"]),
            snr_value=float(preprocessing_metadata["estimated_snr_db"]),
            utt_split_value=float(preprocessing_metadata["calibrated_utt_split"]),
            is_primary=True,
        ),
        database_path,
    )

    parsed_response = parse_deepgram_response(deepgram_response)
    mapped_payload = map_transcript_payload(
        request.case_id,
        session_record.id,
        asset_record.id,
        parsed_response,
        database_path,
    )
    clear_transcript_for_session(session_record.id, database_path)

    block_records = []
    word_records = []
    speaker_segment_records = []
    for block_payload in mapped_payload["transcript_blocks"]:
        speaker_segment_record = create_speaker_segment(
            build_speaker_segment(block_payload["speaker_segment"]),
            database_path,
        )
        speaker_segment_records.append(speaker_segment_record)
        block_record = create_transcript_block(
            build_transcript_block(block_payload, speaker_segment_record.id),
            database_path,
        )
        block_records.append(block_record)
        for word_payload in block_payload["words"]:
            word_records.append(
                insert_word_object(
                    build_word_object(block_record.id, word_payload),
                    database_path,
                )
            )

    return {
        "case_id": request.case_id,
        "session_id": session_record.id,
        "asset": asset_record.model_dump(mode="json"),
        "preprocessing": preprocessing_metadata,
        "transcript_summary": {
            "block_count": len(block_records),
            "word_count": len(word_records),
            "speaker_count": len({segment.speaker_index for segment in speaker_segment_records}),
            "duration": parsed_response.get("duration"),
        },
    }


def get_transcript(session_id: int, database_path: Path | None = None) -> dict[str, object]:
    session_record = get_session(session_id, database_path)
    timeline = get_timeline_for_session(session_id, database_path)
    assets = get_assets_for_session(session_id, database_path)
    speaker_segments = get_speaker_segments_for_session(session_id, database_path)
    word_objects = get_word_objects_for_session(session_id, database_path)
    return {
        "session": session_record.model_dump(mode="json"),
        "assets": [asset.model_dump(mode="json") for asset in assets],
        "speaker_segments": [segment.model_dump(mode="json") for segment in speaker_segments],
        "transcript_blocks": [block.model_dump(mode="json") for block in timeline],
        "word_objects": [word.model_dump(mode="json") for word in word_objects],
    }


def get_transcript_timeline(
    session_id: int,
    database_path: Path | None = None,
) -> dict[str, object]:
    timeline = get_timeline_for_session(session_id, database_path)
    return {
        "session_id": session_id,
        "timeline": [block.model_dump(mode="json") for block in timeline],
    }


def get_transcript_word(word_id: int, database_path: Path | None = None) -> dict[str, object]:
    return get_word_object(word_id, database_path)


def _resolve_session(
    request: TranscriptionRequest,
    case_name: str,
    database_path: Path | None,
):
    if request.session_id:
        return get_session(request.session_id, database_path)
    sessions = list_sessions_for_case(request.case_id, database_path)
    if sessions:
        return sessions[0]
    session_name = str(request.intake_metadata.get("session_name") or f"{case_name} Session 1")
    return create_session(
        SessionCreate(case_id=request.case_id, session_name=session_name),
        database_path,
    )


def _infer_asset_type(file_name: str) -> str:
    suffix = Path(file_name).suffix.lower()
    if suffix in {".mp4", ".mov", ".avi", ".mkv"}:
        return "video"
    return "audio"
