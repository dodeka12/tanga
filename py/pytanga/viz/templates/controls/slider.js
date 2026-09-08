// Tanga Viewer — the slider DOM factory (range input + value readout).

import { registerControl, applyTooltip, sendControlEvent, throttledSend, throttledFlush } from '../controls-panel.js';

export function createSlider(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-slider';
    if (ctrl.variant === 'menu') wrapper.classList.add('tanga-menu-item');
    if (ctrl.variant === 'toolbar') wrapper.classList.add('tanga-toolbar-item');

    const labelRow = document.createElement('div');
    labelRow.className = 'tanga-control-label-row';

    const label = document.createElement('label');
    label.textContent = ctrl.label || ctrl.id;

    const valueSpan = document.createElement('span');
    valueSpan.className = 'tanga-value';
    const ctrlValue = ctrl.value !== undefined ? ctrl.value : ctrl.min;
    valueSpan.textContent = String(ctrlValue);

    labelRow.appendChild(label);
    labelRow.appendChild(valueSpan);
    wrapper.appendChild(labelRow);

    const input = document.createElement('input');
    input.type = 'range';
    input.min = ctrl.min !== undefined ? ctrl.min : 0;
    input.max = ctrl.max !== undefined ? ctrl.max : 1;
    input.step = ctrl.step !== undefined ? ctrl.step : 0.01;
    input.value = ctrlValue;
    input.className = 'tanga-range-input';
    wrapper.appendChild(input);

    // Immediate visual update
    input.addEventListener('input', () => {
        valueSpan.textContent = input.value;
    });

    // Throttled WebSocket send while dragging (~25 Hz max)
    input.addEventListener('input', () => {
        throttledSend('control:change', ctrl.id, parseFloat(input.value));
    });

    // Flush final value when the user releases the slider (change event), and
    // send a distinct release notification for drag-end handling.
    input.addEventListener('change', () => {
        throttledFlush('control:change', ctrl.id);
        sendControlEvent('control:release', ctrl.id, parseFloat(input.value));
    });

    // Notify the backend when the user presses the slider (start of drag).
    input.addEventListener('pointerdown', () => {
        sendControlEvent('control:press', ctrl.id, parseFloat(input.value));
    });

    // Stop propagation to prevent orbit control interference
    wrapper.addEventListener('pointerdown', (e) => e.stopPropagation());
    registerControl(ctrl.id, {
        owner: ctrl.owner || 'panel',
        kind: 'slider',
        apply: (value) => {
            const coerced = Number(value);
            input.value = coerced;
            valueSpan.textContent = String(coerced);
        },
    });
    applyTooltip(wrapper, ctrl);

    return wrapper;
}
