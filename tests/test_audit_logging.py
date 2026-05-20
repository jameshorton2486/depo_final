from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.database.init_db import initialize_database
from backend.database.models.case_models import CaseCreate
from backend.database.models.session_models import SessionCreate
from backend.database.repositories.cases_repo import create_case
from backend.database.repositories.sessions_repo import create_session
from backend.review.audit_logger import list_audit_events, log_audit_event


class AuditLoggingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "phase6_audit.db"
        initialize_database(self.database_path)
        case_record = create_case(CaseCreate(case_name="Phase 6 Audit"), self.database_path)
        self.session_record = create_session(
            SessionCreate(case_id=case_record.id, session_name="Session 1"),
            self.database_path,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_audit_event_persists_and_reads_back(self) -> None:
        event = log_audit_event(
            session_id=self.session_record.id,
            entity_type="word_object",
            entity_id=10,
            action_type="resolve",
            issue_category="LOW_CONFIDENCE",
            original_value="Heeth",
            modified_value="Heath",
            reviewer="Phase 6 Tester",
            correction_source="deterministic_rule",
            database_path=self.database_path,
        )
        events = list_audit_events(self.session_record.id, self.database_path)

        self.assertEqual(event["action_type"], "resolve")
        self.assertGreaterEqual(len(events), 1)
        self.assertEqual(events[0]["reviewer"], "Phase 6 Tester")
