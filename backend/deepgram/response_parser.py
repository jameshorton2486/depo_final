from __future__ import annotations

FILLER_WORDS = {"uh", "um", "mhmm", "mm-mm", "uh-uh", "uh-huh", "nuh-uh"}


def parse_deepgram_response(payload: dict[str, object]) -> dict[str, object]:
    results = payload.get("results", {}) if isinstance(payload, dict) else {}
    metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
    utterances = results.get("utterances", []) if isinstance(results, dict) else []
    parsed_utterances: list[dict[str, object]] = []

    for index, utterance in enumerate(utterances):
        words = []
        for word_index, word in enumerate(utterance.get("words", [])):
            word_text = str(word.get("punctuated_word") or word.get("word") or "").strip()
            base_word = str(word.get("word") or word_text).strip()
            words.append(
                {
                    "word_index": word_index,
                    "word_text": word_text or base_word,
                    "modified_text": None,
                    "start_time": float(word.get("start", utterance.get("start", 0.0))),
                    "end_time": float(word.get("end", utterance.get("end", 0.0))),
                    "confidence": float(word.get("confidence", utterance.get("confidence", 0.0))),
                    "is_filler": base_word.lower() in FILLER_WORDS,
                    "speaker_index": word.get("speaker", utterance.get("speaker")),
                }
            )
        parsed_utterances.append(
            {
                "utterance_index": index,
                "speaker_index": utterance.get("speaker"),
                "start_time": float(utterance.get("start", 0.0)),
                "end_time": float(utterance.get("end", 0.0)),
                "confidence": float(utterance.get("confidence", 0.0)),
                "transcript": str(utterance.get("transcript", "")).strip(),
                "words": words,
            }
        )

    return {
        "duration": metadata.get("duration"),
        "request_id": metadata.get("request_id"),
        "utterances": parsed_utterances,
        "word_count": sum(len(item["words"]) for item in parsed_utterances),
        "speaker_count": len(
            {
                item["speaker_index"]
                for item in parsed_utterances
                if item.get("speaker_index") is not None
            }
        ),
    }
