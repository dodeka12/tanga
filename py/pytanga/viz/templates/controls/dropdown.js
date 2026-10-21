// Tanga Viewer — the dropdown (select) DOM factory.

import { registerControl, applyTooltip, applyControlStateToElement, sendControlEvent } from '../controls-panel.js';

export function createDropdown(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-dropdown';
    if (ctrl.variant === 'toolbar') wrapper.classList.add('tanga-toolbar-item');

    if (!ctrl.hide_label) {
        const label = document.createElement('label');
        label.textContent = ctrl.label || ctrl.id;
        wrapper.appendChild(label);
    }

    const select = document.createElement('select');
    select.className = 'tanga-select-input';
    const options = ctrl.options || [];
    for (const opt of options) {
        const option = document.createElement('option');
        if (typeof opt === 'string') {
            option.value = opt;
            option.textContent = opt;
            if (opt === ctrl.value) option.selected = true;
        } else {
            option.value = opt.value;
            option.textContent = opt.label;
            if (opt.value === ctrl.value) option.selected = true;
        }
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
        el: wrapper,
        apply: (value) => { select.value = value == null ? '' : String(value); },
        applyState: (state) => {
            if (state.options !== undefined) {
                const current = select.value;
                select.replaceChildren();
                for (const opt of state.options) {
                    const option = document.createElement('option');
                    option.value = typeof opt === 'string' ? opt : opt.value;
                    option.textContent = typeof opt === 'string' ? opt : opt.label;
                    select.appendChild(option);
                }
                if (Array.from(select.options).some((o) => o.value === current)) {
                    select.value = current;
                }
            }
            applyControlStateToElement(wrapper, state);
        },
    });
    applyTooltip(wrapper, ctrl);
    applyControlStateToElement(wrapper, ctrl);

    return wrapper;
}
