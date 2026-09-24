// Tanga Viewer — `TextAreaView`: a multi-line text control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createTextArea } from '../controls/text-area.js';

export class TextAreaView extends ControlView {
    constructor({ id, label = '', value = '', placeholder = '', rows = 4, tooltip = '' } = {}) {
        super({ id, label, tooltip });
        this.value = value;
        this.placeholder = placeholder;
        this.rows = rows;
    }

    update(node) {
        this.value = node.value ?? this.value;
        this.placeholder = node.placeholder ?? this.placeholder;
        this.rows = node.rows ?? this.rows;
        super.update(node);
    }

    render() {
        return createTextArea({
            id: this.controlId,
            owner: 'layout',
            label: this.label,
            tooltip: this.tooltip,
            value: this.value,
            placeholder: this.placeholder,
            rows: this.rows,
        });
    }
}