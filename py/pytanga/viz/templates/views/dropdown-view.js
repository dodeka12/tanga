// Tanga Viewer — `DropdownView`: a dropdown/select control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createDropdown } from '../controls/dropdown.js';

export class DropdownView extends ControlView {
    constructor({ id, label = '', tooltip = '', options = [], value = '', variant = 'default' } = {}) {
        super({ id, label, tooltip });
        this.options = options;
        this.value = value;
        this.variant = variant;
    }

    update(node) {
        this.options = node.options ?? this.options;
        this.value = node.value ?? this.value;
        this.variant = node.variant ?? this.variant;
        super.update(node);
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
