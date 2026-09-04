// Tanga Viewer — `LabelView`: a read-only text label rendered as a `View`.

import { ControlView } from './control-view.js';
import { createLabel } from '../controls-panel.js';

export class LabelView extends ControlView {
    constructor({ id, value = '', font_size = 14 } = {}) {
        super({ id });
        this.value = value;
        this.font_size = font_size;
    }

    render() {
        return createLabel({
            id: this.controlId,
            owner: 'layout',
            value: this.value,
            font_size: this.font_size,
        });
    }
}
