// Tanga Viewer — `DropdownView`: a dropdown/select control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createDropdown } from '../controls-panel.js';

export class DropdownView extends ControlView {
    constructor({ id, label = '', tooltip = '', options = [], value = '' } = {}) {
        super({ id, label, tooltip });
        this.options = options;
        this.value = value;
    }

    render() {
        return createDropdown({
            id: this.controlId,
            label: this.label,
            tooltip: this.tooltip,
            options: this.options,
            value: this.value,
        });
    }
}
