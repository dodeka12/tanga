// Tanga Viewer — `SliderView`: a slider control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createSlider } from '../controls-panel.js';

export class SliderView extends ControlView {
    constructor({ id, label = '', min = 0, max = 1, step = 0.01, default: defaultValue } = {}) {
        super({ id, label });
        this.min = min;
        this.max = max;
        this.step = step;
        this.default = defaultValue !== undefined ? defaultValue : min;
    }

    render() {
        return createSlider({
            id: this.controlId,
            label: this.label,
            min: this.min,
            max: this.max,
            step: this.step,
            default: this.default,
        });
    }
}
