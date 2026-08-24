// Tanga Viewer — `DropdownView`: a dropdown/select control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createDropdown } from '../controls-panel.js';

export class DropdownView extends ControlView {
    constructor({ id, label = '', options = [], default: defaultValue = '' } = {}) {
        super({ id, label });
        this.options = options;
        this.default = defaultValue;
    }

    render() {
        return createDropdown({
            id: this.controlId,
            label: this.label,
            options: this.options,
            default: this.default,
        });
    }
}
