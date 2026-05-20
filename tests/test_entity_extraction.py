from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from backend.services.intake_service import IntakeParseRequest, get_intake, parse_and_persist

SAMPLE_TEXT = """
IN THE UNITED STATES DISTRICT COURT
WESTERN DISTRICT OF TEXAS
SAN ANTONIO DIVISION
DELIA GARZA
v.
HOME DEPOT U.S.A., INC.
CIVIL ACTION NO. 25-cv-00598-OLG

Notice is hereby given that the deposition of Heath Thomas will be taken.
Date: 04/30/2026
Time: 1:30 PM
Location: Via Zoom
Ordered by: Tiffany Netcher

Steven A. Nunez
Brain and Spine Personal Injury Lawyers of San Antonio, PLLC
8620 N New Braunfels Ave, Ste. N 604
San Antonio, TX 78217-4000
Tel: (210) 999-5033
service@brainspine-law.com
ATTORNEYS FOR PLAINTIFF
"""


class EntityExtractionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "phase3.db"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_intake_parse_persists_entities_and_metadata(self) -> None:
        result = parse_and_persist(
            IntakeParseRequest(
                pasted_text=SAMPLE_TEXT,
                intake_metadata={"source_document": "sample_nod.txt"},
            ),
            self.database_path,
        )
        persisted = get_intake(result["case_id"], self.database_path)
        self.assertEqual(persisted["case"]["cause_number"], "25-cv-00598-OLG")
        self.assertEqual(persisted["sessions"][0]["deponent_name"], "Heath Thomas")
        self.assertEqual(persisted["parties"][0]["extracted_from"], "Manual")
        self.assertEqual(persisted["attorneys"][0]["case_attorney"]["speaker_label"], "MR. NUNEZ")
        self.assertTrue(
            (Path("data") / "cases" / str(result["case_id"]) / "keyterms.json").exists()
        )
        self.assertTrue(
            (Path("data") / "cases" / str(result["case_id"]) / "phonetics.json").exists()
        )
