// Tanga Viewer — runtime state carried by a serialized `view_layout` node.
//
// Kept free of view imports so the layout builder and the unit tests can share
// it (`build.js` pulls in Three.js via `three-view.js`).

/**
 * Apply a node's serialized visibility to its view.
 *
 * Visibility is a property of **every** view node, not just of controls: a
 * `visible: false` group, stack, toolbar or params pane collapses exactly like
 * a hidden control (`View.setHidden` removes it from flow and from the size
 * maths).  A node without a `visible` field means "visible" — which also shows
 * a reused view that an earlier push hid.
 */
export function applyNodeVisibility(view, node) {
    if (!view || typeof view.setHidden !== 'function') return;
    view.setHidden(node.visible === false);
}
