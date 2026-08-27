// Tanga Viewer — `ColorPickerView`: a color picker control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createColorPicker } from '../controls-panel.js';

export class ColorPickerView extends ControlView {
    constructor({ id, label = '', value = '#ffffff', tooltip = '' } = {}) {
        super({ id, label, tooltip });
        this.value = value;
    }

    render() {
        return createColorPicker({
            id: this.controlId,
            label: this.label,
            tooltip: this.tooltip,
            value: this.value,
        });
    }
}