// Tanga Viewer — Layout tree materialization.
// Maps the serialized `view_layout` node tree to `View` instances and collects
// the scene→view routing map used by the bootstrap to dispatch messages.

import { View } from './view.js';
import { SplitView } from './split-view.js';
import { StackView } from './stack-view.js';
import { GroupView } from './group-view.js';
import { MenuView } from './menu-view.js';
import { ThreeJsView } from './three-view.js';
import { SliderView } from './slider-view.js';
import { ButtonView } from './button-view.js';
import { DropdownView } from './dropdown-view.js';
import { FileChooserView } from './file-chooser-view.js';
import { TextFieldView } from './text-field-view.js';
import { TextAreaView } from './text-area-view.js';
import { ColorPickerView } from './color-picker-view.js';
import { CheckboxView } from './checkbox-view.js';
import { ValueEditView } from './value-edit-view.js';
import { TableView } from './table-view.js';
import { SpacerView } from './spacer-view.js';

function applySizeSpecs(view, node) {
    // Assign unconditionally so a `null` from Python clears any JS default
    // (e.g. the ControlView min floors set at construction time).
    view.minWidth = node.min_width ?? null;
    view.maxWidth = node.max_width ?? null;
    view.minHeight = node.min_height ?? null;
    view.maxHeight = node.max_height ?? null;
    view.preferredWidth = node.preferred_width ?? null;
    view.preferredHeight = node.preferred_height ?? null;
}

/** Build a `View` tree from a serialized `view_layout` node. */
export function buildViewTree(node, ws) {
    if (!node) return new View();

    if (node.type === 'split') {
        const split = new SplitView({ orientation: node.orientation, movable: node.movable });
        applySizeSpecs(split, node);
        const children = node.children || [];
        const sizes = node.sizes || [];
        children.forEach((childNode, i) => {
            const child = buildViewTree(childNode, ws);
            // Initial splitter positions (`sizes`) → the child's preferred size
            // along the split axis.
            const sizeSpec = sizes[i] || null;
            if (sizeSpec) {
                if (node.orientation === 'horizontal') child.preferredWidth = sizeSpec;
                else child.preferredHeight = sizeSpec;
            }
            split.addChild(child);
        });
        return split;
    }

    if (node.type === 'stack') {
        const stack = new StackView({
            direction: node.direction,
            scrollable: node.scrollable,
            gap: node.gap,
            align: node.align,
            justify: node.justify,
        });
        applySizeSpecs(stack, node);
        for (const childNode of node.children || []) {
            stack.addChild(buildViewTree(childNode, ws));
        }
        return stack;
    }

    if (node.type === 'group') {
        const group = new GroupView({
            title: node.title,
            direction: node.direction,
            position: node.position,
            collapsed: node.collapsed,
            scrollable: node.scrollable,
            gap: node.gap,
            align: node.align,
            justify: node.justify,
            icon: node.icon,
            icon_only: node.icon_only,
            parent_id: node.parent_id,
            id: node.id,
        });
        applySizeSpecs(group, node);
        for (const childNode of node.children || []) {
            group.addChild(buildViewTree(childNode, ws));
        }
        return group;
    }

    if (node.type === 'menu') {
        const menu = new MenuView({
            trigger_icon: node.trigger_icon,
            label: node.label,
            mode: node.mode,
            direction: node.direction,
            position: node.position,
        });
        applySizeSpecs(menu, node);
        for (const childNode of node.children || []) {
            menu.addChild(buildViewTree(childNode, ws));
        }
        return menu;
    }

    if (node.type === 'scene_view') {
        const view = new ThreeJsView(node.scene, ws, node.camera || null, node.id || null);
        applySizeSpecs(view, node);
        for (const childNode of node.children || []) {
            view.addOverlay(buildViewTree(childNode, ws));
        }
        return view;
    }

    let view;
    if (node.type === 'slider_view') {
        view = new SliderView({
            id: node.id, label: node.label, tooltip: node.tooltip,
            min: node.min, max: node.max, step: node.step, value: node.value,
            variant: node.variant,
        });
    } else if (node.type === 'button_view') {
        view = new ButtonView({
            id: node.id, label: node.label, tooltip: node.tooltip,
            icon: node.icon, icon_only: node.icon_only,
            variant: node.variant,
        });
    } else if (node.type === 'dropdown_view') {
        view = new DropdownView({
            id: node.id, label: node.label, tooltip: node.tooltip,
            options: node.options, value: node.value,
        });
    } else if (node.type === 'file_chooser_view') {
        view = new FileChooserView({
            id: node.id, value: node.value, root: node.root, accept: node.accept,
        });
    } else if (node.type === 'text_field_view') {
        view = new TextFieldView({
            id: node.id, label: node.label, tooltip: node.tooltip,
            value: node.value, placeholder: node.placeholder,
        });
    } else if (node.type === 'text_area_view') {
        view = new TextAreaView({
            id: node.id, label: node.label, tooltip: node.tooltip,
            value: node.value, placeholder: node.placeholder, rows: node.rows,
        });
    } else if (node.type === 'color_picker_view') {
        view = new ColorPickerView({
            id: node.id, label: node.label, tooltip: node.tooltip,
            value: node.value,
        });
    } else if (node.type === 'checkbox_view') {
        view = new CheckboxView({
            id: node.id, label: node.label, tooltip: node.tooltip,
            value: node.value, variant: node.variant,
        });
    } else if (node.type === 'value_edit_view') {
        view = new ValueEditView({
            id: node.id, label: node.label, tooltip: node.tooltip,
            min: node.min, max: node.max, step: node.step,
            digits: node.digits, value: node.value, editable: node.editable,
        });
    } else if (node.type === 'table_view') {
        view = new TableView({
            id: node.id, label: node.label, tooltip: node.tooltip,
            columns: node.columns, rows: node.rows,
            allow_add_rows: node.allow_add_rows, allow_add_columns: node.allow_add_columns,
        });
    } else if (node.type === 'spacer') {
        view = new SpacerView();
    } else {
        view = new View();
    }
    applySizeSpecs(view, node);
    return view;
}

/** Walk a built tree and return scene → {sceneViews} (only scenes are routed). */
export function collectSceneRoutes(root) {
    const routes = new Map();

    const visit = (view) => {
        if (view instanceof ThreeJsView) {
            const scene = view.sceneName ?? '';
            const r = routes.get(scene) || { sceneViews: [] };
            r.sceneViews.push(view);
            routes.set(scene, r);
        }
        if (view.children) {
            for (const child of view.children) visit(child);
        }
    };

    visit(root);
    return routes;
}

/** Walk a built tree and return `view_id` → `ThreeJsView` (per-pane routing). */
export function collectViewByIds(root) {
    const byId = new Map();

    const visit = (view) => {
        if (view instanceof ThreeJsView && view.viewId) {
            byId.set(view.viewId, view);
        }
        if (view.children) {
            for (const child of view.children) visit(child);
        }
    };

    visit(root);
    return byId;
}

