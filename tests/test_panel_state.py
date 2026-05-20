# ruff: noqa: E501 - tests embed JS source as multi-line string literals.
from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PANELS_MODULE = (REPO_ROOT / "frontend" / "assets" / "js" / "ui_panels.js").as_posix()
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


def _wrap(body: str) -> str:
    return textwrap.dedent(f"""
        const {{ createCollapsiblePanels }} = require('{PANELS_MODULE}');
        const {{ makeFakeDom }} = require('{FAKE_DOM}');
        {body}
        """)


class CollapsiblePanelStateTests(unittest.TestCase):
    def test_toggle_flips_collapsed_state_and_persists(self) -> None:
        script = _wrap("""
            const dom = makeFakeDom();
            const persisted = {};
            const state = { panelCollapse: {} };
            const panels = createCollapsiblePanels({
                document: dom.document,
                state,
                persist: () => { persisted.panelCollapse = JSON.parse(JSON.stringify(state.panelCollapse)); },
            });
            const panel = dom.create('section', { class: 'collapsible-panel', 'data-panel-id': 'parsed-entities', 'data-collapsed': 'false' });
            const toggle = dom.create('button', { class: 'panel-toggle' });
            const badge = dom.create('span', { 'data-panel-count': '', 'data-state': 'zero' });
            panel.appendChild(toggle);
            panel.appendChild(badge);
            dom.document.body.appendChild(panel);

            panels.init();
            const before = panel.dataset.collapsed;
            toggle.click();
            const afterClick = panel.dataset.collapsed;
            panels.toggle('parsed-entities');
            const afterApi = panel.dataset.collapsed;

            console.log(JSON.stringify({
                before,
                afterClick,
                afterApi,
                aria: toggle.getAttribute('aria-expanded'),
                persisted: persisted.panelCollapse,
            }));
            """)
        payload = _run_node(script)
        self.assertEqual(payload["before"], "false")
        self.assertEqual(payload["afterClick"], "true")
        self.assertEqual(payload["afterApi"], "false")
        self.assertEqual(payload["aria"], "true")
        self.assertEqual(payload["persisted"], {"parsed-entities": False})

    def test_set_count_updates_badge_and_zero_state(self) -> None:
        script = _wrap("""
            const dom = makeFakeDom();
            const state = { panelCollapse: {} };
            const panels = createCollapsiblePanels({ document: dom.document, state, persist: () => {} });
            const panel = dom.create('section', { class: 'collapsible-panel', 'data-panel-id': 'speaker-labels', 'data-collapsed': 'false' });
            const badge = dom.create('span', { 'data-panel-count': '', 'data-state': 'zero' });
            panel.appendChild(badge);
            dom.document.body.appendChild(panel);

            panels.setCount('speaker-labels', 7);
            const withCount = { text: badge.textContent, state: badge.dataset.state };
            panels.setCount('speaker-labels', 0);
            const zeroed = { text: badge.textContent, state: badge.dataset.state };

            console.log(JSON.stringify({ withCount, zeroed }));
            """)
        payload = _run_node(script)
        self.assertEqual(payload["withCount"], {"text": "7", "state": "has"})
        self.assertEqual(payload["zeroed"], {"text": "0", "state": "zero"})

    def test_restored_state_applies_before_user_interaction(self) -> None:
        script = _wrap("""
            const dom = makeFakeDom();
            const state = { panelCollapse: { 'case-state': true } };
            const panels = createCollapsiblePanels({ document: dom.document, state, persist: () => {} });
            const panel = dom.create('section', { class: 'collapsible-panel', 'data-panel-id': 'case-state', 'data-collapsed': 'false' });
            panel.appendChild(dom.create('button', { class: 'panel-toggle' }));
            dom.document.body.appendChild(panel);

            panels.init();
            console.log(JSON.stringify({ collapsed: panel.dataset.collapsed }));
            """)
        payload = _run_node(script)
        self.assertEqual(payload["collapsed"], "true")


if __name__ == "__main__":
    unittest.main()
