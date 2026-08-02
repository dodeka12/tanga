# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""JS generators and constants for animated exports: playback engine, controls."""

from __future__ import annotations

# ── Shared JS snippet constants ────────────────────────────────────

_GET_ANIM_DATA_JS = """function _getAnimData() {
    return window.__TANGA_ANIMATION__ || { initial_state: [], frames: [], frame_count: 0 };
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
            // Reset to start
            currentFrame = -1;
            for (let i = 0; i < frames.length; i++) {
                for (const ent of (frames[i] || [])) {
                    // We can't easily reset to initial, so just restart from 0
                }
            }
        }
        isPlaying = true;
        startTime = performance.now() - (Math.max(0, currentFrame) / fps * 1000);
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

function _onScrub(val) {
    const targetFrame = parseInt(val, 10);
    // Walk from frame 0 to target
    const direction = targetFrame > currentFrame ? 1 : -1;
    let f = currentFrame;
    while (f !== targetFrame) {
        f += direction;
        if (f >= 0 && f < frames.length) {
            for (const ent of (frames[f] || [])) {
                applyFrameUpdate(ent, figMeshMap);
            }
        }
    }
    currentFrame = targetFrame;
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


def js_animated_label_function(label_map_var: str = "") -> str:
    """Generate the ``_createLabel()`` JS function for animated adapters.

    Args:
        label_map_var: If non-empty (e.g. ``"labelObjects"``), the function
            stores created label objects in a Map under this variable name.

    Returns:
        JS code string defining the ``_createLabel`` function.
    """
    map_set = f"    {label_map_var}.set(lbl.id, labelObj);" if label_map_var else ""

    return f"""function _createLabel(lbl) {{
    if (!lbl.text) return;
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
        catch(e) {{ /* ignore */ }}
    }}
    const container = document.createElement('div');
    container.appendChild(div);
    const labelObj = new CSS2DObject(container);
    if (lbl.parentId && figMeshMap.has(lbl.parentId)) {{
        const pos = lbl.position || [0, 0, 0];
        labelObj.position.set(pos[0], pos[1], pos[2]);
        const parentMesh = figMeshMap.get(lbl.parentId);
        parentMesh.add(labelObj);
        parentMesh.userData._labels = parentMesh.userData._labels || [];
        parentMesh.userData._labels.push(lbl.id);
    }} else {{
        const pos = lbl.position || [0, 0, 0];
        labelObj.position.set(pos[0], pos[1], pos[2]);
        figScene.add(labelObj);
    }}
{map_set}}}"""


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
        JS code string extracting ``animData``, ``fps``, ``frames``, ``initial``,
        and ``figMeshMap``.
    """
    return f"""const animData = _getAnimData();
const fps = animData.fps || {fps};
const frames = animData.frames || [];
const initial = animData.initial_state || [];
const figMeshMap = new Map();{extra_map_vars}"""


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
    """Generate the animated playback engine and render loop.

    Moved from ``_animated_figure.py._animated_playback_engine()``.
    Replaces the old unused ``js_animation_playback()`` in ``_bootstrap_core.py``.

    Args:
        fps: Playback frame rate.
        loop_js_bool: JS boolean literal for looping (e.g. ``"true"`` or
            ``"animData.loop"``).
        scene_var: JS variable name for the scene (``"figScene"``).
        label_objects_map_var: JS variable name for the label objects Map
            (``"labelObjects"`` for full-page, ``"figScene"`` for figure).

    Returns:
        JS code string with ``applyFrameUpdate`` and ``_figAnimate``.
    """
    return f"""// ── Playback engine ──────────────────────────────────────────
function applyFrameUpdate(ent, meshMap) {{
    const mesh = meshMap.get(ent.id);
    if (!mesh) return;

    if (ent.position) mesh.position.set(ent.position[0], ent.position[1], ent.position[2]);
    if (ent.center) mesh.position.set(ent.center[0], ent.center[1], ent.center[2]);
    if (ent.vector || ent.direction) {{
        const vec = ent.vector || ent.direction;
        const origin = ent.origin || [0, 0, 0];
        mesh.position.set(origin[0], origin[1], origin[2]);
        const dir = new THREE.Vector3(vec[0], vec[1], vec[2]).normalize();
        const quat = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
        mesh.setRotationFromQuaternion(quat);
    }}

    if (ent.opacity !== undefined) {{
        mesh.traverse(child => {{
            if (child.material && child.material.opacity !== undefined && !child.material.wireframe) {{
                child.material.opacity = ent.opacity;
                child.material.transparent = ent.opacity < 1.0;
                child.material.depthWrite = ent.opacity >= 0.99;
                child.material.needsUpdate = true;
            }}
        }});
    }}

    if (ent.color) {{
        const c = new THREE.Color(ent.color);
        mesh.traverse(child => {{
            if (child.material && child.material.color && !child.material.wireframe)
                child.material.color.copy(c);
        }});
    }}

    if (ent.scale) mesh.scale.set(ent.scale[0], ent.scale[1], ent.scale[2]);

    // Full rebuild for structural changes
    const prevData = mesh.userData._data || {{}};
    if (ent.radius !== undefined && ent.radius !== prevData.radius ||
        ent.extent !== undefined && ent.extent !== prevData.extent ||
        ent.kind !== undefined && ent.kind !== prevData.kind) {{
        const oldLabels = mesh.userData._labels || [];
        removeEntityMesh(mesh);
        meshMap.delete(ent.id);
        const merged = {{ ...prevData, ...ent }};
        merged.id = ent.id;
        const rebuilt = createEntityMesh(merged);
        if (rebuilt) {{
            {scene_var}.add(rebuilt);
            meshMap.set(ent.id, rebuilt);
            rebuilt.userData._data = merged;
            rebuilt.userData._labels = [];
            for (const lblId of oldLabels) {{
                const lbl = {label_objects_map_var}.get(lblId);
                if (lbl) {{
                    rebuilt.add(lbl);
                    rebuilt.userData._labels.push(lblId);
                }}
            }}
        }}
        return;
    }}
    mesh.userData._data = {{ ...prevData, ...ent }};
}}

// ── Render loop ──────────────────────────────────────────────
let _lastTimestamp = 0;
function _figAnimate(timestamp) {{
    requestAnimationFrame(_figAnimate);
    const dt = (_lastTimestamp ? timestamp - _lastTimestamp : 16) / 1000;
    _lastTimestamp = timestamp;

    if (isPlaying && frames.length > 0) {{
        const elapsed = (timestamp - startTime) / 1000;
        let effectiveTime = elapsed;
        if (animData.loop || {loop_js_bool}) {{
            effectiveTime = elapsed % totalDuration;
        }}
        const targetFrame = Math.floor(effectiveTime * {fps});
        if (targetFrame !== currentFrame && targetFrame >= 0 && targetFrame < frames.length) {{
            // Walk forward through frames
            const step = targetFrame > currentFrame ? 1 : -1;
            let f = currentFrame;
            while (f !== targetFrame) {{
                f += step;
                if (f >= 0 && f < frames.length) {{
                    for (const ent of (frames[f] || [])) {{
                        applyFrameUpdate(ent, figMeshMap);
                    }}
                }}
            }}
        }}
        currentFrame = targetFrame;
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
