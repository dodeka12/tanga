// Tanga Viewer — the button DOM factory (icon + label, click-only).

import { applyTooltip, sendControlEvent, createIconElement } from '../controls-panel.js';

export function createButton(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-button';
    if (ctrl.variant === 'menu') wrapper.classList.add('tanga-menu-item');

    const btn = document.createElement('button');
    btn.className = 'tanga-action-button';

    if (ctrl.icon) {
        btn.appendChild(createIconElement(ctrl.icon));
        if (!ctrl.icon_only && (ctrl.label || ctrl.id)) {
            btn.appendChild(document.createTextNode(' ' + (ctrl.label || ctrl.id)));
        }
    } else {
        btn.textContent = ctrl.label || ctrl.id;
    }

    if (ctrl.icon_only) {
        btn.classList.add('tanga-icon-button');
        btn.title = ctrl.tooltip || ctrl.label || ctrl.id || '';
    }

    wrapper.appendChild(btn);

    btn.addEventListener('click', () => {
        sendControlEvent('control:click', ctrl.id, null);
    });

    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());
    applyTooltip(wrapper, ctrl);

    return wrapper;
}
