# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""JS generators and constants for animated exports: playback engine, controls."""

from __future__ import annotations

# ── Shared JS snippet constants ────────────────────────────────────

_GET_ANIM_DATA_JS = """function _getAnimData() {
    return window.__TANGA_ANIMATION__ || { frames: [], frame_count: 0 };
}"""

_ANIMATION_DECOMPRESS_JS = r"""<script type="module">
// Decompress gzip-compressed animation data at page load
(async () => {
    const el = document.getElementById('tanga-anim-data');
    if (!el) return;
    const b64 = el.textContent.trim();
    const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    const ds = new DecompressionStream('gzip');
    const writer = ds.writable.getWriter();
    writer.write(bytes);
    writer.close();
    const reader = ds.readable.getReader();
    const chunks = [];
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        chunks.push(value);
    }
    const totalLen = chunks.reduce((s, c) => s + c.length, 0);
    const merged = new Uint8Array(totalLen);
    let offset = 0;
    for (const c of chunks) {
        merged.set(c, offset);
        offset += c.length;
    }
    const json = new TextDecoder().decode(merged);
    window.__TANGA_ANIMATION__ = JSON.parse(json);
    el.remove();
})();
</script>
"""

_CONTROLS_HTML = """<div id="tanga-controls" style="
    position:absolute;bottom:8px;left:50%;transform:translateX(-50%);
    display:flex;gap:8px;align-items:center;
    background:rgba(0,0,0,0.7);padding:6px 12px;border-radius:6px;
    z-index:10;pointer-events:auto;color:#ccc;font-family:sans-serif;font-size:12px;">
    <button id="tanga-play-btn" style="
        background:none;border:1px solid #666;color:#ccc;
        border-radius:3px;padding:2px 8px;cursor:pointer;">▶ Play</button>
    <input type="range" id="tanga-scrub" min="0" max="0" value="0"
        style="width:150px;cursor:pointer;">
    <span id="tanga-time">0.0s / 0.0s</span>
    <select id="tanga-speed" style="
        background:#222;color:#ccc;border:1px solid #666;
        border-radius:3px;padding:2px 4px;">
        <option value="0.25">0.25×</option>
        <option value="0.5">0.5×</option>
        <option value="1" selected>1×</option>
        <option value="2">2×</option>
    </select>
    <label style="cursor:pointer;">
        <input type="checkbox" id="tanga-loop" checked> Loop
    </label>
</div>"""

_CONTROLS_JS = """// ── Playback controls ──
let _playSpeed = 1.0;
let _loopEnabled = true;

function _togglePlay() {
    if (isPlaying) {
        isPlaying = false;
    } else {
        if (currentFrame >= frames.length - 1 && !_loopEnabled) {
            // Restart from the first frame when at the end and not looping
            _playFrame(0);
            startTime = performance.now();
        } else {
            startTime = performance.now() - (Math.max(0, currentFrame) / fps * 1000);
        }
        isPlaying = true;
    }
    _updatePlayBtn();
}

function _updatePlayBtn() {
    const btn = document.getElementById('tanga-play-btn');
    if (btn) btn.textContent = isPlaying ? '⏸ Pause' : '▶ Play';
}

function _updateScrubBar() {
    const scrub = document.getElementById('tanga-scrub');
    const timeEl = document.getElementById('tanga-time');
    if (!scrub || !timeEl) return;
    scrub.max = Math.max(0, frames.length - 1);
    scrub.value = Math.max(0, currentFrame);
    const ct = Math.max(0, currentFrame) / fps;
    timeEl.textContent = ct.toFixed(1) + 's / ' + totalDuration.toFixed(1) + 's';
}

async function _onScrub(val) {
    const targetFrame = parseInt(val, 10);
    await _playFrame(targetFrame);
    if (isPlaying) startTime = performance.now() - (targetFrame / fps * 1000);
    _updateScrubBar();
}

function _onSpeed(val) {
    // Speed is handled by adjusting the playback rate
    _playSpeed = parseFloat(val);
}

function _onLoop(checked) {
    _loopEnabled = checked;
    animData.loop = checked;
}

// Override the playback loop to respect speed
const _origFigAnimate = _figAnimate;
_figAnimate = function(timestamp) {
    // Adjust timestamp for speed
    if (isPlaying && _playSpeed !== 1.0) {
        const realElapsed = (timestamp - startTime);
        const adjustedTimestamp = startTime + realElapsed * _playSpeed;
        _origFigAnimate(adjustedTimestamp);
        return;
    }
    _origFigAnimate(timestamp);
};

_updateScrubBar();

// Wire controls via addEventListener (ES modules don't expose globals to inline handlers)
const _playBtn = document.getElementById('tanga-play-btn');
if (_playBtn) _playBtn.addEventListener('click', _togglePlay);
const _scrub = document.getElementById('tanga-scrub');
if (_scrub) _scrub.addEventListener('input', (e) => _onScrub(e.target.value));
const _speed = document.getElementById('tanga-speed');
if (_speed) _speed.addEventListener('change', (e) => _onSpeed(e.target.value));
const _loopChk = document.getElementById('tanga-loop');
if (_loopChk) _loopChk.addEventListener('change', (e) => _onLoop(e.target.checked));"""

