// Tanga Viewer — `ProgressBarView`: a progress bar control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createProgressBar } from '../controls/progress-bar.js';

export class ProgressBarView extends ControlView {
    constructor({ id, title = '', value = 0, total = 0, indeterminate = false, text = '' } = {}) {
        super({ id });
        this.title = title;
        this.value = value;
        this.total = total;
        this.indeterminate = indeterminate;
        this.text = text;
    }

    update(node) {
        this.title = node.title ?? this.title;
        this.value = node.value ?? this.value;
        this.total = node.total ?? this.total;
        this.indeterminate = node.indeterminate ?? this.indeterminate;
        this.text = node.text ?? this.text;
        super.update(node);
    }

    render() {
        return createProgressBar({
            id: this.controlId,
            owner: 'layout',
            title: this.title,
            value: this.value,
            total: this.total,
            indeterminate: this.indeterminate,
            text: this.text,
        });
    }
}
