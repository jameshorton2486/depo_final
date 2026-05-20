(function (globalScope) {
    function createCollapsiblePanels(options = {}) {
        const documentRef = options.document || null;
        const stateRef = options.state || null;
        const persistRef = options.persist || null;

        function getDoc() {
            return documentRef || globalScope.document;
        }
        function getState() {
            return stateRef || globalScope.appState || { panelCollapse: {} };
        }
        function persist() {
            const fn = persistRef || globalScope.persistState;
            if (typeof fn === 'function') fn();
        }

        function findPanel(id) {
            const doc = getDoc();
            if (!doc) return null;
            return doc.querySelector(`.collapsible-panel[data-panel-id="${id}"]`);
        }

        function setCollapsed(panel, collapsed, { persist: shouldPersist = true } = {}) {
            if (!panel) return;
            panel.dataset.collapsed = collapsed ? 'true' : 'false';
            const toggle = panel.querySelector('.panel-toggle');
            if (toggle && typeof toggle.setAttribute === 'function') {
                toggle.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
            }
            if (!shouldPersist) return;
            const state = getState();
            state.panelCollapse = state.panelCollapse || {};
            state.panelCollapse[panel.dataset.panelId] = collapsed;
            persist();
        }

        function toggle(id) {
            const panel = findPanel(id);
            if (!panel) return;
            setCollapsed(panel, panel.dataset.collapsed !== 'true');
        }

        function setCount(id, count) {
            const panel = findPanel(id);
            if (!panel) return;
            const badge = panel.querySelector('[data-panel-count]');
            if (!badge) return;
            const value = Number(count) || 0;
            badge.textContent = String(value);
            badge.dataset.state = value === 0 ? 'zero' : 'has';
        }

        function setEmpty(id, isEmpty) {
            const panel = findPanel(id);
            if (!panel) return;
            if (panel.classList.toggle) {
                panel.classList.toggle('empty', Boolean(isEmpty));
            } else if (isEmpty) {
                panel.classList.add('empty');
            } else {
                panel.classList.remove('empty');
            }
        }

        function update(id, payload = {}) {
            if (payload.count !== undefined) setCount(id, payload.count);
            if (payload.isEmpty !== undefined) setEmpty(id, payload.isEmpty);
        }

        function init(root) {
            const doc = getDoc();
            const scope = root || doc;
            if (!scope || typeof scope.querySelectorAll !== 'function') return;
            const panels = scope.querySelectorAll('.collapsible-panel[data-panel-id]');
            panels.forEach((panel) => {
                const id = panel.dataset.panelId;
                if (!id) return;
                const state = getState();
                const stored = state.panelCollapse ? state.panelCollapse[id] : undefined;
                if (typeof stored === 'boolean') {
                    setCollapsed(panel, stored, { persist: false });
                }
                const toggleBtn = panel.querySelector('.panel-toggle');
                if (!toggleBtn || toggleBtn.dataset.bound === '1') return;
                toggleBtn.dataset.bound = '1';
                toggleBtn.addEventListener('click', () => toggle(id));
            });
        }

        return { init, toggle, setCount, setEmpty, update, findPanel, setCollapsed };
    }

    const defaultInstance = createCollapsiblePanels();
    globalScope.CollapsiblePanels = defaultInstance;
    globalScope.createCollapsiblePanels = createCollapsiblePanels;

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { createCollapsiblePanels, CollapsiblePanels: defaultInstance };
    }
})(typeof window !== 'undefined' ? window : globalThis);