# ── JS generator functions ──────────────────────────────────────────


def js_animation_state() -> str:
    """Generate the animation state variable declarations.

    Returns:
        JS code declaring ``isPlaying``, ``currentFrame``, ``startTime``,
        and ``totalDuration``.
    """
    return """// State
let isPlaying = false;
let currentFrame = -1;
let startTime = 0;
let totalDuration = animData.frame_count > 0
    ? animData.frame_count / fps
    : 0;"""


def js_animation_data_init(fps: int, extra_map_vars: str = "") -> str:
    """Generate the animation data initialisation block.

    Args:
        fps: Default frame rate (used as fallback if ``animData.fps`` is absent).
        extra_map_vars: Additional JS to append (e.g. ``"\\nconst labelObjects = new Map();"``).

    Returns:
        JS code string extracting ``animData``, ``fps``, ``frames``,
        and ``figMeshMap``.
    """
    return f"""const animData = _getAnimData();
const fps = animData.fps || {fps};
const frames = animData.frames || [];
const figMeshMap = new Map();{extra_map_vars}"""


def js_reconcile_frame(
    *,
    scene_var: str,
    label_objects_map_var: str = "labelObjects",
    mesh_map_var: str = "figMeshMap",
    registry_var: str = "figRegistry",
) -> str:
    """Generate the id-based frame reconciliation engine.

    Emits ``_reconcileFrame(frame)`` (create-on-first-seen, update-on-seen-again,
    hide-and-cache on absence) and the ``_playFrame(n)`` helper.  Scene objects
    are built through the shared ``buildSceneObject``/``buildOverlay`` so the
    animated export applies node transforms + parenting exactly like the live
    viewer, then updated in place via the bundled ``updateEntityMesh``
    dispatcher.

    Args:
        scene_var: JS variable name for the three.js Scene.
        label_objects_map_var: JS variable name for the label objects Map.
        mesh_map_var: JS variable name for the id -> inner-mesh Map.
        registry_var: JS variable name for the id -> entry registry Map.

    Returns:
        JS code string defining ``_reconcileFrame`` and ``_playFrame``.
    """
    return f"""// ── Frame reconciliation (id-based snapshot diff) ──
async function _reconcileFrame(frame) {{
    const ents = frame || [];
    const targetIds = new Set(ents.map(e => e.id));

    for (const ent of ents) {{
        if (ent.layer === 'overlay') {{
            let entry = {registry_var}.get(ent.id);
            if (!entry) {{
                entry = buildOverlay(ent, {scene_var}, {registry_var});
                if (entry && entry.obj) {label_objects_map_var}.set(ent.id, entry.obj);
            }}
            if (entry) {{
                entry.obj.visible = true;
                if (entry.obj.element) entry.obj.element.style.display = '';
            }}
            continue;
        }}
        if (ent.layer !== 'scene') continue;

        let mesh = {mesh_map_var}.get(ent.id);
        if (!mesh) {{
            const entry = await buildSceneObject(ent, {scene_var}, {registry_var});
            if (entry) {{
                {mesh_map_var}.set(ent.id, entry.mesh);
                entry.mesh.userData._data = ent;
                entry.mesh.visible = true;
            }}
            continue;
        }}

        const prev = mesh.userData._data || {{}};
        if (updateEntityMesh(mesh, ent, prev)) {{
            mesh.userData._data = {{ ...prev, ...ent }};
            mesh.visible = true;
        }} else {{
            const entry = {registry_var}.get(ent.id);
            const oldLabels = entry && entry.obj ? (entry.obj.userData._labels || []) : [];
            removeEntityMesh(entry ? entry.obj : mesh);
            {mesh_map_var}.delete(ent.id);
            {registry_var}.delete(ent.id);
            const merged = {{ ...prev, ...ent }};
            merged.id = ent.id;
            const newEntry = await buildSceneObject(merged, {scene_var}, {registry_var});
            if (newEntry) {{
                {mesh_map_var}.set(ent.id, newEntry.mesh);
                newEntry.mesh.userData._data = merged;
                newEntry.obj.userData._labels = [];
                for (const lblId of oldLabels) {{
                    const lbl = {label_objects_map_var}.get(lblId);
                    if (lbl) {{
                        newEntry.obj.add(lbl);
                        newEntry.obj.userData._labels.push(lblId);
                    }}
                }}
                newEntry.mesh.visible = true;
            }}
        }}
    }}

    for (const [id, mesh] of {mesh_map_var}) {{
        if (!targetIds.has(id)) mesh.visible = false;
    }}
    for (const [id, lbl] of {label_objects_map_var}) {{
        if (!targetIds.has(id)) {{
            lbl.visible = false;
            if (lbl.element) lbl.element.style.display = 'none';
        }}
    }}
}}

async function _playFrame(n) {{
    if (n >= 0 && n < frames.length) {{
        await _reconcileFrame(frames[n]);
        currentFrame = n;
    }}
}}"""


