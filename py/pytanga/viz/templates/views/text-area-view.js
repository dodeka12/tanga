// Tanga Viewer — `TextAreaView`: a multi-line text control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createTextArea } from '../controls-panel.js';

export class TextAreaView extends ControlView {
    constructor({ id, label = '', value = '', placeholder = '', rows = 4, tooltip = '' } = {}) {
        super({ id, label, tooltip });
        this.value = value;
        this.placeholder = placeholder;
        this.rows = rows;
    }

    render() {
        return createTextArea({
            id: this.controlId,
            label: this.label,
            tooltip: this.tooltip,
            value: this.value,
            placeholder: this.placeholder,
            rows: this.rows,
        });
    }
}