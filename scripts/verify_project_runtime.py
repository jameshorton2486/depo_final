from __future__ import annotations

import base64
import json
import math
import os
import struct
import subprocess
import tempfile
import time
import urllib.request
import wave


def _post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return json.loads(urllib.request.urlopen(request).read().decode("utf-8"))


def _get_json(url: str) -> dict[str, object]:
    return json.loads(urllib.request.urlopen(url).read().decode("utf-8"))


def main() -> None:
    env = dict(os.environ)
    env["DEPO_PRO_TRANSCRIBE_MOCK"] = "1"
    process = subprocess.Popen(
        [
            r".\.venv\Scripts\python.exe",
            "-m",
            "uvicorn",
            "backend.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
        ],
        env=env,
    )
    try:
        time.sleep(2)
        health = _get_json("http://127.0.0.1:8765/api/health")
        db_status = _get_json("http://127.0.0.1:8765/api/db/status")
        stage1 = urllib.request.urlopen("http://127.0.0.1:8765/screens/stage_1_intake.html").status
        stage2 = urllib.request.urlopen(
            "http://127.0.0.1:8765/screens/stage_2_transcripts.html"
        ).status
        stage3 = urllib.request.urlopen(
            "http://127.0.0.1:8765/screens/stage_3_workspace.html"
        ).status
        stage4 = urllib.request.urlopen(
            "http://127.0.0.1:8765/screens/stage_4_insertions.html"
        ).status
        stage6 = urllib.request.urlopen("http://127.0.0.1:8765/screens/stage_6_export.html").status

        parsed = _post_json(
            "http://127.0.0.1:8765/api/intake/parse",
            {
                "pasted_text": (
                    "DELIA GARZA\nv.\nHOME DEPOT U.S.A., INC.\nCAUSE NO. 25-cv-00598-OLG\n"
                    "Date: 04/30/2026\nTime: 1:30 PM\nNotice of deposition of Heath Thomas\n"
                    "Steven A. Nunez\nservice@brainspine-law.com\nATTORNEYS FOR PLAINTIFF"
                ),
                "intake_metadata": {"source_document": "verify-intake.txt"},
            },
        )
        persisted = _get_json(f"http://127.0.0.1:8765/api/intake/{parsed['case_id']}")

        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_audio.close()
        with wave.open(temp_audio.name, "wb") as wave_file:
            wave_file.setnchannels(1)
            wave_file.setsampwidth(2)
            wave_file.setframerate(16000)
            frames = b"".join(
                struct.pack("<h", int(12000 * math.sin(2 * math.pi * 220 * (index / 16000))))
                for index in range(16000 * 4)
            )
            wave_file.writeframes(frames)
        encoded_audio = base64.b64encode(open(temp_audio.name, "rb").read()).decode("utf-8")
        transcription_result = _post_json(
            "http://127.0.0.1:8765/api/transcribe/prerecorded",
            {
                "case_id": parsed["case_id"],
                "file_name": "verify.wav",
                "file_content_base64": encoded_audio,
            },
        )
        session_id = int(transcription_result["session_id"])
        timeline = _get_json(f"http://127.0.0.1:8765/api/transcript/{session_id}/timeline")
        queue = _get_json(f"http://127.0.0.1:8765/api/review/{session_id}/queue")
        low_item = next(
            item for item in queue["items"] if item["issue_category"] == "LOW_CONFIDENCE"
        )
        resolved = _post_json(
            "http://127.0.0.1:8765/api/review/resolve",
            {
                "session_id": session_id,
                "review_flag_id": low_item["id"],
                "action": "resolve",
                "reviewer": "verify-user",
                "note": "apply deterministic cleanup",
                "apply_deterministic_rules": True,
            },
        )
        speaker_item = next(
            item for item in queue["items"] if item.get("speaker_segment_id") is not None
        )
        speaker_resolved = _post_json(
            "http://127.0.0.1:8765/api/review/resolve",
            {
                "session_id": session_id,
                "review_flag_id": speaker_item["id"],
                "action": "resolve",
                "reviewer": "verify-user",
                "note": "correct speaker label",
                "corrected_speaker_label": "MS. FLORA",
                "corrected_role": "attorney",
            },
        )
        audit = _get_json(f"http://127.0.0.1:8765/api/review/{session_id}/audit")
        word_id = timeline["timeline"][0]["words"][0]["id"]
        word = _get_json(f"http://127.0.0.1:8765/api/transcript/{session_id}/word/{word_id}")
        media_status = urllib.request.urlopen(
            f"http://127.0.0.1:8765/api/transcript/{session_id}/media"
        ).status

        annotation_result = _post_json(
            "http://127.0.0.1:8765/api/review/annotation",
            {
                "session_id": session_id,
                "transcript_block_id": timeline["timeline"][0]["id"],
                "annotation_type": "BOOKMARK",
                "annotation_text": "Key admission",
                "bookmark_label": "Admission",
                "issue_category": "UNRESOLVED_ENTITY",
                "author": "verify-user",
            },
        )
        objection_result = _post_json(
            "http://127.0.0.1:8765/api/review/objection",
            {
                "session_id": session_id,
                "transcript_block_id": timeline["timeline"][0]["id"],
                "category": "FORM",
                "objection_text": "Objection, form.",
                "reviewer": "verify-user",
            },
        )
        exhibit_result = _post_json(
            "http://127.0.0.1:8765/api/review/exhibit-link",
            {
                "session_id": session_id,
                "transcript_block_id": timeline["timeline"][0]["id"],
                "exhibit_label": "Exhibit 4",
                "exhibit_description": "Mechanical systems report",
                "created_by": "verify-user",
            },
        )
        review_dashboard = _get_json(f"http://127.0.0.1:8765/api/review/{session_id}/dashboard")
        review_navigation = _get_json(f"http://127.0.0.1:8765/api/review/{session_id}/navigation")

        docx_result = _post_json(
            "http://127.0.0.1:8765/api/export/docx",
            {"session_id": session_id, "include_pdf": False},
        )
        txt_result = _post_json("http://127.0.0.1:8765/api/export/txt", {"session_id": session_id})
        package_result = _post_json(
            "http://127.0.0.1:8765/api/export/package",
            {"session_id": session_id, "include_pdf": True},
        )
        export_history = _get_json(f"http://127.0.0.1:8765/api/export/{session_id}/history")

        realtime_started = _post_json(
            "http://127.0.0.1:8765/api/realtime/start",
            {
                "session_id": session_id,
                "meeting_id": "verify-meeting",
                "passcode": "verify-passcode",
                "mock": True,
            },
        )
        time.sleep(1)
        realtime_status = _get_json(f"http://127.0.0.1:8765/api/realtime/status/{session_id}")
        realtime_stopped = _post_json(
            "http://127.0.0.1:8765/api/realtime/stop",
            {"session_id": session_id, "reason": "verify-stop"},
        )

        assert health["status"] == "ok"
        assert db_status["database"] == "connected"
        assert db_status["tables_initialized"] is True
        assert stage1 == 200 and stage2 == 200 and stage3 == 200 and stage4 == 200 and stage6 == 200
        assert parsed["keyterms"]["term_count"] >= 1
        assert parsed["phonetics"]["generated"] is not None
        assert persisted["case"]["id"] == parsed["case_id"]
        assert timeline["timeline"]
        assert queue["items"]
        assert resolved["review_flag"]["status"] == "reviewed"
        assert speaker_resolved["speaker_correction"]["corrected_speaker_label"] == "MS. FLORA"
        assert audit["items"]
        assert word["seek_time"] == word["start_time"]
        assert media_status == 200
        assert annotation_result["bookmark_label"] == "Admission"
        assert objection_result["objection"]["category"] == "FORM"
        assert exhibit_result["linked_exhibit"]["exhibit_label"] == "Exhibit 4"
        assert review_dashboard["annotations"]
        assert review_dashboard["objections"]
        assert review_dashboard["linked_exhibits"]
        assert "interpreted_segments" in review_dashboard
        assert review_navigation["items"]
        assert any(path.endswith(".docx") for path in docx_result["files"])
        assert any(path.endswith(".txt") for path in txt_result["files"])
        assert any(path.endswith(".zip") for path in package_result["files"])
        assert export_history["items"]
        assert realtime_started["source_label"] == "zoom_rtms"
        assert realtime_status["packet_count"] >= 1
        assert realtime_stopped["stream_status"] in {"completed", "stopped"}
        print(health)
        print(db_status)
        print(session_id)
    finally:
        process.terminate()
        process.wait(timeout=10)


if __name__ == "__main__":
    main()
