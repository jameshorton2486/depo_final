from __future__ import annotations

import unittest

from backend.parsers.nod_parser import parse_nod_text

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


class NodParserTests(unittest.TestCase):
    def test_nod_parser_extracts_session_fields(self) -> None:
        parsed = parse_nod_text(SAMPLE_TEXT)
        self.assertEqual(parsed["deponent_name"], "Heath Thomas")
        self.assertEqual(parsed["session_date"], "2026-04-30")
        self.assertEqual(parsed["location_type"], "zoom")
        self.assertEqual(parsed["ordered_by"], "Tiffany Netcher")

    def test_nod_parser_extracts_attorneys(self) -> None:
        parsed = parse_nod_text(SAMPLE_TEXT)
        self.assertEqual(len(parsed["attorneys"]), 1)
        attorney = parsed["attorneys"][0]
        self.assertEqual(attorney["full_name"], "Steven A. Nunez")
        self.assertEqual(attorney["email"], "service@brainspine-law.com")
        self.assertEqual(attorney["represented_party"], "Plaintiff")
