from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode

from backend.deepgram.keyterm_loader import load_case_prompting


def build_live_request_config(case_id: int, data_root: Path | None = None) -> dict[str, object]:
    prompting = load_case_prompting(case_id, data_root=data_root)
    return {
        "model": "nova-3",
        "diarize": True,
        "punctuate": True,
        "filler_words": True,
        "interim_results": False,
        "encoding": "linear16",
        "sample_rate": 16000,
        "channels": 1,
        "prompted_terms": prompting["prompted_terms"],
        "keyterms_path": prompting["keyterms_path"],
        "phonetics_path": prompting["phonetics_path"],
    }


def generate_mock_live_events() -> list[dict[str, object]]:
    return [
        {
            "start": 0.0,
            "end": 1.8,
            "confidence": 0.972,
            "speaker": 0,
            "speaker_label": "MR. YANG",
            "transcript": "Please state your name for the record.",
            "words": [
                _word("Please", 0.00, 0.18, 0.98),
                _word("state", 0.19, 0.39, 0.97),
                _word("your", 0.40, 0.55, 0.97),
                _word("name", 0.56, 0.78, 0.98),
                _word("for", 0.79, 0.90, 0.97),
                _word("the", 0.91, 1.02, 0.97),
                _word("record.", 1.03, 1.31, 0.97),
            ],
        },
        {
            "start": 2.0,
            "end": 3.9,
            "confidence": 0.848,
            "speaker": 1,
            "speaker_label": "THE WITNESS",
            "transcript": "My name is Heath Thomas.",
            "words": [
                _word("My", 2.00, 2.12, 0.96),
                _word("name", 2.13, 2.32, 0.95),
                _word("is", 2.33, 2.42, 0.95),
                _word("Heath", 2.43, 2.74, 0.82),
                _word("Thomas.", 2.75, 3.10, 0.83),
            ],
        },
        {
            "start": 4.2,
            "end": 6.4,
            "confidence": 0.915,
            "speaker": 0,
            "speaker_label": "MR. YANG",
            "transcript": "Have you ever given a deposition before?",
            "words": [
                _word("Have", 4.20, 4.38, 0.94),
                _word("you", 4.39, 4.52, 0.94),
                _word("ever", 4.53, 4.74, 0.93),
                _word("given", 4.75, 5.02, 0.93),
                _word("a", 5.03, 5.10, 0.93),
                _word("deposition", 5.11, 5.58, 0.88),
                _word("before?", 5.59, 5.94, 0.91),
            ],
        },
    ]


def build_live_request_url(prompted_terms: list[str]) -> str:
    params: list[tuple[str, str]] = [
        ("model", "nova-3"),
        ("diarize", "true"),
        ("punctuate", "true"),
        ("filler_words", "true"),
        ("interim_results", "false"),
        ("encoding", "linear16"),
        ("sample_rate", "16000"),
        ("channels", "1"),
    ]
    params.extend(("keyterm", term) for term in prompted_terms[:100])
    return f"wss://api.deepgram.com/v1/listen?{urlencode(params, doseq=True)}"


def _word(token: str, start: float, end: float, confidence: float) -> dict[str, object]:
    return {
        "word": token.rstrip(".,?!"),
        "punctuated_word": token,
        "start": start,
        "end": end,
        "confidence": confidence,
    }
