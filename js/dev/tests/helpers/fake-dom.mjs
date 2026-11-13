// Tanga — minimal DOM stand-in for unit-testing layout views under `node --test`.
//
// The layout views (View, StackView, GroupView, ParamsView …) only touch a
// small, well-defined slice of the DOM: element creation, `classList`, inline
// `style`, attribute/tooltip plumbing, event listeners and element extents.
// `installFakeDom()` provides exactly that, so a view can be constructed and
// driven in Node without a browser (or a jsdom dependency).
//
// Call it *before* constructing views; the modules themselves import fine
// without a DOM.

class FakeClassList {
    constructor() { this._names = new Set(); }
    add(...names) { names.forEach((n) => this._names.add(n)); }
    remove(...names) { names.forEach((n) => this._names.delete(n)); }
    contains(name) { return this._names.has(name); }
    toggle(name, force) {
        const on = force === undefined ? !this._names.has(name) : !!force;
        if (on) this._names.add(name);
        else this._names.delete(name);
        return on;
    }
}

class FakeElement extends EventTarget {
    constructor(tagName = 'div') {
        super();
        this.tagName = String(tagName).toUpperCase();
        this.children = [];
        this.parentNode = null;
        this.style = {};
        this.classList = new FakeClassList();
        this.className = '';
        this.dataset = {};
        this.textContent = '';
        this.title = '';
        this._attributes = new Map();
    }

    appendChild(child) {
        if (child && child.parentNode) child.remove();
        if (child) child.parentNode = this;
        this.children.push(child);
        return child;
    }

    insertBefore(child, reference) {
        const idx = this.children.indexOf(reference);
        if (child && child.parentNode) child.remove();
        if (child) child.parentNode = this;
        if (idx === -1) this.children.push(child);
        else this.children.splice(idx, 0, child);
        return child;
    }

    removeChild(child) {
        const idx = this.children.indexOf(child);
        if (idx !== -1) this.children.splice(idx, 1);
        if (child) child.parentNode = null;
        return child;
    }

    replaceChildren(...nodes) {
        for (const child of this.children) child.parentNode = null;
        this.children = [];
        for (const node of nodes.flat()) this.appendChild(node);
    }

    remove() {
        if (this.parentNode) this.parentNode.removeChild(this);
    }

    setAttribute(name, value) { this._attributes.set(name, String(value)); }
    getAttribute(name) {
        return this._attributes.has(name) ? this._attributes.get(name) : null;
    }
    removeAttribute(name) { this._attributes.delete(name); }

    querySelector() { return null; }
    querySelectorAll() { return []; }

    getBoundingClientRect() {
        return { width: 0, height: 0, top: 0, left: 0, right: 0, bottom: 0 };
    }
}

class FakeResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
}

const COMPUTED_STYLE = {
    display: 'block',
    rowGap: '0px',
    columnGap: '0px',
    gap: '0px',
    minWidth: '0px',
    minHeight: '0px',
    marginBottom: '0px',
    paddingBottom: '0px',
    borderBottomWidth: '0px',
};

/** Install the globals the layout views expect.  Returns the fake document. */
export function installFakeDom() {
    const document = {
        createElement: (tag) => new FakeElement(tag),
        createElementNS: (_ns, tag) => new FakeElement(tag),
        getElementById: () => null,
        querySelector: () => null,
        querySelectorAll: () => [],
        addEventListener() {},
        removeEventListener() {},
        head: new FakeElement('head'),
        body: new FakeElement('body'),
    };
    globalThis.document = document;
    globalThis.window = {
        addEventListener() {},
        removeEventListener() {},
        innerWidth: 1400,
        innerHeight: 900,
    };
    globalThis.ResizeObserver = FakeResizeObserver;
    globalThis.getComputedStyle = () => ({ ...COMPUTED_STYLE });
    return document;
}

export { FakeElement };
