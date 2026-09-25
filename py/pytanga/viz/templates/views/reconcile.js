// Tanga Viewer — pure layout reconciliation core (no DOM/three imports).
// Decides, for a serialized `view_layout` tree, which live views are reused
// (same id and same type), which nodes are new, and which live views are
// orphaned.  Unit-tested with `node --test` (see js/dev/tests/reconcile.test.mjs).

/**
 * Node types whose live view is reused across a `view_layout` re-push.
 * Everything else (containers, `log_view`, `file_chooser_view`, `table_view`,
 * unknown types) is rebuilt each time and its old view orphaned.
 */
export const REUSABLE_TYPES = new Set([
    'scene_view',
    'slider_view',
    'button_view',
    'dropdown_view',
    'text_field_view',
    'label_view',
    'markdown_view',
    'text_area_view',
    'color_picker_view',
    'checkbox_view',
    'value_edit_view',
    'spacer',
    'separator',
]);

/**
 * DFS over `node` and its `children`, returning `[{ id, type }]` in traversal
 * order (mirrors `buildViewTree`'s recursion).
 */
export function collectNodeTypes(node, out = []) {
    if (!node) return out;
    if (node.id != null) out.push({ id: node.id, type: node.type });
    for (const child of node.children || []) collectNodeTypes(child, out);
    return out;
}

/**
 * Given the ordered node descriptors and the live views (`Map<id, typeTag>`),
 * return the reconciliation plan:
 *   - `reuse`:    nodes that keep their live view (reusable type, same id+type)
 *   - `create`:   nodes that need a new view
 *   - `orphaned`: live ids referenced by no reused node
 */
export function planReconciliation(nodes, live, reusableTypes = REUSABLE_TYPES) {
    const reuse = [];
    const create = [];
    const remaining = new Map(live);
    for (const node of nodes) {
        const tag = remaining.get(node.id);
        if (reusableTypes.has(node.type) && tag !== undefined && tag === node.type) {
            reuse.push(node);
            remaining.delete(node.id);
        } else {
            create.push(node);
        }
    }
    return { reuse, create, orphaned: [...remaining.keys()] };
}
