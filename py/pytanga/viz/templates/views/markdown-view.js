// Tanga Viewer — `MarkdownView`: a read-only rendered-markdown control (with KaTeX).

import { ControlView } from './control-view.js';
import { createMarkdown } from '../controls/markdown.js';

export class MarkdownView extends ControlView {
    constructor({ id, value = '', font_size = null } = {}) {
        super({ id });
        this.value = value;
        this.fontSize = font_size;
        this._applyFontSize();
    }

    update(node) {
        this.value = node.value ?? this.value;
        if ('font_size' in node) this.fontSize = node.font_size ?? null;
        this._applyFontSize();
        super.update(node);
    }

    _onMounted() {
        super._onMounted();
        this._applyFontSize();
    }

    // Instance override: the custom property is inherited by the rendered
    // `.tanga-markdown-body`, so the theme still owns every other markdown view.
    _applyFontSize() {
        if (this.fontSize == null) {
            this.el.style.removeProperty('--tanga-font-size-markdown');
        } else {
            this.el.style.setProperty('--tanga-font-size-markdown', `${this.fontSize}px`);
        }
    }

    render() {
        return createMarkdown({
            id: this.controlId,
            owner: 'layout',
            value: this.value,
        });
    }
}
