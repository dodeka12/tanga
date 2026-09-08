// Tanga Viewer — the checkbox DOM factory.

import { registerControl, applyTooltip, sendControlEvent } from '../controls-panel.js';

export function createCheckbox(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-checkbox';
    if (ctrl.variant === 'menu') wrapper.classList.add('tanga-menu-item');
    if (ctrl.variant === 'toolbar') wrapper.classList.add('tanga-toolbar-item');

    const row = document.createElement('label');
    row.className = 'tanga-checkbox-row';

    const input = document.createElement('input');
    input.type = 'checkbox';
    input.checked = !!ctrl.value;
    input.className = 'tanga-checkbox-input';

    const text = document.createElement('span');
    text.className = 'tanga-checkbox-label';
    text.textContent = ctrl.label || ctrl.id;

    row.appendChild(input);
    row.appendChild(text);
    wrapper.appendChild(row);

    input.addEventListener('change', () => {
        sendControlEvent('control:change', ctrl.id, input.checked);
    });

    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());
    registerControl(ctrl.id, {
        owner: ctrl.owner || 'panel',
        kind: 'checkbox',
        apply: (value) => { input.checked = !!value; },
    });
    applyTooltip(wrapper, ctrl);

    return wrapper;
}
