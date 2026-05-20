from __future__ import annotations


def build_zoom_rtms_metadata(
    *,
    meeting_id: str | None,
    passcode: str | None,
    source_label: str,
) -> dict[str, object]:
    return {
        "source": source_label,
        "meeting_id": meeting_id,
        "passcode_present": bool(passcode),
        "transport": "websocket",
        "audio_format": "pcm16/16000/mono",
    }
