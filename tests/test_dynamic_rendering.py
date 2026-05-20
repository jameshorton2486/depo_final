# ruff: noqa: E501 - tests embed JS source as multi-line string literals.
from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PANELS_MODULE = (REPO_ROOT / "frontend" / "assets" / "js" / "ui_panels.js").as_posix()
STAGE1_MODULE = (REPO_ROOT / "frontend" / "assets" / "js" / "screens" / "stage_1.js").as_posix()
FAKE_DOM = (REPO_ROOT / "tests" / "_fake_dom.js").as_posix()


def _run_node(script: str) -> dict[str, object]:
    process = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
    )
    if process.returncode != 0:
        raise AssertionError(
            f"node failed (exit {process.returncode}):\nSTDERR:\n{process.stderr}\nSTDOUT:\n{process.stdout}"
        )
    return json.loads(process.stdout)


HARNESS = textwrap.dedent(f"""
    const fs = require('fs');
    const {{ createCollapsiblePanels }} = require('{PANELS_MODULE}');
    const {{ makeFakeDom }} = require('{FAKE_DOM}');

    const dom = makeFakeDom();
    function mkPanel(id, mountId, extra) {{
        const section = dom.create('section', {{
            class: 'collapsible-panel empty',
            'data-panel-id': id,
            'data-collapsed': 'false',
        }});
        section.appendChild(dom.create('button', {{ class: 'panel-toggle' }}));
        section.appendChild(dom.create('span', {{ 'data-panel-count': '', 'data-state': 'zero' }}));
        const mount = dom.create('div', {{ id: mountId, class: 'panel-content scrollable-panel-body' }});
        section.appendChild(mount);
        if (extra) extra(section, mount);
        dom.document.body.appendChild(section);
        return mount;
    }}

    mkPanel('parsed-entities', 'intakeSummaryGrid');
    mkPanel('speaker-labels', 'speakerLabelPreview');
    mkPanel('case-state', 'intakeCaseStateGrid');
    mkPanel('keyterm-preview', 'keytermPreview', (section, mount) => {{
        const select = dom.create('select', {{ id: 'keytermSort' }});
        select.value = 'weight';
        section.appendChild(select);
    }});
    mkPanel('provenance', 'provenancePreview');
    mkPanel('phonetic-seeds', 'phoneticPreview');
    // Stub editable fields target so renderIntakeEditableFields() doesn't crash if called.
    dom.document.body.appendChild(dom.create('div', {{ id: 'intakeEditableFields' }}));

    global.appState = {{ panelCollapse: {{}}, currentCaseId: 0 }};
    global.persistState = () => {{}};
    global.document = dom.document;
    global.CollapsiblePanels = createCollapsiblePanels({{ document: dom.document, state: global.appState }});
    global.window = {{ stage1Module: null }};

    const stage1Source = fs.readFileSync('{STAGE1_MODULE}', 'utf8');
    const exposed = stage1Source + '\\n;Object.assign(globalThis, {{ renderSpeakerLabels, renderSummaryGrid, renderKeyterms, renderProvenance, renderPhonetics, renderCaseState }});';
    new Function('window', 'document', 'appState', 'persistState', 'CollapsiblePanels', exposed)(
        global.window, global.document, global.appState, global.persistState, global.CollapsiblePanels
    );
    """)


def _wrap(body: str) -> str:
    return HARNESS + "\n" + textwrap.dedent(body)


