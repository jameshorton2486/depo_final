from __future__ import annotations

import unittest

from backend.database.models.transcript_models import ReviewIssueCategory
from backend.review.deterministic_rules import apply_deterministic_rules, normalize_speaker_label


class DeterministicRulesTests(unittest.TestCase):
    def test_deterministic_rules_are_repeatable(self) -> None:
        source = "Q.   Please  state  your name ."
        first = apply_deterministic_rules(source, ReviewIssueCategory.COLLOQUY_FORMAT)
        second = apply_deterministic_rules(
            first["updated_value"], ReviewIssueCategory.COLLOQUY_FORMAT
        )

        self.assertTrue(first["changed"])
        self.assertEqual(first["updated_value"], second["updated_value"])

    def test_speaker_label_normalization_is_uppercase_and_legal_style(self) -> None:
        self.assertEqual(normalize_speaker_label("mr yang"), "MR. YANG")
