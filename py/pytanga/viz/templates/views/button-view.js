// Tanga Viewer — `ButtonView`: a button control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createButton } from '../controls/button.js';

export class ButtonView extends ControlView {
    constructor({ id, label = '', icon = null, icon_only = false, tooltip = '', variant = 'default' } = {}) {
        super({ id, label, tooltip });
        this.icon = icon;
        this.icon_only = icon_only;
        this.variant = variant;
    }

    update(node) {
        this.icon = node.icon ?? this.icon;
        this.icon_only = node.icon_only ?? this.icon_only;
        this.variant = node.variant ?? this.variant;
        super.update(node);
    }

    render() {
        return createButton({
            id: this.controlId,
            owner: 'layout',
            label: this.label,
            tooltip: this.tooltip,
            icon: this.icon,
            icon_only: this.icon_only,
            variant: this.variant,
        });
    }
}
