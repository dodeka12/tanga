// Tanga Viewer — `ControlView` base: a single HTML control rendered as a `View`
// (no scene, no Three.js).  Subclasses fill `render()` with the control element.

import { View } from './view.js';

export class ControlView extends View {
    constructor({ id, label = '', tooltip = '' } = {}) {
        super();
        this.controlId = id;
        this.label = label;
        this.tooltip = tooltip;
        this.el.classList.add('tanga-control-view');
        // Sensible floors so a StackView can size to its controls.  These are a
        // safety net for direct JS construction; `build.js` overrides them with
        // the Python-serialized values (which may be `null` to disable them).
        this.minWidth = { value: 120, unit: 'px' };
        this.minHeight = { value: 32, unit: 'px' };
    }

    _onMounted() {
        const el = this.render();
        if (el) this.el.appendChild(el);
    }

    /** Return the control DOM element (subclass responsibility). */
    render() {
        return null;
    }
}
