// Tanga Viewer — `SpacerView`: an empty, transparent, non-interactive filler.

import { View } from './view.js';

/**
 * An empty, fully-flexible filler pane.  Its `fr` preferred size (set on the
 * Python side and applied by `build.js::applySizeSpecs`) makes
 * `StackView.addChild` assign `flex: 1 1 0`, so it grows along a flow
 * container's main axis.  Under `SplitView` the spacer is positioned
 * absolutely, so it needs no flex there.
 */
export class SpacerView extends View {
    constructor() {
        super();
        this.el.classList.add('tanga-spacer');
        this.el.style.pointerEvents = 'none';
    }
}
