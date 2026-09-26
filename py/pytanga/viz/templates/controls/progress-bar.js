// Tanga Viewer — the progress-bar DOM factory (determinate + indeterminate).

import { registerControl, applyTooltip, applyControlStateToElement } from '../controls-panel.js';

export function createProgressBar(ctrl) {
    const wrapper = document.createElement('div');
    wrapper.className = 'tanga-control tanga-progress';

    const titleEl = document.createElement('div');
    titleEl.className = 'tanga-progress-title';
    wrapper.appendChild(titleEl);

    const track = document.createElement('div');
    track.className = 'tanga-progress-track';
    const fill = document.createElement('div');
    fill.className = 'tanga-progress-fill';
    track.appendChild(fill);
    wrapper.appendChild(track);

    const valueEl = document.createElement('div');
    valueEl.className = 'tanga-progress-value';
    wrapper.appendChild(valueEl);

    const textEl = document.createElement('div');
    textEl.className = 'tanga-progress-text';
    wrapper.appendChild(textEl);

    function render(payload) {
        const title = payload.title != null ? String(payload.title) : '';
        titleEl.textContent = title;
        titleEl.style.display = title ? '' : 'none';

        const total = Number(payload.total) || 0;
        const indeterminate = !!payload.indeterminate;
        track.classList.toggle('tanga-progress-indeterminate', indeterminate);

        if (indeterminate) {
            fill.style.width = '';
            valueEl.textContent = '';
        } else if (total > 0) {
            const pct = Math.max(0, Math.min(100, (Number(payload.value) / total) * 100));
            fill.style.width = pct + '%';
            valueEl.textContent = Math.round(pct) + '%';
        } else {
            // Not indeterminate and no total: an empty (stopped) bar.
            fill.style.width = '0%';
            valueEl.textContent = '';
        }

        const text = payload.text != null ? String(payload.text) : '';
        textEl.textContent = text;
        textEl.style.display = text ? '' : 'none';
    }

    render(ctrl);

    registerControl(ctrl.id, {
        owner: ctrl.owner || 'panel',
        kind: 'progress',
        el: wrapper,
        apply: (payload) => {
            if (payload == null) return;
            render({ ...ctrl, ...payload });
            // Fold back so later partial updates keep earlier fields.
            if (payload.title != null) ctrl.title = payload.title;
            if (payload.value != null) ctrl.value = payload.value;
            if (payload.total != null) ctrl.total = payload.total;
            if (payload.indeterminate != null) ctrl.indeterminate = payload.indeterminate;
            if (payload.text != null) ctrl.text = payload.text;
        },
    });
    applyTooltip(wrapper, ctrl);
    applyControlStateToElement(wrapper, ctrl);

    return wrapper;
}
