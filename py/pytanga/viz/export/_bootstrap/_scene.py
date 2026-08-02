# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""JS generators for scene setup: camera, renderers, controls, lighting, loop."""

from __future__ import annotations

from pytanga.viz.export._bootstrap._utils import _format_js_bool


def js_imports() -> str:
    """Three.js addon imports for the ``<script type="module">`` block."""
    return """import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';"""


def js_scene_setup(
    *,
    bg_color: str,
    container_expr: str,
    append_to: str,
    renderer_var: str,
    label_renderer_var: str,
    camera_var: str,
    controls_var: str,
    scene_var: str,
    width_expr: str,
    height_expr: str,
    cam_fov: float = 50,
    cam_pos: tuple[float, float, float] = (8, 6, 10),
    cam_target: tuple[float, float, float] = (0, 0, 0),
    cam_near: float = 0.1,
    cam_far: float = 1000,
    auto_rotate: bool = False,
    show_grid: bool = True,
    show_axes: bool = True,
    space_extent: float = 10,
    pixel_ratio_expr: str = "window.devicePixelRatio",
    explicit_mouse_buttons: bool = False,
) -> str:
    """Generate JS for scene, camera, renderers, controls, lighting, grid, axes.

    When *bg_color* is ``"transparent"``, the ``WebGLRenderer`` is created with
    ``alpha: true`` and ``setClearColor(0, 0)``, and the scene background is set
    to ``null`` (not ``new THREE.Color('transparent')`` which silently falls
    back to black).

    Args:
        bg_color: CSS color for scene background.  When ``"transparent"``,
            the renderer uses ``alpha: true`` and a fully transparent clear
            colour so the figure blends into its parent container.
        container_expr: JS expression for the container DOM element.
        append_to: JS expression for where to append renderer DOM elements.
        renderer_var: JS variable name for ``WebGLRenderer``.
        label_renderer_var: JS variable name for ``CSS2DRenderer``.
        camera_var: JS variable name for ``PerspectiveCamera``.
        controls_var: JS variable name for ``OrbitControls``.
        scene_var: JS variable name for ``Scene``.
        width_expr: JS expression for renderer width.
        height_expr: JS expression for renderer height.
        cam_fov: Camera field-of-view.
        cam_pos: Initial camera position.
        cam_target: OrbitControls target.
        cam_near: Camera near plane.
        cam_far: Camera far plane.
        auto_rotate: Whether OrbitControls auto-rotate.
        show_grid: Whether to add a ``GridHelper``.
        show_axes: Whether to add an ``AxesHelper``.
        space_extent: Extent for grid/axes sizing.
        pixel_ratio_expr: JS expression for device pixel ratio.
        explicit_mouse_buttons: If True, set LEFT/MIDDLE/RIGHT mouse buttons.

    Returns:
        JS code string.
    """
    mouse_buttons_block = ""
    if explicit_mouse_buttons:
        mouse_buttons_block = f"""{controls_var}.mouseButtons = {{
    LEFT: THREE.MOUSE.ROTATE,
    MIDDLE: THREE.MOUSE.DOLLY,
    RIGHT: THREE.MOUSE.PAN,
}};
"""

    grid_block = ""
    if show_grid:
        grid_block = f"""const gs = {space_extent * 2};
{scene_var}.add(new THREE.GridHelper(gs, Math.max(gs, 20), 0x444466, 0x222244));"""

    axes_block = ""
    if show_axes:
        axes_block = f"{scene_var}.add(new THREE.AxesHelper({space_extent}));"

    if bg_color == "transparent":
        scene_bg = f"{scene_var}.background = null;"
        renderer_opts = "{ antialias: true, alpha: true }"
        clear_color = f"\n{renderer_var}.setClearColor(0x000000, 0);"
    else:
        scene_bg = f"{scene_var}.background = new THREE.Color('{bg_color}');"
        renderer_opts = "{ antialias: true }"
        clear_color = ""

    return f"""// Scene
const {scene_var} = new THREE.Scene();
{scene_bg}

const {camera_var} = new THREE.PerspectiveCamera(
    {cam_fov}, {width_expr} / {height_expr}, {cam_near}, {cam_far}
);
{camera_var}.position.set({cam_pos[0]}, {cam_pos[1]}, {cam_pos[2]});

const {renderer_var} = new THREE.WebGLRenderer({renderer_opts});{clear_color}
{renderer_var}.setPixelRatio({pixel_ratio_expr});
{renderer_var}.setSize({width_expr}, {height_expr});
{renderer_var}.domElement.style.display = 'block';
{append_to}.appendChild({renderer_var}.domElement);

const {label_renderer_var} = new CSS2DRenderer();
{label_renderer_var}.setSize({width_expr}, {height_expr});
{label_renderer_var}.domElement.style.position = 'absolute';
{label_renderer_var}.domElement.style.top = '0px';
{label_renderer_var}.domElement.style.left = '0px';
{label_renderer_var}.domElement.style.pointerEvents = 'none';
{append_to}.appendChild({label_renderer_var}.domElement);

const {controls_var} = new OrbitControls({camera_var}, {renderer_var}.domElement);
{mouse_buttons_block}{controls_var}.enableDamping = true;
{controls_var}.dampingFactor = 0.08;
{controls_var}.screenSpacePanning = true;
{controls_var}.target.set({cam_target[0]}, {cam_target[1]}, {cam_target[2]});
{controls_var}.autoRotate = {_format_js_bool(auto_rotate)};
{controls_var}.update();

// Toggle auto-rotate with 'r' key
window.addEventListener('keydown', (e) => {{
    if (e.key === 'r' || e.key === 'R') {{
        {controls_var}.autoRotate = !{controls_var}.autoRotate;
    }}
}});

// Lighting
{scene_var}.add(new THREE.AmbientLight(0xffffff, 0.5));
const _d1 = new THREE.DirectionalLight(0xffffff, 0.8);
_d1.position.set(10, 20, 10);
{scene_var}.add(_d1);
const _d2 = new THREE.DirectionalLight(0xffffff, 0.3);
_d2.position.set(-5, -2, -8);
{scene_var}.add(_d2);

// Grid & axes
{grid_block}
{axes_block}"""


