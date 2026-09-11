// Tanga Viewer — the multi-line textarea DOM factory.

import { registerControl, applyTooltip, attachDebouncedChange } from '../controls-panel.js';

export function createTextArea(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-text-area';

    const label = document.createElement('label');
    label.textContent = ctrl.label || ctrl.id;
    wrapper.appendChild(label);

    const input = document.createElement('textarea');
    input.value = ctrl.value || '';
    input.placeholder = ctrl.placeholder || '';
    input.rows = ctrl.rows !== undefined ? ctrl.rows : 4;
    input.className = 'tanga-text-input tanga-textarea';
    wrapper.appendChild(input);

    attachDebouncedChange(input, ctrl.id);
    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());
    registerControl(ctrl.id, {
        owner: ctrl.owner || 'panel',
        kind: 'textarea',
        apply: (value) => { input.value = value == null ? '' : String(value); },
    });
    applyTooltip(wrapper, ctrl);

    return wrapper;
}
