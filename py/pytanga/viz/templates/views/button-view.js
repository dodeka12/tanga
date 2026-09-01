// Tanga Viewer — `ButtonView`: a button control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createButton } from '../controls-panel.js';

export class ButtonView extends ControlView {
    constructor({ id, label = '', icon = null, icon_only = false, tooltip = '' } = {}) {
        super({ id, label, tooltip });
        this.icon = icon;
        this.icon_only = icon_only;
    }

    render() {
        return createButton({
            id: this.controlId,
            owner: 'layout',
            label: this.label,
            tooltip: this.tooltip,
            icon: this.icon,
            icon_only: this.icon_only,
        });
    }
}
