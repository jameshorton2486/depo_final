function makeFakeDom() {
    class ClassList {
        constructor() {
            this._set = new Set();
        }
        add(...items) {
            items.forEach((item) => this._set.add(item));
        }
        remove(...items) {
            items.forEach((item) => this._set.delete(item));
        }
        contains(item) {
            return this._set.has(item);
        }
        toggle(item, force) {
            const want = force === undefined ? !this._set.has(item) : Boolean(force);
            if (want) this._set.add(item);
            else this._set.delete(item);
            return want;
        }
    }

    class Element {
        constructor(tag) {
            this.tagName = (tag || 'DIV').toUpperCase();
            this.dataset = {};
            this.attributes = {};
            this.classList = new ClassList();
            this.children = [];
            this.parent = null;
            this._text = '';
            this._html = '';
            this._listeners = {};
        }
        appendChild(child) {
            child.parent = this;
            this.children.push(child);
            return child;
        }
        setAttribute(name, value) {
            this.attributes[name] = String(value);
            if (name.startsWith('data-')) {
                const key = name.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase());
                this.dataset[key] = String(value);
            }
            if (name === 'class') {
                String(value)
                    .split(/\s+/)
                    .filter(Boolean)
                    .forEach((cls) => this.classList.add(cls));
            }
        }
        getAttribute(name) {
            return this.attributes[name];
        }
        addEventListener(event, handler) {
            this._listeners[event] = this._listeners[event] || [];
            this._listeners[event].push(handler);
        }
        dispatchEvent(event) {
            (this._listeners[event] || []).forEach((handler) => handler());
        }
        click() {
            this.dispatchEvent('click');
        }
        set textContent(value) {
            this._text = String(value);
        }
        get textContent() {
            return this._text;
        }
        set innerHTML(value) {
            this._html = String(value);
        }
        get innerHTML() {
            return this._html;
        }
        querySelector(selector) {
            return this._queryAll(selector)[0] || null;
        }
        querySelectorAll(selector) {
            return this._queryAll(selector);
        }
        _queryAll(selector) {
            const results = [];
            const walk = (node) => {
                if (matches(node, selector)) results.push(node);
                node.children.forEach(walk);
            };
            this.children.forEach(walk);
            return results;
        }
    }

    function matches(node, selector) {
        // Supports composite selectors: .class[attr], [attr], [attr="value"], .class
        const remaining = selector.trim();
        const tokens = remaining.match(/(\.[\w-]+|\[[^\]]+\])/g) || [];
        if (!tokens.length) return false;
        for (const token of tokens) {
            if (token.startsWith('.')) {
                if (!node.classList.contains(token.slice(1))) return false;
            } else if (token.startsWith('[')) {
                const inner = token.slice(1, -1);
                const eq = inner.indexOf('=');
                let key;
                let want;
                if (eq === -1) {
                    key = inner;
                } else {
                    key = inner.slice(0, eq);
                    want = inner.slice(eq + 1).replace(/^"|"$/g, '');
                }
                const datasetKey = key.startsWith('data-')
                    ? key.slice(5).replace(/-([a-z])/g, (_, c) => c.toUpperCase())
                    : null;
                if (datasetKey !== null) {
                    if (node.dataset[datasetKey] === undefined) return false;
                    if (want !== undefined && node.dataset[datasetKey] !== want) return false;
                } else {
                    if (node.attributes[key] === undefined) return false;
                    if (want !== undefined && node.attributes[key] !== want) return false;
                }
            }
        }
        return true;
    }

    const body = new Element('body');
    function findById(id) {
        const stack = [body];
        while (stack.length) {
            const node = stack.pop();
            if (node.attributes && node.attributes.id === id) return node;
            if (node.dataset && node.dataset.id === id) return node;
            stack.push(...node.children);
        }
        return null;
    }
    const document = {
        body,
        querySelector: (s) => body.querySelector(s),
        querySelectorAll: (s) => body.querySelectorAll(s),
        getElementById: (id) => findById(id),
    };
    function create(tag, attrs = {}) {
        const el = new Element(tag);
        Object.entries(attrs).forEach(([key, value]) => el.setAttribute(key, value));
        return el;
    }
    return { document, create, Element };
}

module.exports = { makeFakeDom };
