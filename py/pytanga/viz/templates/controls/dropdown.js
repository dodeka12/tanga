// Tanga Viewer — the dropdown (select) DOM factory.

import { registerControl, applyTooltip, sendControlEvent } from '../controls-panel.js';

export function createDropdown(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-dropdown';
    if (ctrl.variant === 'toolbar') wrapper.classList.add('tanga-toolbar-item');

    const label = document.createElement('label');
    label.textContent = ctrl.label || ctrl.id;
    wrapper.appendChild(label);

    const select = document.createElement('select');
    select.className = 'tanga-select-input';
    const options = ctrl.options || [];
    for (const opt of options) {
        const option = document.createElement('option');
        option.value = opt;
        option.textContent = opt;
        if (opt === ctrl.value) option.selected = true;
        select.appendChild(option);
    }
    wrapper.appendChild(select);

    select.addEventListener('change', () => {
        sendControlEvent('control:change', ctrl.id, select.value);
    });

    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());
    registerControl(ctrl.id, {
        owner: ctrl.owner || 'panel',
        kind: 'dropdown',
        apply: (value) => { select.value = value == null ? '' : String(value); },
    });
    applyTooltip(wrapper, ctrl);

    return wrapper;
}
