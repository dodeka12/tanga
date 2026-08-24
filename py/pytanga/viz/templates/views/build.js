// Tanga Viewer — Layout tree materialization.
// Maps the serialized `view_layout` node tree to `View` instances and collects
// the scene→view routing map used by the bootstrap to dispatch messages.

import { View } from './view.js';
import { SplitView } from './split-view.js';
import { StackView } from './stack-view.js';
import { GroupView } from './group-view.js';
import { ThreeJsView } from './three-view.js';
import { SliderView } from './slider-view.js';
import { ButtonView } from './button-view.js';
import { DropdownView } from './dropdown-view.js';
import { SpacerView } from './spacer-view.js';

function applySizeSpecs(view, node) {
    if (node.min_width) view.minWidth = node.min_width;
    if (node.max_width) view.maxWidth = node.max_width;
    if (node.min_height) view.minHeight = node.min_height;
    if (node.max_height) view.maxHeight = node.max_height;
    if (node.preferred_width) view.preferredWidth = node.preferred_width;
    if (node.preferred_height) view.preferredHeight = node.preferred_height;
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
        const stack = new StackView({ direction: node.direction });
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
        });
        applySizeSpecs(group, node);
        for (const childNode of node.children || []) {
            group.addChild(buildViewTree(childNode, ws));
        }
        return group;
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
            id: node.id, label: node.label,
            min: node.min, max: node.max, step: node.step, default: node.default,
        });
    } else if (node.type === 'button_view') {
        view = new ButtonView({ id: node.id, label: node.label });
    } else if (node.type === 'dropdown_view') {
        view = new DropdownView({
            id: node.id, label: node.label, options: node.options, default: node.default,
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

