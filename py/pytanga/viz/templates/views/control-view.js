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
        // Don't let a flex parent shrink the control below its content.
        this.el.style.flexShrink = '0';
        // Sensible floors so a StackView can size to its controls.
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
