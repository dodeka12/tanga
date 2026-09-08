// Tanga Viewer — the read-only text label DOM factory.

import { registerControl, applyTooltip } from '../controls-panel.js';

export function createLabel(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-label';

    const text = document.createElement('div');
    text.className = 'tanga-label-text';
    text.textContent = ctrl.value != null ? String(ctrl.value) : '';
    if (ctrl.font_size != null) text.style.fontSize = `${ctrl.font_size}px`;
    wrapper.appendChild(text);

    registerControl(ctrl.id, {
        owner: ctrl.owner || 'panel',
        kind: 'label',
        apply: (value) => { text.textContent = value == null ? '' : String(value); },
    });
    applyTooltip(wrapper, ctrl);

    return wrapper;
}
