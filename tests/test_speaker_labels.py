from __future__ import annotations

import unittest

from backend.entities.speaker_labels import generate_speaker_label


class SpeakerLabelTests(unittest.TestCase):
    def test_speaker_labels_use_last_name(self) -> None:
        self.assertEqual(generate_speaker_label("Elizabeth R. Flora"), "MS. FLORA")
        self.assertEqual(generate_speaker_label("Wayne Krause Yang"), "MR. YANG")
        self.assertEqual(generate_speaker_label("Lori Varnell"), "MS. VARNELL")

    def test_existing_label_is_preserved(self) -> None:
        self.assertEqual(
            generate_speaker_label("Any Name", preserve="MR. COLEMAN"),
            "MR. COLEMAN",
        )
