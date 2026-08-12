# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""JS generators for entity mesh creation and label CSS2D object creation."""

from __future__ import annotations


def js_entity_creation(
    *,
    entities_expr: str,
    mesh_map_var: str,
    scene_var: str,
    layer_dispatch: bool = True,
) -> str:
    """Generate JS for entity mesh creation loop.

    Args:
        entities_expr: JS expression yielding the entities array.
        mesh_map_var: JS variable name for the mesh map.
        scene_var: JS variable name for the scene.
        layer_dispatch: If True, use ``ent.layer`` dispatch (animated path
            separates scene/overlay layers).  If False, use simple
            ``createEntityMesh`` without layer dispatch (static path).

    Returns:
        JS code string.
    """
    if layer_dispatch:
        return f"""// ── Entity creation (initial_state) ──
(async () => {{
    for (const ent of {entities_expr}) {{
        if (ent.layer === 'scene') {{
            const mesh = await createEntityMesh(ent);
            if (mesh) {{
                {scene_var}.add(mesh);
                {mesh_map_var}.set(ent.id, mesh);
                mesh.userData._data = ent;
            }}
        }} else if (ent.layer === 'overlay' && ent.kind === 'label') {{
            _createLabel(ent);
        }}
    }}
}})();"""

    return f"""// Entities
const {mesh_map_var} = new Map();
(async () => {{
    for (const ent of {entities_expr}) {{
        const mesh = await createEntityMesh(ent);
        if (mesh) {{
            {scene_var}.add(mesh);
            {mesh_map_var}.set(ent.id, mesh);
        }}
    }}
}})();"""


def js_label_creation(
    *,
    labels_expr: str,
    mesh_map_var: str,
    scene_var: str,
    use_label_objects_map: bool = False,
    label_objects_map_var: str = "labelObjects",
) -> str:
    """Generate JS for label ``CSS2DObject`` creation (animated path).

    When ``use_label_objects_map`` is True, labels are stored in a ``Map``
    so the rebuild path can re-attach them.

    Args:
        labels_expr: JS expression yielding the labels array.
        mesh_map_var: JS variable name for the mesh map.
        scene_var: JS variable name for the scene.
        use_label_objects_map: If True, store labels in ``labelObjects`` Map.
        label_objects_map_var: JS variable name for the label objects Map.

    Returns:
        JS code string.
    """
    label_map_set = (
        f"    {label_objects_map_var}.set(lbl.id, labelObj);"
        if use_label_objects_map
        else ""
    )

    return f"""// Labels (CSS2D objects)
for (const lbl of {labels_expr}) {{
    if (!lbl.text) continue;
    const div = document.createElement('div');
    div.textContent = lbl.text;
    const s = lbl.style || {{}};
    div.style.fontFamily = s.font_family || 'sans-serif';
    div.style.fontSize = (s.font_size || 14) + 'px';
    div.style.color = s.color || '#ffffff';
    div.style.backgroundColor = s.background || 'rgba(0, 0, 0, 0.6)';
    div.style.padding = '2px 6px';
    div.style.borderRadius = '3px';
    div.style.userSelect = 'none';
    div.style.whiteSpace = 'nowrap';
    if (typeof renderMathInElement !== 'undefined') {{
        try {{ renderMathInElement(div, {{ delimiters: [
            {{ left: '$$', right: '$$', display: true }},
            {{ left: '$', right: '$', display: false }} ], throwOnError: false }}); }}
        catch (e) {{ /* ignore */ }}
    }}
    const container = document.createElement('div');
    container.appendChild(div);
    const labelObj = new CSS2DObject(container);
    if (lbl.parentId && {mesh_map_var}.has(lbl.parentId)) {{
        const pos = lbl.position || [0, 0, 0];
        labelObj.position.set(pos[0], pos[1], pos[2]);
        const parentMesh = {mesh_map_var}.get(lbl.parentId);
        parentMesh.add(labelObj);
        parentMesh.userData._labels = parentMesh.userData._labels || [];
        parentMesh.userData._labels.push(lbl.id);
    }} else {{
        const pos = lbl.position || [0, 0, 0];
        labelObj.position.set(pos[0], pos[1], pos[2]);
        {scene_var}.add(labelObj);
    }}
{label_map_set}}}"""


def js_label_creation_static(
    *,
    labels_expr: str,
    mesh_map_var: str,
    scene_var: str,
) -> str:
    """Generate JS for static (non-animated) label ``CSS2DObject`` creation.

    The static path differs from the animated path in two ways:
    1. Child labels use ``{{offset2d}}`` + alignment transform on the inner
       ``div`` (and wrap in a container div).
    2. There is no label objects Map.

    Args:
        labels_expr: JS expression yielding labels array.
        mesh_map_var: JS variable name for the mesh map.
        scene_var: JS variable name for the scene.

    Returns:
        JS code string.
    """
    return f"""// Labels (CSS2D objects)
for (const lbl of {labels_expr}) {{
    if (!lbl.text) continue;
    const div = document.createElement('div');
    div.textContent = lbl.text;
    const s = lbl.style || {{}};
    div.style.fontFamily = s.font_family || 'sans-serif';
    div.style.fontSize = (s.font_size || 14) + 'px';
    div.style.color = s.color || '#ffffff';
    div.style.backgroundColor = s.background || 'rgba(0, 0, 0, 0.6)';
    div.style.padding = '2px 6px';
    div.style.borderRadius = '3px';
    div.style.userSelect = 'none';
    div.style.whiteSpace = 'nowrap';
    // KaTeX math rendering in labels
    if (typeof renderMathInElement !== 'undefined') {{
        try {{
            renderMathInElement(div, {{
                delimiters: [
                    {{ left: '$$', right: '$$', display: true }},
                    {{ left: '$', right: '$', display: false }},
                ],
                throwOnError: false,
            }});
        }} catch (e) {{ /* ignore */ }}
    }}
    const container = document.createElement('div');
    container.appendChild(div);
    const labelObj = new CSS2DObject(container);
    if (lbl.parentId && {mesh_map_var}.has(lbl.parentId)) {{
        // Label is child of parent mesh — position is relative to parent.
        // The position from Python is already the parent-relative anchor.
        const pos = lbl.position || [0, 0, 0];
        labelObj.position.set(pos[0], pos[1], pos[2]);
        // CSS2DRenderer centers the container via translate(-50%,-50%).
        // Counter that centering on the inner div + apply pixel offset:
        const off2d = s.offset_2d || [0, 0];
        const align = s.align || [0.5, 0.5];
        const tx = (0.5 - align[0]) * 100;
        const ty = (0.5 - align[1]) * 100;
        div.style.transform = `translate(${{off2d[0]}}px, ${{off2d[1]}}px) translate(${{tx}}%, ${{ty}}%)`;
        {mesh_map_var}.get(lbl.parentId).add(labelObj);
    }} else {{
        // Standalone label — use absolute position.
        const pos = lbl.position || [0, 0, 0];
        labelObj.position.set(pos[0], pos[1], pos[2]);
        {scene_var}.add(labelObj);
    }}
}}"""
