// Tanga Viewer — `ColorPickerView`: a color picker control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createColorPicker } from '../controls/color-picker.js';

export class ColorPickerView extends ControlView {
    constructor({ id, label = '', value = '#ffffff', tooltip = '' } = {}) {
        super({ id, label, tooltip });
        this.el.classList.add('tanga-color-picker-view');
        this.value = value;
    }

    update(node) {
        this.value = node.value ?? this.value;
        super.update(node);
    }

    render() {
        return createColorPicker({
            id: this.controlId,
            owner: 'layout',
            label: this.label,
            hide_label: this.hide_label,
            tooltip: this.tooltip,
            value: this.value,
        });
    }
}