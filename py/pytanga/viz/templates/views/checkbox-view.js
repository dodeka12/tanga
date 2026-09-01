// Tanga Viewer — `CheckboxView`: a checkbox control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createCheckbox } from '../controls-panel.js';

export class CheckboxView extends ControlView {
    constructor({ id, label = '', value = false, tooltip = '', variant = 'default' } = {}) {
        super({ id, label, tooltip });
        this.value = value;
        this.variant = variant;
    }

    render() {
        return createCheckbox({
            id: this.controlId,
            owner: 'layout',
            label: this.label,
            tooltip: this.tooltip,
            value: this.value,
            variant: this.variant,
        });
    }
}