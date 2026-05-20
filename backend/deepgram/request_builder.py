from __future__ import annotations

from urllib.parse import urlencode


def build_prerecorded_request_url(
    *,
    utt_split: float,
    prompted_terms: list[str],
) -> str:
    params: list[tuple[str, str]] = [
        ("model", "nova-3"),
        ("punctuate", "true"),
        ("paragraphs", "true"),
        ("diarize", "true"),
        ("filler_words", "true"),
        ("utterances", "true"),
        ("utt_split", f"{utt_split:.3f}"),
    ]
    params.extend(("keyterm", term) for term in prompted_terms[:100])
    return f"https://api.deepgram.com/v1/listen?{urlencode(params, doseq=True)}"
