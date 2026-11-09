// Tanga Viewer — the button DOM factory (icon + label, click-only).

import { applyTooltip, registerControl, applyControlStateToElement, sendControlEvent, createIconElement } from '../controls-panel.js';

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
        // Icon-only buttons have no visible text, so keep the label as hover
        // text (switch-aware) and expose it to screen readers.
        const hoverText = ctrl.tooltip || ctrl.label || ctrl.id || '';
        applyTooltip(btn, hoverText);
        btn.setAttribute('aria-label', hoverText);
    }

    wrapper.appendChild(btn);

    btn.addEventListener('click', () => {
        sendControlEvent('control:click', ctrl.id, null);
    });

    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());
    applyTooltip(wrapper, ctrl);

    registerControl(ctrl.id, {
        owner: ctrl.owner || 'panel',
        kind: 'button',
        el: wrapper,
        apply: () => {},
        applyState: (state) => {
            applyControlStateToElement(wrapper, state);
            if (ctrl.icon_only && state.tooltip !== undefined) {
                const hoverText = state.tooltip || ctrl.label || ctrl.id || '';
                applyTooltip(btn, hoverText);
                btn.setAttribute('aria-label', hoverText);
            }
        },
    });
    applyControlStateToElement(wrapper, ctrl);

    return wrapper;
}
