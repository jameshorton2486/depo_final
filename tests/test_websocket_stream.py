from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient

from backend.database.init_db import initialize_database
from backend.database.models.case_models import CaseCreate
from backend.database.models.session_models import SessionCreate
from backend.database.repositories.cases_repo import create_case
from backend.database.repositories.sessions_repo import create_session
from backend.realtime.realtime_service import RealtimeSessionManager, RealtimeStartRequest


class WebsocketStreamTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.database_path = self.root / "phase8_ws.db"
        self.data_root = self.root / "data"
        initialize_database(self.database_path)
        self.case_record = create_case(CaseCreate(case_name="Phase 8 WS"), self.database_path)
        self.session_record = create_session(
            SessionCreate(case_id=self.case_record.id, session_name="Live Session"),
            self.database_path,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_websocket_receives_snapshot_and_updates(self) -> None:
        manager = RealtimeSessionManager(database_path=self.database_path, data_root=self.data_root)

        app = FastAPI()

        @app.post("/start")
        async def start_route() -> dict[str, object]:
            return await manager.start_session(
                RealtimeStartRequest(session_id=self.session_record.id, mock=True)
            )

        @app.websocket("/ws/transcript/{session_id}")
        async def ws_route(websocket: WebSocket, session_id: int) -> None:
            await manager.websocket_session(websocket, session_id)

        with TestClient(app) as client:
            client.post("/start")
            with client.websocket_connect(f"/ws/transcript/{self.session_record.id}") as websocket:
                snapshot = websocket.receive_json()
                update = websocket.receive_json()
                self.assertEqual(snapshot["type"], "snapshot")
                self.assertEqual(update["type"], "transcript_update")
                self.assertTrue(update["payload"]["raw_text"])
