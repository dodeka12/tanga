// Tanga Viewer — `ButtonView`: a button control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createButton } from '../controls-panel.js';

export class ButtonView extends ControlView {
    constructor({ id, label = '' } = {}) {
        super({ id, label });
    }

    render() {
        return createButton({ id: this.controlId, label: this.label });
    }
}
