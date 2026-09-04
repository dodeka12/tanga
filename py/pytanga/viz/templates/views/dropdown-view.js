// Tanga Viewer — `DropdownView`: a dropdown/select control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createDropdown } from '../controls-panel.js';

export class DropdownView extends ControlView {
    constructor({ id, label = '', tooltip = '', options = [], value = '', variant = 'default' } = {}) {
        super({ id, label, tooltip });
        this.options = options;
        this.value = value;
        this.variant = variant;
    }

    render() {
        return createDropdown({
            id: this.controlId,
            owner: 'layout',
            label: this.label,
            tooltip: this.tooltip,
            options: this.options,
            value: this.value,
            variant: this.variant,
        });
    }
}
