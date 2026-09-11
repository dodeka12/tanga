// Tanga Viewer — `TableView`: an editable table control rendered as a `View`.

import { ControlView } from './control-view.js';
import { createTable } from '../controls/table.js';

export class TableView extends ControlView {
    constructor({
        id,
        label = '',
        tooltip = '',
        columns = [],
        rows = [],
        allow_add_rows = true,
        allow_add_columns = true,
        allow_delete_rows = true,
        show_column_titles = true,
        show_row_numbers = false,
        allow_delete_columns = true,
        sortable = true,
        column_types = [],
        column_widths = null,
        row_height = null,
        sort = null,
    } = {}) {
        super({ id, label, tooltip });
        this.columns = columns;
        this.rows = rows;
        this.allow_add_rows = allow_add_rows;
        this.allow_add_columns = allow_add_columns;
        this.allow_delete_rows = allow_delete_rows;
        this.show_column_titles = show_column_titles;
        this.show_row_numbers = show_row_numbers;
        this.allow_delete_columns = allow_delete_columns;
        this.sortable = sortable;
        this.column_types = column_types;
        this.column_widths = column_widths;
        this.row_height = row_height;
        this.sort = sort;

        // A table needs more room than a single form control; default a min and
        // a natural preferred extent so a SplitView/StackView gives it a usable
        // region.  `build.js` overrides these with the Python-serialized values
        // (which may be `null` to disable them).
        this.minWidth = { value: 240, unit: 'px' };
        this.minHeight = { value: 160, unit: 'px' };
        this.preferredWidth = { value: 480, unit: 'px' };
        this.preferredHeight = { value: 320, unit: 'px' };

        // The table is a fixed-size widget that scrolls internally.  Pin an
        // explicit width/height + clip so an auto-sized parent (GroupView /
        // overlay) shrink-to-fits to this size instead of growing with the
        // grid's content (which otherwise inflates on column zoom).  A SplitView
        // overrides these inline sizes with its splitter sizes.
        this.el.style.width = '480px';
        this.el.style.height = '320px';
        // Cap the pinned width at the parent so a narrower flow container
        // (scrollable GroupView / StackView pane) shrinks the table instead of
        // scrolling the whole widget (title bar included) horizontally.  The
        // grid then becomes the horizontal scroll region.  In an auto-sized
        // parent the percentage resolves against an indefinite width and is
        // ignored, so the 480px natural size is preserved.
        this.el.style.maxWidth = '100%';
        this.el.style.overflow = 'hidden';
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
            allow_delete_rows: this.allow_delete_rows,
            show_column_titles: this.show_column_titles,
            show_row_numbers: this.show_row_numbers,
            allow_delete_columns: this.allow_delete_columns,
            sortable: this.sortable,
            column_types: this.column_types,
            column_widths: this.column_widths,
            row_height: this.row_height,
            sort: this.sort,
            onResize: (w, h) => {
                this.preferredWidth = { value: w, unit: 'px' };
                this.preferredHeight = { value: h, unit: 'px' };
                this.el.style.width = w + 'px';
                this.el.style.height = h + 'px';
                // A fixed-size widget: use the inline sizes as the flex basis.
                this.el.style.flex = 'none';
            },
        });
    }
}
