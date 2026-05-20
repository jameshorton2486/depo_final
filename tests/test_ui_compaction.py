from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INTAKE_HTML = REPO_ROOT / "frontend" / "screens" / "stage_1_intake.html"
WORKSPACE_CSS = REPO_ROOT / "frontend" / "assets" / "css" / "workspace.css"

REQUIRED_CSS_CLASSES = (
    ".collapsible-panel",
    ".panel-toggle",
    ".panel-content",
    ".panel-count",
    ".compact-chip",
    ".empty-state-minimized",
    ".scrollable-panel-body",
)

EXPECTED_PANELS = {
    "parsed-entities": "intakeSummaryGrid",
    "speaker-labels": "speakerLabelPreview",
    "case-state": "intakeCaseStateGrid",
    "keyterm-preview": "keytermPreview",
    "provenance": "provenancePreview",
}


class UiCompactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = INTAKE_HTML.read_text(encoding="utf-8")
        self.css = WORKSPACE_CSS.read_text(encoding="utf-8")

    def test_required_css_classes_exist(self) -> None:
        for klass in REQUIRED_CSS_CLASSES:
            with self.subTest(klass=klass):
                self.assertIn(klass, self.css, f"missing CSS rule for {klass}")

    def test_each_target_panel_is_collapsible(self) -> None:
        for panel_id, mount_id in EXPECTED_PANELS.items():
            with self.subTest(panel=panel_id):
                pattern = rf"data-panel-id=\"{re.escape(panel_id)}\""
                self.assertRegex(self.html, pattern, f"panel {panel_id} not declared")
                self.assertIn(
                    f'id="{mount_id}"',
                    self.html,
                    f"mount point {mount_id} for {panel_id} missing",
                )

    def test_no_oversized_placeholder_cards_for_target_panels(self) -> None:
        # The five target panels must no longer render inside placeholder-card containers.
        for mount_id in EXPECTED_PANELS.values():
            with self.subTest(mount=mount_id):
                section = self._enclosing_section(mount_id)
                self.assertIn("collapsible-panel", section)
                self.assertNotIn("placeholder-card", section)

    def test_panels_provide_toggle_and_count_badge(self) -> None:
        for panel_id in EXPECTED_PANELS:
            with self.subTest(panel=panel_id):
                section = self._panel_section(panel_id)
                self.assertIn("panel-toggle", section)
                self.assertIn("aria-expanded", section)
                self.assertIn("data-panel-count", section)

    def test_panel_bodies_scroll_when_overflowing(self) -> None:
        # At least the entity/speaker/keyterm/provenance/phonetic bodies use scrollable-panel-body.
        scrollable_targets = {
            "intakeSummaryGrid",
            "speakerLabelPreview",
            "keytermPreview",
            "phoneticPreview",
            "provenancePreview",
        }
        for mount_id in scrollable_targets:
            with self.subTest(mount=mount_id):
                section = self._enclosing_section(mount_id)
                self.assertIn("scrollable-panel-body", section)

    def test_max_height_and_overflow_defined_on_scrollable_body(self) -> None:
        match = re.search(r"\.scrollable-panel-body\s*\{([^}]+)\}", self.css, re.DOTALL)
        self.assertIsNotNone(match, "scrollable-panel-body rule missing")
        block = match.group(1)
        self.assertRegex(block, r"max-height\s*:")
        self.assertRegex(block, r"overflow-y\s*:\s*auto")

    def test_collapse_transition_defined(self) -> None:
        match = re.search(r"\.panel-chevron\s*\{([^}]+)\}", self.css, re.DOTALL)
        self.assertIsNotNone(match)
        self.assertRegex(match.group(1), r"transition\s*:")

    def _panel_section(self, panel_id: str) -> str:
        marker = f'data-panel-id="{panel_id}"'
        start = self.html.find(marker)
        self.assertNotEqual(start, -1)
        section_start = self.html.rfind("<section", 0, start)
        section_end = self.html.find("</section>", start) + len("</section>")
        return self.html[section_start:section_end]

    def _enclosing_section(self, mount_id: str) -> str:
        marker = f'id="{mount_id}"'
        start = self.html.find(marker)
        self.assertNotEqual(start, -1)
        section_start = self.html.rfind("<section", 0, start)
        section_end = self.html.find("</section>", start) + len("</section>")
        return self.html[section_start:section_end]


if __name__ == "__main__":
    unittest.main()
