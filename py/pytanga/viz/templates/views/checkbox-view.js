// Tanga Viewer — `CheckboxView`: a checkbox control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createCheckbox } from '../controls-panel.js';

export class CheckboxView extends ControlView {
    constructor({ id, label = '', default: defaultValue = false, tooltip = '' } = {}) {
        super({ id, label, tooltip });
        this.default = defaultValue;
    }

    render() {
        return createCheckbox({
            id: this.controlId,
            label: this.label,
            tooltip: this.tooltip,
            default: this.default,
        });
    }
}