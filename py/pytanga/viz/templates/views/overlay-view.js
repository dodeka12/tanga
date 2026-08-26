// Tanga Viewer — `OverlayView`: a full-screen overlay container for view-based
// elements (banners).  Spans the viewport but lets pointer events fall through,
// so the scene beneath stays interactive until a child opts in via its own
// `pointer-events: auto`.

import { View } from './view.js';

export class OverlayView extends View {
    constructor() {
        super();
        this.children = [];
        this.el.classList.add('tanga-overlay');
        Object.assign(this.el.style, {
            position: 'fixed',
            top: '0',
            left: '0',
            right: '0',
            bottom: '0',
            pointerEvents: 'none',
            zIndex: '500',
        });
    }

    addChild(view) {
        view.mount(this.el);
        this.children.push(view);
        return view;
    }

    removeChild(view) {
        const idx = this.children.indexOf(view);
        if (idx !== -1) this.children.splice(idx, 1);
        view.unmount();
    }

    clear() {
        for (const child of [...this.children]) child.unmount();
        this.children = [];
    }

    destroy() {
        this.clear();
        super.destroy();
    }
}
