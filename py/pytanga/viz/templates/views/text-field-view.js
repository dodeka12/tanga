// Tanga Viewer — `TextFieldView`: a single-line text control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createTextField } from '../controls-panel.js';

export class TextFieldView extends ControlView {
    constructor({ id, label = '', value = '', placeholder = '', tooltip = '' } = {}) {
        super({ id, label, tooltip });
        this.value = value;
        this.placeholder = placeholder;
    }

    render() {
        return createTextField({
            id: this.controlId,
            owner: 'layout',
            label: this.label,
            tooltip: this.tooltip,
            value: this.value,
            placeholder: this.placeholder,
        });
    }
}