class DynamicRenderingTests(unittest.TestCase):
    def test_speaker_labels_render_as_compact_chips_with_count(self) -> None:
        script = _wrap("""
            renderSpeakerLabels([
                { speaker_label: 'MS. FLORA', full_name: 'Elizabeth Flora', role: 'attorney' },
                { speaker_label: 'MR. YANG', full_name: 'David Yang', role: 'attorney' },
                { speaker_label: 'THE WITNESS', full_name: 'Heath Thomas', role: 'witness' },
                { speaker_label: '', full_name: '', role: 'noise' },
            ]);
            const mount = dom.document.querySelector('[id="speakerLabelPreview"]');
            const panel = dom.document.querySelector('[data-panel-id="speaker-labels"]');
            const badge = panel.querySelector('[data-panel-count]');
            console.log(JSON.stringify({
                html: mount.innerHTML,
                count: badge.textContent,
                empty: panel.classList.contains('empty'),
                collapsed: panel.dataset.collapsed,
            }));
            """)
        payload = _run_node(script)
        self.assertEqual(payload["count"], "3")
        self.assertFalse(payload["empty"])
        self.assertIn("compact-chip", payload["html"])
        self.assertIn("MS. FLORA", payload["html"])
        self.assertIn('data-role="attorney"', payload["html"])
        self.assertEqual(payload["collapsed"], "false")

    def test_empty_provenance_minimizes_panel(self) -> None:
        script = _wrap("""
            renderProvenance([]);
            const mount = dom.document.querySelector('[id="provenancePreview"]');
            const panel = dom.document.querySelector('[data-panel-id="provenance"]');
            console.log(JSON.stringify({
                html: mount.innerHTML,
                empty: panel.classList.contains('empty'),
                collapsed: panel.dataset.collapsed,
            }));
            """)
        payload = _run_node(script)
        self.assertIn("empty-state-minimized", payload["html"])
        self.assertTrue(payload["empty"])
        # Empty panels stay visible but visually minimized; user controls collapse.
        self.assertEqual(payload["collapsed"], "false")

    def test_parsed_entities_render_compact_rows(self) -> None:
        script = _wrap("""
            renderSummaryGrid(
                { case_style: 'Garza v. GuideOne', cause_number: '25-cv-00598', parser_confidence: 0.94 },
                [{ party_type: 'Plaintiff', party_name: 'Maria Garza', parser_confidence: 0.91 }],
                [{ attorney: { full_name: 'Elizabeth Flora', firm_name: 'Flora & Co.', email: 'ef@example.com' }, case_attorney: { represented_party_name: 'GuideOne' } }],
                { deponent_name: 'Heath Thomas', session_date: '2026-02-10', location_address: '123 Main' }
            );
            const mount = dom.document.querySelector('[id="intakeSummaryGrid"]');
            const panel = dom.document.querySelector('[data-panel-id="parsed-entities"]');
            const badge = panel.querySelector('[data-panel-count]');
            const rows = mount.innerHTML.split('class="compact-row"').length - 1;
            console.log(JSON.stringify({
                rows,
                count: badge.textContent,
                html_excerpt: mount.innerHTML.slice(0, 80),
                empty: panel.classList.contains('empty'),
            }));
            """)
        payload = _run_node(script)
        self.assertGreaterEqual(payload["rows"], 6)
        self.assertEqual(payload["count"], str(payload["rows"]))
        self.assertFalse(payload["empty"])

    def test_keyterms_render_chip_pills_and_count(self) -> None:
        script = _wrap("""
            renderKeyterms({
                keyterms: [
                    { term: 'Discovery', category: 'legal', source: 'rule', weight: 2.0 },
                    { term: 'Witness', category: 'role', source: 'manual', weight: 1.0 },
                ],
            });
            const mount = dom.document.querySelector('[id="keytermPreview"]');
            const panel = dom.document.querySelector('[data-panel-id="keyterm-preview"]');
            const badge = panel.querySelector('[data-panel-count]');
            console.log(JSON.stringify({
                html: mount.innerHTML,
                count: badge.textContent,
                empty: panel.classList.contains('empty'),
            }));
            """)
        payload = _run_node(script)
        self.assertEqual(payload["count"], "2")
        self.assertFalse(payload["empty"])
        self.assertIn("keyterm-pill", payload["html"])

    def test_case_state_renders_compact_rows_when_populated(self) -> None:
        script = _wrap("""
            renderCaseState({
                stage_label: 'Transcripts',
                stage_key: 'transcripts',
                session_count: 2,
                review_state: 'pending',
                is_export_ready: false,
                latest_session_id: 17,
            });
            const mount = dom.document.querySelector('[id="intakeCaseStateGrid"]');
            const panel = dom.document.querySelector('[data-panel-id="case-state"]');
            const badge = panel.querySelector('[data-panel-count]');
            console.log(JSON.stringify({
                html: mount.innerHTML,
                count: badge.textContent,
                empty: panel.classList.contains('empty'),
            }));
            """)
        payload = _run_node(script)
        self.assertGreaterEqual(int(payload["count"]), 4)
        self.assertIn("compact-row", payload["html"])
        self.assertIn("Transcripts", payload["html"])
        self.assertFalse(payload["empty"])


if __name__ == "__main__":
    unittest.main()
