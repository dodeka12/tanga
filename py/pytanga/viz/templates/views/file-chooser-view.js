// Tanga Viewer — `FileChooserView`: a file chooser control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createFileChooser } from '../controls-panel.js';

export class FileChooserView extends ControlView {
    constructor({ id, label = '', value = '', placeholder = '', root = null, accept = '' } = {}) {
        super({ id, label });
        this.value = value;
        this.placeholder = placeholder;
        this.root = root;
        this.accept = accept;
    }

    render() {
        return createFileChooser({
            id: this.controlId,
            label: this.label,
            value: this.value,
            placeholder: this.placeholder,
            root: this.root,
            accept: this.accept,
        });
    }
}
