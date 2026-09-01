// Tanga Viewer — `SliderView`: a slider control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createSlider } from '../controls-panel.js';

export class SliderView extends ControlView {
    constructor({ id, label = '', tooltip = '', min = 0, max = 1, step = 0.01, value = undefined, variant = 'default' } = {}) {
        super({ id, label, tooltip });
        this.min = min;
        this.max = max;
        this.step = step;
        this.value = value !== undefined ? value : min;
        this.variant = variant;
    }

    render() {
        return createSlider({
            id: this.controlId,
            owner: 'layout',
            label: this.label,
            tooltip: this.tooltip,
            min: this.min,
            max: this.max,
            step: this.step,
            value: this.value,
            variant: this.variant,
        });
    }
}
