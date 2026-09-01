// Tanga Viewer — `TableView`: an editable table control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createTable } from '../controls-panel.js';

export class TableView extends ControlView {
    constructor({
        id,
        label = '',
        tooltip = '',
        columns = [],
        rows = [],
        allow_add_rows = true,
        allow_add_columns = true,
    } = {}) {
        super({ id, label, tooltip });
        this.columns = columns;
        this.rows = rows;
        this.allow_add_rows = allow_add_rows;
        this.allow_add_columns = allow_add_columns;
    }

    render() {
        return createTable({
            id: this.controlId,
            owner: 'layout',
            label: this.label,
            tooltip: this.tooltip,
            columns: this.columns,
            rows: this.rows,
            allow_add_rows: this.allow_add_rows,
            allow_add_columns: this.allow_add_columns,
            height: '100%',
        });
    }
}
