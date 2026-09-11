// Tanga Viewer — the color picker DOM factory.

import { registerControl, applyTooltip, attachDebouncedChange } from '../controls-panel.js';

export function createColorPicker(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-color-picker';

    const label = document.createElement('label');
    label.textContent = ctrl.label || ctrl.id;
    wrapper.appendChild(label);

    const input = document.createElement('input');
    input.type = 'color';
    input.value = ctrl.value || '#ffffff';
    input.className = 'tanga-color-input';
    wrapper.appendChild(input);

    attachDebouncedChange(input, ctrl.id);
    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());
    registerControl(ctrl.id, {
        owner: ctrl.owner || 'panel',
        kind: 'color',
        apply: (value) => { input.value = value == null ? '#ffffff' : String(value); },
    });
    applyTooltip(wrapper, ctrl);

    return wrapper;
}