def js_render_loop(
    *,
    renderer_var: str,
    label_renderer_var: str,
    scene_var: str,
    camera_var: str,
    controls_var: str,
    extra_per_frame: str = "",
) -> str:
    """Generate JS for the ``requestAnimationFrame`` render loop."""
    return f"""// Render loop
function _figAnimate() {{
    requestAnimationFrame(_figAnimate);
    {extra_per_frame}    {controls_var}.update();
    {renderer_var}.render({scene_var}, {camera_var});
    {label_renderer_var}.render({scene_var}, {camera_var});
}}
_figAnimate();"""


def js_resize_handler(
    *,
    renderer_var: str,
    label_renderer_var: str,
    camera_var: str,
    width_expr: str,
    height_expr: str,
    conditional: bool = False,
    container_expr: str = "",
) -> str:
    """Generate JS for window resize handler."""
    if conditional:
        if not container_expr:
            return ""
        else:
            return f"""// Resize handler
window.addEventListener('resize', () => {{
    const rw = {container_expr}.clientWidth || window.innerWidth;
    const rh = {container_expr}.clientHeight || window.innerHeight;
    {camera_var}.aspect = rw / rh;
    {camera_var}.updateProjectionMatrix();
    {renderer_var}.setSize(rw, rh);
    {label_renderer_var}.setSize(rw, rh);
}});"""

    return f"""// Resize handler
window.addEventListener('resize', () => {{
    {camera_var}.aspect = {width_expr} / {height_expr};
    {camera_var}.updateProjectionMatrix();
    {renderer_var}.setSize({width_expr}, {height_expr});
    {label_renderer_var}.setSize({width_expr}, {height_expr});
}});"""


def js_autofit_camera(
    *,
    mesh_map_var: str,
    camera_var: str,
    controls_var: str,
    cam_explicit: bool,
) -> str:
    """Generate JS for auto-fit camera from entity bounding box."""
    if cam_explicit:
        return ""

    return f"""// Auto-fit camera from entity bounds
if ({mesh_map_var}.size > 0) {{
    const box = new THREE.Box3();
    {mesh_map_var}.forEach(m => box.expandByObject(m));
    if (!box.isEmpty()) {{
        const center = new THREE.Vector3();
        box.getCenter(center);
        const sz = new THREE.Vector3();
        box.getSize(sz);
        const maxDim = Math.max(sz.x, sz.y, sz.z, 1);
        const distance = maxDim * 1.5 + 2;
        {controls_var}.target.copy(center);
        {camera_var}.position.set(
            center.x + distance * 0.6,
            center.y + distance * 0.5,
            center.z + distance * 0.7
        );
        {camera_var}.lookAt({controls_var}.target);
        {camera_var}.updateProjectionMatrix();
        {controls_var}.update();
    }}
}}"""
