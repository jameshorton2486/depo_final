from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.config import settings
from backend.database.repositories.cases_repo import get_case
from backend.database.repositories.sessions_repo import get_session
from backend.realtime.deepgram_live import (
    build_live_request_config,
    build_live_request_url,
    generate_mock_live_events,
)
from backend.realtime.live_speaker_tracker import resolve_live_speaker_label
from backend.realtime.live_transcript_buffer import LiveTranscriptBuffer
from backend.realtime.stream_persistence import (
    append_raw_event,
    create_live_stream_asset,
    log_session_event,
    persist_live_utterance,
)
from backend.realtime.websocket_router import WebSocketHub
from backend.realtime.zoom_rtms import build_zoom_rtms_metadata


class RealtimeStartRequest(BaseModel):
    session_id: int
    meeting_id: str | None = None
    passcode: str | None = None
    source_label: str = "zoom_rtms"
    mock: bool = True


class RealtimeStopRequest(BaseModel):
    session_id: int
    reason: str | None = None


@dataclass
class RealtimeSessionState:
    session_id: int
    case_id: int
    source_label: str
    mock: bool
    stream_asset_id: int
    raw_json_path: Path
    metadata: dict[str, object]
    buffer: LiveTranscriptBuffer
    task: asyncio.Task | None = None
    stop_requested: bool = False
    error: str | None = None
    request_url: str | None = None
    started: bool = False
    completed: bool = False
    diagnostics: dict[str, object] = field(default_factory=dict)


