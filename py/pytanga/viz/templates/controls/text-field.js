// Tanga Viewer — the single-line text input DOM factory.

import { registerControl, applyTooltip, attachDebouncedChange } from '../controls-panel.js';

export function createTextField(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-text-field';

    const label = document.createElement('label');
    label.textContent = ctrl.label || ctrl.id;
    wrapper.appendChild(label);

    const input = document.createElement('input');
    input.type = 'text';
    input.value = ctrl.value || '';
    input.placeholder = ctrl.placeholder || '';
    input.className = 'tanga-text-input';
    wrapper.appendChild(input);

    attachDebouncedChange(input, ctrl.id);
    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());
    registerControl(ctrl.id, {
        owner: ctrl.owner || 'panel',
        kind: 'text',
        apply: (value) => { input.value = value == null ? '' : String(value); },
    });
    applyTooltip(wrapper, ctrl);

    return wrapper;
}
