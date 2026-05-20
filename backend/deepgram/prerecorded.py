from __future__ import annotations

import json
import uuid
from pathlib import Path
from urllib.request import Request, urlopen

import soundfile as sf

from backend.config import settings
from backend.deepgram.keyterm_loader import load_case_prompting
from backend.deepgram.request_builder import build_prerecorded_request_url


def transcribe_prerecorded(
    *,
    case_id: int,
    audio_path: Path,
    utt_split: float,
    data_root: Path | None = None,
    mock: bool | None = None,
) -> dict[str, object]:
    prompting = load_case_prompting(case_id, data_root=data_root)
    should_mock = settings.transcribe_mock if mock is None else mock
    request_metadata = {
        "model": "nova-3",
        "punctuate": True,
        "paragraphs": True,
        "diarize": True,
        "filler_words": True,
        "utterances": True,
        "utt_split": utt_split,
        "prompted_terms": prompting["prompted_terms"],
        "keyterms_path": prompting["keyterms_path"],
        "phonetics_path": prompting["phonetics_path"],
    }
    if should_mock:
        return _mock_response(audio_path, request_metadata)
    if not settings.deepgram_api_key:
        raise RuntimeError("DEEPGRAM_API_KEY is not configured for prerecorded transcription.")

    request = Request(
        build_prerecorded_request_url(
            utt_split=utt_split,
            prompted_terms=list(prompting["prompted_terms"]),
        ),
        data=audio_path.read_bytes(),
        headers={
            "Authorization": f"Token {settings.deepgram_api_key}",
            "Content-Type": "audio/wav",
        },
        method="POST",
    )
    with urlopen(request, timeout=300) as response:
        payload = json.loads(response.read().decode("utf-8"))
    payload["_request_metadata"] = request_metadata
    return payload


def _mock_response(audio_path: Path, request_metadata: dict[str, object]) -> dict[str, object]:
    info = sf.info(str(audio_path))
    duration = round(float(info.duration), 3)
    utterances = [
        {
            "start": 0.0,
            "end": min(duration, 2.1),
            "confidence": 0.962,
            "speaker": 0,
            "transcript": "Please state your name for the record.",
            "words": [
                _word("Please", 0.0, 0.22, 0, 0.98),
                _word("state", 0.23, 0.42, 0, 0.97),
                _word("your", 0.43, 0.57, 0, 0.97),
                _word("name", 0.58, 0.79, 0, 0.98),
                _word("for", 0.8, 0.92, 0, 0.96),
                _word("the", 0.93, 1.03, 0, 0.96),
                _word("record.", 1.04, 1.32, 0, 0.97),
            ],
        },
        {
            "start": min(duration, 2.6),
            "end": min(duration, 4.9),
            "confidence": 0.844,
            "speaker": 1,
            "transcript": "My name is Heath Thomas.",
            "words": [
                _word("My", 2.6, 2.74, 1, 0.96),
                _word("name", 2.75, 2.96, 1, 0.95),
                _word("is", 2.97, 3.08, 1, 0.95),
                _word("Heath", 3.09, 3.42, 1, 0.82),
                _word("Thomas.", 3.43, 3.89, 1, 0.83),
            ],
        },
        {
            "start": min(duration, 5.5),
            "end": min(duration, 7.9),
            "confidence": 0.917,
            "speaker": 0,
            "transcript": "Have you ever given a deposition before?",
            "words": [
                _word("Have", 5.5, 5.68, 0, 0.94),
                _word("you", 5.69, 5.83, 0, 0.94),
                _word("ever", 5.84, 6.08, 0, 0.93),
                _word("given", 6.09, 6.36, 0, 0.93),
                _word("a", 6.37, 6.43, 0, 0.93),
                _word("deposition", 6.44, 6.92, 0, 0.88),
                _word("before?", 6.93, 7.32, 0, 0.91),
            ],
        },
    ]
    return {
        "metadata": {
            "request_id": str(uuid.uuid4()),
            "duration": duration,
            "model_info": {"name": "nova-3", "mock": True},
        },
        "results": {
            "utterances": utterances,
        },
        "_request_metadata": request_metadata,
    }


def _word(
    token: str,
    start: float,
    end: float,
    speaker: int,
    confidence: float,
) -> dict[str, object]:
    return {
        "word": token.rstrip(".,?!"),
        "punctuated_word": token,
        "start": start,
        "end": end,
        "speaker": speaker,
        "confidence": confidence,
    }
