from __future__ import annotations

import unittest

from backend.entities.keyterms import build_keyterms


class KeytermGenerationTests(unittest.TestCase):
    def test_keyterm_generation_includes_attorneys_and_firms(self) -> None:
        payload = {
            "case": {
                "case_style": "Delia Garza v. Home Depot U.S.A., Inc.",
                "cause_number": "25-cv-00598-OLG",
            },
            "parties": [{"party_name": "Delia Garza", "entity_type": "individual"}],
            "attorneys": [
                {
                    "full_name": "Steven A. Nunez",
                    "law_firm": "Brain and Spine Personal Injury Lawyers of San Antonio, PLLC",
                    "email": "service@brainspine-law.com",
                    "address_line_1": "8620 N New Braunfels Ave, Ste. N 604",
                }
            ],
            "session": {"deponent_name": "Heath Thomas"},
        }
        result = build_keyterms(payload)
        terms = {item["term"] for item in result["keyterms"]}
        self.assertIn("Steven A. Nunez", terms)
        self.assertIn("Brain and Spine Personal Injury Lawyers of San Antonio, PLLC", terms)
        self.assertIn("Heath Thomas", terms)