def js_controls_ui(show_controls: bool = True) -> str:
    """Return the playback controls JS, or empty string if hidden.

    Args:
        show_controls: Whether to include the controls.

    Returns:
        JS code string, or empty string.
    """
    if not show_controls:
        return ""
    return _CONTROLS_JS


def js_controls_html(show_controls: bool = True) -> str:
    """Return the playback controls HTML, or empty string if hidden.

    Args:
        show_controls: Whether to include the controls.

    Returns:
        HTML string for the controls div, or empty string.
    """
    return _CONTROLS_HTML if show_controls else ""


def js_animated_render_loop(
    *,
    fps: int,
    loop_js_bool: str,
    scene_var: str,
    label_objects_map_var: str = "labelObjects",
) -> str:
    """Generate the animated render loop.

    The loop computes the target frame from elapsed time (with loop modulo)
    and jumps directly to it via ``_playFrame`` — no frame-by-frame walking.

    Args:
        fps: Playback frame rate.
        loop_js_bool: JS boolean literal for looping (e.g. ``"true"`` or
            ``"animData.loop"``).
        scene_var: JS variable name for the scene (``"figScene"``).
        label_objects_map_var: JS variable name for the label objects Map
            (``"labelObjects"``).  Kept for signature compatibility with the
            previous API; the loop itself delegates to ``_playFrame``.

    Returns:
        JS code string with the ``_figAnimate`` render loop.
    """
    return f"""// ── Render loop ──────────────────────────────────────────
async function _figAnimate(timestamp) {{
    requestAnimationFrame(_figAnimate);

    if (isPlaying && frames.length > 0) {{
        const elapsed = (timestamp - startTime) / 1000;
        let effectiveTime = elapsed;
        if (animData.loop || {loop_js_bool}) {{
            effectiveTime = elapsed % totalDuration;
        }}
        const targetFrame = Math.floor(effectiveTime * {fps});
        if (targetFrame >= 0 && targetFrame < frames.length && targetFrame !== currentFrame) {{
            await _playFrame(targetFrame);
        }}
        if (effectiveTime >= totalDuration && !animData.loop && !{loop_js_bool}) {{
            isPlaying = false;
            _updatePlayBtn();
        }}
        _updateScrubBar();
    }}

    figControls.update();
    figRenderer.render(figScene, figCamera);
    figLabelRenderer.render(figScene, figCamera);
}}
_figAnimate(0);"""


# ── Animation data embedding helpers ────────────────────────────────


def embed_animation_data(json_str: str, *, compress: bool = False) -> str:
    """Return a ``<script>`` tag embedding the animation JSON.

    When *compress* is True, the data is gzip-compressed and base64-encoded.
    """
    if compress:
        import base64
        import gzip

        compressed = base64.b64encode(gzip.compress(json_str.encode("utf-8"))).decode(
            "ascii"
        )
        return (
            '<script type="application/octet-stream" id="tanga-anim-data">\n'
            + compressed
            + "\n</script>\n"
        )

    return "<script>\nwindow.__TANGA_ANIMATION__ = " + json_str + ";\n</script>\n"


def get_anim_decompress_js(compress: bool = False) -> str:
    """Return the decompression bootstrapper if *compress* is True."""
    return _ANIMATION_DECOMPRESS_JS if compress else ""


def get_anim_data_js() -> str:
    """Return the ``_getAnimData()`` helper function."""
    return _GET_ANIM_DATA_JS