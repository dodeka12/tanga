// Tanga Viewer — the numeric stepper DOM factory (input + up/down buttons).

import { registerControl, applyTooltip, sendControlEvent, createIconElement } from '../controls-panel.js';

export function createValueEdit(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-value-edit';

    const label = document.createElement('label');
    label.textContent = ctrl.label || ctrl.id;
    wrapper.appendChild(label);

    const min = ctrl.min !== undefined ? ctrl.min : 0;
    const max = ctrl.max !== undefined ? ctrl.max : 1;
    const step = ctrl.step !== undefined ? ctrl.step : 0.1;
    const digits = ctrl.digits !== undefined ? ctrl.digits : 2;
    const editable = ctrl.editable !== false;

    const clamp = (v) => Math.min(max, Math.max(min, v));
    const round = (v) => Number(v.toFixed(digits));

    let value = round(clamp(ctrl.value !== undefined ? ctrl.value : min));

    const input = document.createElement('input');
    input.type = 'text';
    input.inputMode = 'decimal';
    input.readOnly = !editable;
    input.className = 'tanga-value-input';
    input.value = value.toFixed(digits);

    const row = document.createElement('div');
    row.className = 'tanga-value-edit-row';

    const upBtn = document.createElement('button');
    upBtn.type = 'button';
    upBtn.className = 'tanga-step-button';
    upBtn.title = 'Increase';
    upBtn.appendChild(createIconElement('uc:▲'));

    const downBtn = document.createElement('button');
    downBtn.type = 'button';
    downBtn.className = 'tanga-step-button';
    downBtn.title = 'Decrease';
    downBtn.appendChild(createIconElement('uc:▼'));

    row.appendChild(input);
    row.appendChild(upBtn);
    row.appendChild(downBtn);
    wrapper.appendChild(row);

    const commit = () => {
        input.value = value.toFixed(digits);
        sendControlEvent('control:change', ctrl.id, value);
    };

    const stepValue = (direction) => {
        value = round(clamp(value + direction * step));
        commit();
    };

    const commitText = () => {
        const parsed = parseFloat(input.value);
        if (Number.isFinite(parsed)) {
            value = round(clamp(parsed));
            input.value = value.toFixed(digits);
            sendControlEvent('control:change', ctrl.id, value);
        } else {
            input.value = value.toFixed(digits);
        }
    };

    upBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        stepValue(1);
    });
    downBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        stepValue(-1);
    });

    // Arrow keys step the value while the control is hovered/focused.
    input.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowUp' || e.key === 'ArrowRight') {
            e.preventDefault();
            stepValue(1);
        } else if (e.key === 'ArrowDown' || e.key === 'ArrowLeft') {
            e.preventDefault();
            stepValue(-1);
        } else if (e.key === 'Enter' && editable) {
            e.preventDefault();
            commitText();
        }
    });

    // When editable, parse a typed value on blur/Enter (clamped + rounded).
    if (editable) {
        input.addEventListener('change', commitText);
    }

    // Focus the input on hover so arrow keys work without an explicit click.
    wrapper.addEventListener('mouseenter', () => {
        input.focus({ preventScroll: true });
    });

    // Scroll wheel steps the value (up = increase).
    wrapper.addEventListener(
        'wheel',
        (e) => {
            e.preventDefault();
            stepValue(e.deltaY < 0 ? 1 : -1);
        },
        { passive: false }
    );

    // Stop propagation to prevent orbit control interference.
    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());

    registerControl(ctrl.id, {
        owner: ctrl.owner || 'panel',
        kind: 'value_edit',
        apply: (v) => {
            value = round(clamp(Number(v)));
            input.value = value.toFixed(digits);
        },
    });
    applyTooltip(wrapper, ctrl);

    return wrapper;
}
