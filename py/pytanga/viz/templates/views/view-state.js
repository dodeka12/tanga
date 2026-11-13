// Tanga Viewer — live view-state registry + `control_state` dispatch.
//
// A server-driven `control_state {visible, collapsed, enabled, title, tooltip,
// row}` addresses a **view**, not a control widget: visibility and collapse are
// view-level layout state (see docs/dev/architecture/viz-controls-and-
// interactions.md).  Every view built by `build.js` registers here under its
// node id, independent of the layout reconciliation registry, which only exists
// to plan reuse — a subtree built without a registry (e.g. a dialog's content)
// must still be reachable by id.

const _statefulViews = new Map(); // view id → View

/** Register a built view so `control_state` messages can reach it by id. */
export function registerStatefulView(view) {
    const id = view && view.viewId;
    if (!id) return view;
    _statefulViews.set(id, view);
    return view;
}

/** Drop a view's entry (no-op when a newer view has taken the id over). */
export function unregisterStatefulView(view) {
    const id = view && view.viewId;
    if (!id) return;
    if (_statefulViews.get(id) === view) _statefulViews.delete(id);
}

/** Drop a whole built subtree — e.g. a transient dialog's content going away. */
export function unregisterStatefulTree(view) {
    if (!view) return;
    unregisterStatefulView(view);
    for (const child of view.children || []) unregisterStatefulTree(child);
    // Overlay children live in their own list (`ThreeJsView._overlays`), not in
    // `children`; walk them too so scene overlays cannot leak entries.
    for (const child of view._overlays || []) unregisterStatefulTree(child);
}

/** The live view registered under `id`, or `undefined`. */
export function getStatefulView(id) {
    if (id === null || id === undefined) return undefined;
    return _statefulViews.get(id);
}

/**
 * Apply the view-level fields of a `control_state` message to `view`.
 *
 * One implementation for every view type: a control, a group, a stack, a
 * toolbar or a params pane all react through the same methods, so hiding a
 * group from Python collapses the whole pane (title included) instead of
 * relying on the widget DOM.  Fields the view does not implement are skipped
 * (e.g. `setCollapsed` only exists on groups/menus).
 *
 * @returns {boolean} whether at least one field reached the view.
 */
export function applyViewState(view, msg) {
    if (!view || !msg) return false;
    let handled = false;
    if (msg.visible !== undefined && typeof view.setHidden === 'function') {
        view.setHidden(!msg.visible);
        handled = true;
    }
    if (msg.collapsed !== undefined && typeof view.setCollapsed === 'function') {
        view.setCollapsed(!!msg.collapsed);
        handled = true;
    }
    if (msg.enabled !== undefined && typeof view.setEnabled === 'function') {
        view.setEnabled(!!msg.enabled);
        handled = true;
    }
    if (msg.tooltip !== undefined && typeof view.setTooltip === 'function') {
        view.setTooltip(msg.tooltip);
        handled = true;
    }
    if (msg.row !== undefined && msg.title !== undefined) {
        if (typeof view.setRowTitle === 'function') {
            view.setRowTitle(msg.row, msg.title);
            handled = true;
        }
    } else if (msg.title !== undefined && typeof view.setTitle === 'function') {
        view.setTitle(msg.title);
        handled = true;
    }
    return handled;
}

/** Test hook: forget every registered view. */
export function clearStatefulViews() {
    _statefulViews.clear();
}
