// Tanga Viewer — `MarkdownView`: a read-only rendered-markdown control (with KaTeX).

import { ControlView } from './control-view.js';
import { createMarkdown } from '../controls/markdown.js';

export class MarkdownView extends ControlView {
    constructor({ id, value = '' } = {}) {
        super({ id });
        this.value = value;
    }

    update(node) {
        this.value = node.value ?? this.value;
        super.update(node);
    }

    render() {
        return createMarkdown({
            id: this.controlId,
            owner: 'layout',
            value: this.value,
        });
    }
}
