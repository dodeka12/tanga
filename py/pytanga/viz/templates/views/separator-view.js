// Tanga Viewer — `SeparatorView`: a thin 1px divider line with spacing.
// The line's orientation is perpendicular to the container it lives in; an
// "auto" orientation is resolved by the parent `StackView` at mount time.

import { Size } from './size.js';
import { View } from './view.js';

const DEFAULT_SPACING = 6;

export class SeparatorView extends View {
    constructor({ orientation = 'auto', spacing = null } = {}) {
        super();
        this.orientation = orientation;
        this.spacing = spacing == null ? DEFAULT_SPACING : spacing;
        this.el.classList.add('tanga-separator');
        if (orientation === 'horizontal' || orientation === 'vertical') {
            this._applyOrientation(orientation);
        }
    }

    // Called by `StackView.addChild` (and its ToolbarView/MenuView/GroupView
    // subclasses) so an "auto" separator can derive the perpendicular
    // orientation from the container's direction.
    resolveOrientation(direction) {
        if (this.orientation !== 'auto') return;
        this._applyOrientation(direction === 'horizontal' ? 'vertical' : 'horizontal');
    }

    _applyOrientation(orientation) {
        this.orientation = orientation;
        this.el.classList.remove('tanga-separator-horizontal', 'tanga-separator-vertical');
        this.el.classList.add(`tanga-separator-${orientation}`);
        if (orientation === 'vertical') {
            this.el.style.margin = `0 ${this.spacing}px`;
            this.preferredWidth = Size.px(1);
        } else {
            this.el.style.margin = `${this.spacing}px 0`;
            this.preferredHeight = Size.px(1);
        }
    }
}
