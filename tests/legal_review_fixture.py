from __future__ import annotations

import base64
import math
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from backend.database.init_db import initialize_database
from backend.database.models.case_models import CaseCreate
from backend.database.models.session_models import SessionCreate
from backend.database.models.transcript_models import (
    BlockType,
    SpeakerSegmentCreate,
    TranscriptBlockCreate,
)
from backend.database.repositories.cases_repo import create_case
from backend.database.repositories.sessions_repo import create_session
from backend.database.repositories.transcript_repo import (
    create_speaker_segment,
    create_transcript_block,
)
from backend.transcript.transcript_service import TranscriptionRequest, transcribe_and_persist


def build_transcribed_session(prefix: str) -> dict[str, object]:
    temp_dir = tempfile.TemporaryDirectory()
    root = Path(temp_dir.name)
    database_path = root / f"{prefix}.db"
    data_root = root / "data"
    initialize_database(database_path)
    case_record = create_case(CaseCreate(case_name=f"{prefix} Matter"), database_path)
    session_record = create_session(
        SessionCreate(case_id=case_record.id, session_name="Session 1"),
        database_path,
    )
    audio_path = _make_audio(root / f"{prefix}.wav")
    transcribe_and_persist(
        TranscriptionRequest(
            case_id=case_record.id,
            session_id=session_record.id,
            file_name=audio_path.name,
            file_content_base64=base64.b64encode(audio_path.read_bytes()).decode("utf-8"),
        ),
        database_path=database_path,
        data_root=data_root,
        mock=True,
    )
    return {
        "temp_dir": temp_dir,
        "root": root,
        "database_path": database_path,
        "data_root": data_root,
        "case_record": case_record,
        "session_record": session_record,
    }


def add_interpreter_block(session_id: int, database_path: Path) -> int:
    speaker_segment = create_speaker_segment(
        SpeakerSegmentCreate(
            session_id=session_id,
            speaker_index=9,
            speaker_label="THE INTERPRETER",
            start_time=9.0,
            end_time=10.0,
            confidence=0.97,
        ),
        database_path,
    )
    block = create_transcript_block(
        TranscriptBlockCreate(
            session_id=session_id,
            speaker_segment_id=speaker_segment.id,
            block_index=999,
            block_type=BlockType.INTERPRETER_STATEMENT,
            speaker_index=9,
            raw_text="Interpreted from Thai to English.",
            working_text=None,
            start_time=9.0,
            end_time=10.0,
            confidence=0.97,
            is_edited=False,
        ),
        database_path,
    )
    return block.id


def _make_audio(path: Path) -> Path:
    sample_rate = 16000
    timeline = np.arange(sample_rate * 8) / sample_rate
    samples = (0.18 * np.sin(2 * math.pi * 205 * timeline)).astype(np.float32)
    samples[:sample_rate] = 0.0
    sf.write(str(path), samples, sample_rate)
    return path
