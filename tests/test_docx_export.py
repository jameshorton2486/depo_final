from __future__ import annotations

import base64
import math
import tempfile
import unittest
import zipfile
from pathlib import Path

import numpy as np
import soundfile as sf

from backend.database.init_db import initialize_database
from backend.database.models.case_models import CaseCreate
from backend.database.models.session_models import SessionCreate
from backend.database.repositories.cases_repo import create_case
from backend.database.repositories.sessions_repo import create_session
from backend.export.export_service import ExportRequest, export_docx_bundle, export_package_bundle
from backend.transcript.transcript_service import TranscriptionRequest, transcribe_and_persist


def _make_audio(path: Path) -> Path:
    sample_rate = 16000
    timeline = np.arange(sample_rate * 6) / sample_rate
    samples = (0.18 * np.sin(2 * math.pi * 205 * timeline)).astype(np.float32)
    samples[:sample_rate] = 0.0
    sf.write(str(path), samples, sample_rate)
    return path


class DocxExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.database_path = self.root / "phase7.db"
        self.data_root = self.root / "data"
        initialize_database(self.database_path)
        self.case_record = create_case(CaseCreate(case_name="Phase 7 Matter"), self.database_path)
        self.session_record = create_session(
            SessionCreate(case_id=self.case_record.id, session_name="Session 1"),
            self.database_path,
        )
        self.audio_path = _make_audio(self.root / "phase7.wav")
        transcribe_and_persist(
            TranscriptionRequest(
                case_id=self.case_record.id,
                session_id=self.session_record.id,
                file_name=self.audio_path.name,
                file_content_base64=base64.b64encode(self.audio_path.read_bytes()).decode("utf-8"),
            ),
            database_path=self.database_path,
            data_root=self.data_root,
            mock=True,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_docx_export_writes_document_xml(self) -> None:
        result = export_docx_bundle(
            ExportRequest(session_id=self.session_record.id),
            database_path=self.database_path,
            data_root=self.data_root,
        )

        docx_path = next(Path(path) for path in result["files"] if path.endswith(".docx"))
        self.assertTrue(docx_path.exists())
        with zipfile.ZipFile(docx_path) as archive:
            document_xml = archive.read("word/document.xml").decode("utf-8")
        self.assertIn("COURT REPORTER CERTIFICATE", document_xml)
        self.assertIn("Q.", document_xml)

    def test_package_export_writes_manifest_and_zip(self) -> None:
        result = export_package_bundle(
            ExportRequest(session_id=self.session_record.id, include_pdf=True),
            database_path=self.database_path,
            data_root=self.data_root,
        )

        self.assertTrue(any(path.endswith(".zip") for path in result["files"]))
        self.assertEqual(result["manifest"]["export_type"], "package")
