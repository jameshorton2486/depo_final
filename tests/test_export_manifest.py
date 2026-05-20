from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.export.export_manifest import build_export_manifest


class ExportManifestTests(unittest.TestCase):
    def test_manifest_contains_export_settings_and_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            exported_files = [Path(temp_dir) / "sample.docx", Path(temp_dir) / "sample.txt"]
            manifest = build_export_manifest(
                session_id=3,
                case_id=2,
                export_type="package",
                exported_files=exported_files,
                transcript_metadata={"block_count": 4, "page_count": 1},
                export_settings={"include_pdf": True},
                review_status={"audit_event_count": 1},
                preprocessing_metadata={"estimated_snr_db": 22.4},
            )

        self.assertEqual(manifest["session_id"], 3)
        self.assertEqual(manifest["case_id"], 2)
        self.assertTrue(manifest["exported_files"][0].endswith("sample.docx"))
        self.assertTrue(manifest["export_settings"]["include_pdf"])
