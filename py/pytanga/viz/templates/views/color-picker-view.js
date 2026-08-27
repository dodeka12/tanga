// Tanga Viewer — `ColorPickerView`: a color picker control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createColorPicker } from '../controls-panel.js';

export class ColorPickerView extends ControlView {
    constructor({ id, label = '', default: defaultValue = '#ffffff', tooltip = '' } = {}) {
        super({ id, label, tooltip });
        this.default = defaultValue;
    }

    render() {
        return createColorPicker({
            id: this.controlId,
            label: this.label,
            tooltip: this.tooltip,
            default: this.default,
        });
    }
}