// Tanga Viewer — `SpacerView`: an empty, transparent, non-interactive filler.

import { View } from './view.js';

/** An empty, fully-flexible pane used to fill leftover space. */
export class SpacerView extends View {
    constructor() {
        super();
        this.el.classList.add('tanga-spacer');
        this.el.style.pointerEvents = 'none';
    }
}
