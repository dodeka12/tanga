// Tanga Viewer — `ValueEditView`: a numeric stepper control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createValueEdit } from '../controls-panel.js';

export class ValueEditView extends ControlView {
    constructor({ id, label = '', tooltip = '', min = 0, max = 1, step = 0.1, digits = 2, value = 0, editable = true } = {}) {
        super({ id, label, tooltip });
        this.min = min;
        this.max = max;
        this.step = step;
        this.digits = digits;
        this.value = value;
        this.editable = editable;
    }

    render() {
        return createValueEdit({
            id: this.controlId,
            owner: 'layout',
            label: this.label,
            tooltip: this.tooltip,
            min: this.min,
            max: this.max,
            step: this.step,
            digits: this.digits,
            value: this.value,
            editable: this.editable,
        });
    }
}
