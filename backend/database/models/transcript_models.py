from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class BlockType(str, Enum):
    COLLOQUY = "COLLOQUY"
    EXAMINATION_Q = "EXAMINATION_Q"
    EXAMINATION_A = "EXAMINATION_A"
    REPORTER_STATEMENT = "REPORTER_STATEMENT"
    INTERPRETER_STATEMENT = "INTERPRETER_STATEMENT"
    PARENTHETICAL = "PARENTHETICAL"
    OBJECTION = "OBJECTION"
    PROCEEDINGS = "PROCEEDINGS"


class TranscriptAssetCreate(BaseModel):
    session_id: int
    asset_type: str
    file_name: str
    file_path: str
    source_format: str | None = None
    deepgram_json_path: str | None = None
    keyterms_path: str | None = None
    preprocessing_metadata_path: str | None = None
    snr_value: float | None = None
    utt_split_value: float | None = None
    is_primary: bool = False


class TranscriptAssetRecord(TranscriptAssetCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class SpeakerSegmentCreate(BaseModel):
    session_id: int
    transcript_asset_id: int | None = None
    speaker_index: int
    speaker_label: str | None = None
    start_time: float
    end_time: float
    confidence: float | None = None


class SpeakerSegmentRecord(SpeakerSegmentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class TranscriptBlockCreate(BaseModel):
    session_id: int
    speaker_segment_id: int | None = None
    block_index: int
    block_type: BlockType
    speaker_index: int | None = None
    raw_text: str
    working_text: str | None = None
    start_time: float
    end_time: float
    confidence: float | None = None
    is_edited: bool = False


class TranscriptBlockRecord(TranscriptBlockCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class WordObjectCreate(BaseModel):
    transcript_block_id: int
    word_index: int
    word_text: str
    modified_text: str | None = None
    start_time: float
    end_time: float
    confidence: float | None = None
    is_filler: bool = False


class WordObjectRecord(WordObjectCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class TranscriptTimelineWord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transcript_block_id: int
    word_index: int
    word_text: str
    modified_text: str | None = None
    start_time: float
    end_time: float
    confidence: float | None = None
    is_filler: bool
    speaker_index: int | None = None
    speaker_label: str | None = None
    block_type: BlockType


class TranscriptTimelineBlock(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    speaker_segment_id: int | None = None
    block_index: int
    block_type: BlockType
    speaker_index: int | None = None
    speaker_label: str | None = None
    raw_text: str
    working_text: str | None = None
    start_time: float
    end_time: float
    confidence: float | None = None
    is_edited: bool
    words: list[TranscriptTimelineWord] = Field(default_factory=list)