class RealtimeSessionManager:
    def __init__(self, *, database_path: Path | None = None, data_root: Path | None = None) -> None:
        self.database_path = database_path
        self.data_root = data_root if data_root is not None else settings.data_root
        self._hub = WebSocketHub()
        self._sessions: dict[int, RealtimeSessionState] = {}

    async def start_session(self, request: RealtimeStartRequest) -> dict[str, object]:
        session_record = get_session(request.session_id, self.database_path)
        case_record = get_case(session_record.case_id, self.database_path)
        existing = self._sessions.get(request.session_id)
        if existing and not existing.completed and not existing.stop_requested:
            raise ValueError(f"Realtime session {request.session_id} is already active.")

        dg_config = build_live_request_config(case_record.id, self.data_root)
        asset_bundle = create_live_stream_asset(
            session_id=request.session_id,
            case_id=case_record.id,
            source_label=request.source_label,
            data_root=self.data_root,
            keyterms_path=dg_config["keyterms_path"],
            phonetics_path=dg_config["phonetics_path"],
            database_path=self.database_path,
        )
        metadata = build_zoom_rtms_metadata(
            meeting_id=request.meeting_id,
            passcode=request.passcode,
            source_label=request.source_label,
        )
        request_url = build_live_request_url(list(dg_config["prompted_terms"]))
        state = RealtimeSessionState(
            session_id=request.session_id,
            case_id=case_record.id,
            source_label=request.source_label,
            mock=request.mock,
            stream_asset_id=asset_bundle["asset"].id,
            raw_json_path=asset_bundle["raw_json_path"],
            metadata=metadata,
            buffer=LiveTranscriptBuffer(request.session_id),
            request_url=request_url,
            diagnostics={"deepgram_config": dg_config},
        )
        self._sessions[request.session_id] = state
        log_session_event(
            request.session_id,
            "realtime_started",
            event_time=0.0,
            details=metadata,
            database_path=self.database_path,
        )
        state.task = asyncio.create_task(self._run_stream(state))
        return self.get_status(request.session_id)

    async def stop_session(self, request: RealtimeStopRequest) -> dict[str, object]:
        state = self._require_session(request.session_id)
        state.stop_requested = True
        if state.task and not state.task.done():
            await state.task
        state.buffer.mark_stopped()
        log_session_event(
            request.session_id,
            "realtime_stopped",
            event_time=None,
            details={"reason": request.reason or "manual_stop"},
            database_path=self.database_path,
        )
        return self.get_status(request.session_id)

    def get_status(self, session_id: int) -> dict[str, object]:
        state = self._require_session(session_id)
        snapshot = state.buffer.snapshot()
        return {
            "session_id": session_id,
            "source_label": state.source_label,
            "stream_status": snapshot["stream_status"],
            "packet_count": snapshot["packet_count"],
            "last_latency_ms": snapshot["last_latency_ms"],
            "reconnect_count": snapshot["reconnect_count"],
            "connected_clients": self._hub.connection_count(session_id),
            "block_count": len(snapshot["timeline"]),
            "word_count": len(snapshot["word_timeline"]),
            "speaker_labels": snapshot["speaker_labels"],
            "completed": state.completed,
            "mock": state.mock,
            "request_url": state.request_url,
            "metadata": state.metadata,
            "error": state.error,
        }

    async def websocket_session(self, websocket: WebSocket, session_id: int) -> None:
        state = self._require_session(session_id)
        await self._hub.connect(session_id, websocket)
        try:
            await websocket.send_json(
                {
                    "type": "snapshot",
                    "payload": state.buffer.snapshot(),
                    "status": self.get_status(session_id),
                }
            )
            while True:
                message = await websocket.receive_json()
                if message.get("action") == "readback":
                    await websocket.send_json(
                        {
                            "type": "readback",
                            "payload": state.buffer.search(str(message.get("query", ""))),
                        }
                    )
                elif message.get("action") == "ping":
                    await websocket.send_json(
                        {"type": "pong", "status": self.get_status(session_id)}
                    )
        except WebSocketDisconnect:
            self._hub.disconnect(session_id, websocket)

    async def _run_stream(self, state: RealtimeSessionState) -> None:
        state.started = True
        try:
            if not state.mock:
                raise RuntimeError(
                    "Realtime Deepgram streaming requires a dedicated websocket client integration."
                )
            for index, event in enumerate(generate_mock_live_events()):
                if state.stop_requested:
                    break
                await asyncio.sleep(0.05)
                speaker_label = resolve_live_speaker_label(
                    state.case_id,
                    speaker_index=int(event["speaker"]),
                    explicit_label=str(event.get("speaker_label") or ""),
                    database_path=self.database_path,
                )
                append_raw_event(state.raw_json_path, event)
                block = persist_live_utterance(
                    session_id=state.session_id,
                    transcript_asset_id=state.stream_asset_id,
                    speaker_label=speaker_label,
                    utterance=event,
                    database_path=self.database_path,
                )
                enriched = state.buffer.add_block(block, latency_ms=120 + (index * 10))
                await self._hub.broadcast(
                    state.session_id,
                    {
                        "type": "transcript_update",
                        "payload": enriched,
                        "status": self.get_status(state.session_id),
                    },
                )
            state.completed = True
            state.buffer.mark_completed()
            await self._hub.broadcast(
                state.session_id,
                {"type": "stream_complete", "status": self.get_status(state.session_id)},
            )
        except Exception as exc:
            state.error = str(exc)
            state.buffer.mark_stopped()
            await self._hub.broadcast(
                state.session_id,
                {
                    "type": "stream_error",
                    "error": state.error,
                    "status": self.get_status(state.session_id),
                },
            )

    def _require_session(self, session_id: int) -> RealtimeSessionState:
        state = self._sessions.get(session_id)
        if state is None:
            raise LookupError(f"Realtime session {session_id} was not found.")
        return state


realtime_manager = RealtimeSessionManager()


async def start_realtime_session(request: RealtimeStartRequest) -> dict[str, object]:
    return await realtime_manager.start_session(request)


async def stop_realtime_session(request: RealtimeStopRequest) -> dict[str, object]:
    return await realtime_manager.stop_session(request)


def get_realtime_status(session_id: int) -> dict[str, object]:
    return realtime_manager.get_status(session_id)
