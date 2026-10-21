// Tanga Viewer — `ValueEditView`: a numeric stepper control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createValueEdit } from '../controls/value-edit.js';

export class ValueEditView extends ControlView {
    constructor({ id, label = '', tooltip = '', min = 0, max = 1, step = 0.1, digits = 2, value = 0, editable = true, unit = '' } = {}) {
        super({ id, label, tooltip });
        this.el.classList.add('tanga-value-edit-view');
        this.min = min;
        this.max = max;
        this.step = step;
        this.digits = digits;
        this.value = value;
        this.editable = editable;
        this.unit = unit;
    }

    update(node) {
        this.min = node.min ?? this.min;
        this.max = node.max ?? this.max;
        this.step = node.step ?? this.step;
        this.digits = node.digits ?? this.digits;
        this.value = node.value ?? this.value;
        this.editable = node.editable ?? this.editable;
        this.unit = node.unit ?? this.unit;
        super.update(node);
    }

    render() {
        return createValueEdit({
            id: this.controlId,
            owner: 'layout',
            label: this.label,
            hide_label: this.hide_label,
            tooltip: this.tooltip,
            min: this.min,
            max: this.max,
            step: this.step,
            digits: this.digits,
            value: this.value,
            editable: this.editable,
            unit: this.unit,
        });
    }
}
