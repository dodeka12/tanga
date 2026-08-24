// SDF Viewer — WebGL2 ray-marched viewer entry point.
//
// Renders a single composed signed-distance field via a fullscreen-quad
// raymarcher. It reuses the standard viewer's camera (`view_mode.js`) and
// OrbitControls (`controls.js`) so the default/custom camera matches the
// non-SDF viewer 1:1.
//
// The fragment is assembled by concatenation: common → primitives →
// combinators → material preamble → materialColor → injected `map(p)` →
// raymarch body. `map` and the material table are composed from the live
// object list received over the shared WebSocket (`scene_update` /
// `scene_config` / `sdf_viewer_config`).

import * as THREE from 'three';
import {
    createCamera,
    switchToCamera,
    configureControls,
    handleResize,
} from '../view_mode.js';
import { setupControls } from '../controls.js';
import { composeObjects } from './composer.js';
import {
    materialColorSrc,
    materialPreamble,
    buildMaterialRows,
    padMaterialRows,
    parseHexColor,
} from './material-table.js';
import {
    overlaySrc,
    buildOverlayUniforms,
    applyOverlayUniforms,
} from './overlays/factory.js';
import {
    distinctEmbedSrcs,
    matrixUniformDecls,
    mvLayout,
    emitDistanceFunctions,
    emitAlgebraLeaves,
    buildAlgebraUniforms,
} from './algebra/eval.js';
import { opacityFuncs } from './algebra/opacities.js';

const VERTEX_SHADER = /* glsl */ `
void main() {
    gl_Position = vec4(position.xy, 0.0, 1.0);
}
`;

// ── Live object state (from the WebSocket scene) ──────────
let objects = [];
let activeDistance = 'scalar_pseudo';
let activeOpacity = 'step';
let sceneConfig = null;

// Friendly viewer label passed via `?viewer=name` (sent back in the ready
// message); frontend build hash injected by the server, compared against the
// backend's advertised version to detect a stale cached copy.
const _viewerName = new URLSearchParams(window.location.search).get('viewer') || null;
const _frontendVersion =
    (typeof window !== 'undefined' && window.__tanga_frontend_version) || null;

// ── Lighting (directional lights + ambient) ───────────────
const MAX_LIGHTS = 8;

// Declared as a JS template so `MAX_LIGHTS` has a single source of truth, then
// injected into the assembled fragment before the raymarch body.
const lightPreamble = `
const int MAX_LIGHTS = ${MAX_LIGHTS};
uniform int uLightCount;
uniform vec3 uLightDir[MAX_LIGHTS];
uniform vec3 uLightColor[MAX_LIGHTS];
uniform vec3 uAmbientColor;
`;

// Frontend defaults mirror the Python defaults (a white light from (10,20,10)
// at intensity 0.8 plus a white 0.45 ambient), so an empty scene renders the
// same even before the server's first lighting config arrives.
const DEFAULT_LIGHTING = {
    ambient: { color: '#ffffff', intensity: 0.45 },
    lights: [{ direction: [10, 20, 10], color: '#ffffff', intensity: 0.8 }],
};

function parseAmbient(a) {
    const [r, g, b] = parseHexColor(a && a.color);
    const i = a && typeof a.intensity === 'number' ? a.intensity : 1.0;
    return [r * i, g * i, b * i];
}

function parseLight(l) {
    const [r, g, b] = parseHexColor(l && l.color);
    const i = l && typeof l.intensity === 'number' ? l.intensity : 1.0;
    let d = (l && l.direction) || [0, 0, 1];
    const len = Math.hypot(d[0], d[1], d[2]);
    d = len > 1e-9 ? [d[0] / len, d[1] / len, d[2] / len] : [0, 0, 1];
    return { direction: d, color: [r * i, g * i, b * i] };
}

let lighting = {
    ambient: parseAmbient(DEFAULT_LIGHTING.ambient),
    lights: DEFAULT_LIGHTING.lights.map(parseLight),
};

function setLightUniforms(u) {
    if (!u) return;
    u.uLightCount.value = lighting.lights.length;
    for (let i = 0; i < MAX_LIGHTS; i++) {
        const l = lighting.lights[i];
        if (l) {
            u.uLightDir.value[i].set(l.direction[0], l.direction[1], l.direction[2]);
            u.uLightColor.value[i].set(l.color[0], l.color[1], l.color[2]);
        } else {
            u.uLightDir.value[i].set(0, 0, 0);
            u.uLightColor.value[i].set(0, 0, 0);
        }
    }
    u.uAmbientColor.value.set(lighting.ambient[0], lighting.ambient[1], lighting.ambient[2]);
}

function applyLighting(wireLighting) {
    if (!wireLighting) return;
    if (wireLighting.ambient) lighting.ambient = parseAmbient(wireLighting.ambient);
    if (wireLighting.lights) lighting.lights = wireLighting.lights.map(parseLight);
    if (viewerState.material && viewerState.material.uniforms) {
        setLightUniforms(viewerState.material.uniforms);
    }
}

let overlays = [];

function applyOverlayState(wireOverlays) {
    if (!wireOverlays) return;
    overlays = wireOverlays;
    if (viewerState.material && viewerState.material.uniforms) {
        applyOverlayUniforms(viewerState.material.uniforms, overlays);
    }
}

// ── GLSL source loading ───────────────────────────────────

let _shaderParts = null;

async function _loadShaderSources() {
    if (_shaderParts) return _shaderParts;
    const base = new URL('./shaders/', import.meta.url);
    const [common, primitives, combinators, raymarch] = await Promise.all([
        fetch(new URL('sdf_common.glsl', base)).then((r) => r.text()),
        fetch(new URL('primitives.glsl', base)).then((r) => r.text()),
        fetch(new URL('combinators.glsl', base)).then((r) => r.text()),
        fetch(new URL('raymarch.glsl', base)).then((r) => r.text()),
    ]);
    _shaderParts = { common, primitives, combinators, raymarch };
    return _shaderParts;
}

// ── Program (re)compilation ───────────────────────────────

function buildFragment() {
    const { common, primitives, combinators, raymarch } = _shaderParts;
    const list = objects.length ? objects : DEFAULT_OBJECTS;
    const { totalFloats } = mvLayout(list);
    return [
        common,
        primitives,
        combinators,
        materialPreamble,
        materialColorSrc,
        lightPreamble,
        overlaySrc(),
        distinctEmbedSrcs(list).join('\n'),
        matrixUniformDecls(totalFloats),
        emitDistanceFunctions(list, activeDistance),
        emitAlgebraLeaves(list, activeDistance),
        emitOpacityFunction(),
        composeObjects(list),
        raymarch,
    ].join('\n');
}

function emitOpacityFunction() {
    const entry = opacityFuncs.get(activeOpacity);
    if (!entry) throw new Error(`Unknown opacity transfer '${activeOpacity}'`);
    return entry.snippet;
}

function buildUniforms() {
    const list = objects.length ? objects : DEFAULT_OBJECTS;
    const actualRows = buildMaterialRows(list);
    // The shader declares `uMaterial[MAX_SDF_OBJECTS]`, so the uniform value
    // must be a full-length array (three.js flattens the whole declared array);
    // pad unused slots with a transparent black material.
    const rows = padMaterialRows(actualRows);
    const { uM, uObjectParams } = buildAlgebraUniforms(list);
    const uniforms = {
        uResolution: { value: new THREE.Vector2() },
        uCameraPosition: { value: new THREE.Vector3() },
        uCameraWorldMatrix: { value: new THREE.Matrix4() },
        uCameraProjectionMatrixInverse: { value: new THREE.Matrix4() },
        uCameraNear: { value: 0.1 },
        uCameraFar: { value: 1000.0 },
        uMaterial: { value: rows.map((r) => new THREE.Vector4(r[0], r[1], r[2], r[3])) },
        uMaterialCount: { value: actualRows.length },
        u_M: { value: uM },
        u_ObjectParams: { value: uObjectParams },
        uLightCount: { value: lighting.lights.length },
        uLightDir: { value: Array.from({ length: MAX_LIGHTS }, () => new THREE.Vector3()) },
        uLightColor: { value: Array.from({ length: MAX_LIGHTS }, () => new THREE.Vector3()) },
        uAmbientColor: { value: new THREE.Vector3() },
    };
    setLightUniforms(uniforms);
    Object.assign(uniforms, buildOverlayUniforms(overlays));
    return uniforms;
}

// A single centered sphere so an empty scene still renders via the composed
// map path (slot 0).
const DEFAULT_OBJECTS = [
    { id: '__default__', tree: { kind: 'sphere', params: { radius: 1.0 } } },
];

// ── WebGL2 gate ────────────────────────────────────────────

function showError(message) {
    const banner = document.createElement('div');
    banner.style.position = 'fixed';
    banner.style.top = '0';
    banner.style.left = '0';
    banner.style.right = '0';
    banner.style.zIndex = '100001';
    banner.style.background = '#cc2222';
    banner.style.color = '#fff';
    banner.style.fontFamily = 'sans-serif';
    banner.style.fontSize = '14px';
    banner.style.padding = '12px 20px';
    banner.style.textAlign = 'center';
    banner.textContent = message;
    document.body.insertBefore(banner, document.body.firstChild);
}

function setStatus(cls) {
    const el = document.getElementById('status');
    if (el) el.className = cls;
}

// ── WebSocket client ──────────────────────────────────────

let ws = null;
let browserId = null;
let reconnectTimer = null;

// Auto-reconnect: retry at a fixed 2s interval for the first minute after a
// disconnect, then stop (manual reconnect via the button remains available).
const _RECONNECT_INTERVAL_MS = 2000;
const _RECONNECT_WINDOW_MS = 60000;
let _reconnectDeadline = 0;  // timestamp when auto-reconnect should stop (0 = none)
let _reconnectAttempts = 0;
const _savedTitle = document.title || 'Tanga SDF Viewer';

// Single-flight guard: increment on teardown so stale onopen/onclose handlers
// from superseded sockets are ignored.
let _wsGeneration = 0;

function _log(phase, detail) {
    const t = (typeof performance !== 'undefined' && performance.now)
        ? (performance.now() / 1000).toFixed(3) : '0';
    const parts = ['[tanga:' + phase + ' t=' + t + ']'];
    if (browserId) parts.push('id=' + browserId);
    if (detail) parts.push(detail);
    console.log(parts.join(' '));
}

function closeActiveWs() {
    if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
        _log('ws-teardown', 'closing active socket readyState=' + ws.readyState);
        _wsGeneration++;                          // invalidate stale handlers
        const old = ws;
        old.onopen = old.onclose = old.onerror = old.onmessage = null;
        try { old.close(); } catch (_) {}
    }
    ws = null;
}

function connectWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${location.host}/ws`;

    closeActiveWs();
    const gen = _wsGeneration;

    _reconnectAttempts++;
    updateStatusIndicator('connecting', _reconnectAttempts);
    document.title = 'Connecting… — ' + _savedTitle;

    _log('ws-connect', 'url=' + url + ' attempt=' + _reconnectAttempts + ' gen=' + gen);

    ws = new WebSocket(url);

    const connectWatchdog = setTimeout(() => {
        if (ws && ws.readyState === WebSocket.CONNECTING && gen === _wsGeneration) {
            _log('ws-watchdog', 'connect timed out after ' + _RECONNECT_INTERVAL_MS + 'ms - aborting and retrying');
            _wsGeneration++;               // invalidate this socket's handlers
            try { ws.close(); } catch (_) {}
            ws = null;
            // Respect the auto-reconnect window: stop retrying once it elapses.
            if (_reconnectDeadline && Date.now() >= _reconnectDeadline) {
                _log('ws-reconnect', 'auto-reconnect window elapsed - stopping (manual reconnect available)');
                return;
            }
            connectWebSocket();            // retry immediately
        }
    }, _RECONNECT_INTERVAL_MS);

    ws.onopen = () => {
        if (gen !== _wsGeneration) return;
        clearTimeout(connectWatchdog);
        const pageToken = window.__tanga_page_token
            || new URLSearchParams(window.location.search).get('token');
        _log('ws-open', 'attempt=' + _reconnectAttempts + ' token=' + (pageToken || 'none'));
        setStatus('connected');
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
        _reconnectAttempts = 0;
        _reconnectDeadline = 0;  // connected — clear any pending reconnect window
        hideReconnectButton();
        updateStatusIndicator('connected');
        document.title = _savedTitle;
        const readyPayload = { type: 'ready', scene: '' };
        if (browserId) readyPayload.browser_id = browserId;
        if (_viewerName) readyPayload.viewer_name = _viewerName;
        if (pageToken) readyPayload.page_token = pageToken;
        _log('ws-send', 'type=ready token=' + (pageToken || 'none'));
        ws.send(JSON.stringify(readyPayload));
    };

    ws.onmessage = (event) => {
        let msg;
        try {
            msg = JSON.parse(event.data);
        } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
            return;
        }
        handleMessage(msg);
    };

    ws.onclose = (event) => {
        if (gen !== _wsGeneration) return;
        clearTimeout(connectWatchdog);
        _log('ws-close', 'code=' + event.code + ' reason=' + (event.reason || 'none')
            + ' wasClean=' + event.wasClean);
        setStatus('disconnected');
        updateStatusIndicator('disconnected');
        document.title = 'Disconnected — ' + _savedTitle;

        // Fixed-interval auto-reconnect for the first minute after the
        // connection was lost, then stop (the manual button still works).
        const now = Date.now();
        if (!_reconnectDeadline) {
            _reconnectDeadline = now + _RECONNECT_WINDOW_MS;
        }
        if (now < _reconnectDeadline) {
            _log('ws-reconnect', 'delay=' + _RECONNECT_INTERVAL_MS + 'ms deadline_in=' + Math.round((_reconnectDeadline - now) / 1000) + 's');
            reconnectTimer = setTimeout(connectWebSocket, _RECONNECT_INTERVAL_MS);
        } else {
            _log('ws-reconnect', 'auto-reconnect window elapsed - stopping (manual reconnect available)');
        }
    };

    ws.onerror = () => { _log('ws-error', 'error event (onclose follows)'); };
}

// ── Visibility wake-up ────────────────────────────────────────
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && ws === null) {
        _log('ws-visibility', 'tab visible with no socket — immediate reconnect');
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
        _reconnectDeadline = Date.now() + _RECONNECT_WINDOW_MS;
        connectWebSocket();
    }
});

// ── Reconnect Button ──────────────────────────────────────────
let _reconnectButtonEl = null;
let _reconnectClickCount = 0;

function showReconnectButton(mode) {
    if (_reconnectButtonEl) {
        _reconnectButtonEl.remove();
        _reconnectButtonEl = null;
    }

    _reconnectButtonEl = document.createElement('button');
    _reconnectButtonEl.id = 'tanga-reconnect-btn';
    _reconnectButtonEl.style.padding = '2px 8px';
    _reconnectButtonEl.style.fontSize = '11px';
    _reconnectButtonEl.style.fontFamily = 'sans-serif';
    _reconnectButtonEl.style.color = '#fff';
    _reconnectButtonEl.style.background = 'rgba(255,255,255,0.15)';
    _reconnectButtonEl.style.border = '1px solid rgba(255,255,255,0.3)';
    _reconnectButtonEl.style.borderRadius = '3px';
    _reconnectButtonEl.style.cursor = 'pointer';
    _reconnectButtonEl.style.zIndex = '11';
    _reconnectButtonEl.style.transition = 'background 0.2s';

    _reconnectButtonEl.addEventListener('mouseenter', () => {
        _reconnectButtonEl.style.background = 'rgba(255,255,255,0.25)';
    });
    _reconnectButtonEl.addEventListener('mouseleave', () => {
        _reconnectButtonEl.style.background = 'rgba(255,255,255,0.15)';
    });

    if (mode === 'page-reload') {
        _reconnectButtonEl.textContent = '↻ Reload';
        _reconnectButtonEl.title = 'Reconnect failed — reload page';
        _reconnectButtonEl.addEventListener('click', () => {
            window.location.reload();
        });
    } else {
        _reconnectButtonEl.textContent = 'Reconnect';
        _reconnectButtonEl.title = 'Click to reconnect immediately';
        _reconnectButtonEl.addEventListener('click', () => {
            _reconnectClickCount++;
            if (_reconnectClickCount >= 3) {
                _log('ws-manual', '3 failed clicks — offering page reload');
                showReconnectButton('page-reload');
                return;
            }
            _log('ws-manual', 'reconnect click=' + _reconnectClickCount);
            if (reconnectTimer) {
                clearTimeout(reconnectTimer);
                reconnectTimer = null;
            }
            closeActiveWs();
            _reconnectDeadline = Date.now() + _RECONNECT_WINDOW_MS;
            connectWebSocket();
        });
    }

    const statusArea = document.getElementById('tanga-status-area');
    if (statusArea) {
        statusArea.appendChild(_reconnectButtonEl);
    } else {
        document.body.appendChild(_reconnectButtonEl);
    }
}

function hideReconnectButton() {
    if (_reconnectButtonEl) {
        _reconnectButtonEl.remove();
        _reconnectButtonEl = null;
    }
    _reconnectClickCount = 0;
}

function updateStatusIndicator(state, attempts) {
    const el = document.getElementById('status');
    if (!el) return;
    if (state === 'connected') {
        el.className = 'connected';
        hideReconnectButton();
    } else {
        el.className = 'disconnected';
        if (!_reconnectButtonEl) {
            showReconnectButton('reconnect');
        }
    }

    let labelEl = document.getElementById('status-label');
    if (state === 'connecting' && attempts > 0) {
        if (!labelEl) {
            labelEl = document.createElement('span');
            labelEl.id = 'status-label';
            labelEl.style.color = '#888';
            labelEl.style.fontFamily = 'sans-serif';
            labelEl.style.fontSize = '11px';
            labelEl.style.pointerEvents = 'none';
            labelEl.style.whiteSpace = 'nowrap';
            const statusArea = document.getElementById('tanga-status-area');
            if (statusArea) {
                statusArea.appendChild(labelEl);
            } else {
                document.body.appendChild(labelEl);
            }
        }
        labelEl.textContent = 'attempt ' + attempts;
        labelEl.style.display = '';
    } else if (labelEl) {
        labelEl.style.display = 'none';
    }
}


// ── Version Mismatch Banner ───────────────────────────────────
let _versionBannerEl = null;

function hardReload() {
    // location.reload(true) is deprecated/ignored; replace with a fresh
    // cache-busting query param (scene routing is path-based, so this is safe).
    const url = new URL(window.location.href);
    url.searchParams.set('t', Date.now().toString());
    window.location.replace(url.toString());
}

function showVersionMismatchBanner(serverVersion, clientVersion) {
    if (_versionBannerEl) return;  // already showing

    const banner = document.createElement('div');
    banner.style.position = 'fixed';
    banner.style.top = '0';
    banner.style.left = '0';
    banner.style.right = '0';
    banner.style.zIndex = '100001';
    banner.style.background = '#cc2222';
    banner.style.color = '#fff';
    banner.style.fontFamily = 'sans-serif';
    banner.style.fontSize = '13px';
    banner.style.padding = '10px 16px';
    banner.style.display = 'flex';
    banner.style.alignItems = 'center';
    banner.style.justifyContent = 'center';
    banner.style.gap = '12px';
    banner.style.lineHeight = '1.5';

    const text = document.createElement('span');
    text.textContent =
        'The visualizer is out of date — backend expects version ' + serverVersion +
        ' but this page is running ' + clientVersion + '. Please hard-reload.';

    const btn = document.createElement('button');
    btn.textContent = 'Reload now';
    btn.style.padding = '4px 12px';
    btn.style.background = '#fff';
    btn.style.color = '#cc2222';
    btn.style.border = 'none';
    btn.style.borderRadius = '3px';
    btn.style.cursor = 'pointer';
    btn.style.fontWeight = 'bold';
    btn.onclick = hardReload;

    banner.appendChild(text);
    banner.appendChild(btn);
    document.body.insertBefore(banner, document.body.firstChild);
    _versionBannerEl = banner;

    _log('version-mismatch', 'server=' + serverVersion + ' client=' + clientVersion);
}

async function handleMessage(msg) {
    if (msg.type === 'browser_id') {
        browserId = msg.browser_id;
        _log('init', 'browser_id=' + msg.browser_id);
        if (msg.frontend_version && _frontendVersion
            && msg.frontend_version !== _frontendVersion) {
            showVersionMismatchBanner(msg.frontend_version, _frontendVersion);
        }
        return;
    }
    if (msg.type === 'clear_all') {
        objects = [];
        rebuildProgram();
        return;
    }
    if (msg.type === 'scene_config') {
        sceneConfig = msg;
        applySceneConfig(msg);
        applyLighting(msg.sdf_lighting);
        applyOverlayState(msg.sdf_overlays);
        return;
    }
    if (msg.type === 'scene_update') {
        let changed = false;
        if (msg.removed) {
            const removed = new Set(msg.removed);
            const before = objects.length;
            objects = objects.filter((o) => !removed.has(o.id));
            if (objects.length !== before) changed = true;
        }
        if (msg.objects) {
            for (const obj of msg.objects) {
                if (obj.kind !== 'sdf') continue;
                const idx = objects.findIndex((o) => o.id === obj.id);
                if (idx >= 0) objects[idx] = obj;
                else objects.push(obj);
            }
            changed = true;
        }
        if (changed) rebuildProgram();

        // Ack full-state sync so the server signals "ready".
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'scene_synced', browser_id: browserId }));
        }
        return;
    }
    if (msg.type === 'sdf_viewer_config') {
        if (msg.distance && msg.distance !== activeDistance) {
            activeDistance = msg.distance;
            rebuildProgram();
        }
        if (msg.opacity && msg.opacity !== activeOpacity) {
            activeOpacity = msg.opacity;
            rebuildProgram();
        }
        if (msg.lights || msg.ambient) {
            applyLighting({ ambient: msg.ambient, lights: msg.lights });
        }
        if (msg.overlays) {
            applyOverlayState(msg.overlays);
        }
        return;
    }
}

// ── Camera application (parity with the standard viewer) ──

function applySceneConfig(config) {
    const spaceDim = config.space_dim || 3;
    // switchToCamera handles "3d" camera configs and the default.
    const oldCamera = viewerState.camera;
    const next = switchToCamera(oldCamera, viewerState.controls, spaceDim, config.camera);
    viewerState.camera = next;

    const cc = config.camera;
    if (cc) {
        if (cc.position) viewerState.camera.position.set(cc.position[0], cc.position[1], cc.position[2]);
        if (cc.target) viewerState.controls.target.set(cc.target[0], cc.target[1], cc.target[2]);
        if (cc.fov) { viewerState.camera.fov = cc.fov; viewerState.camera.updateProjectionMatrix(); }
        if (cc.near) { viewerState.camera.near = cc.near; viewerState.camera.updateProjectionMatrix(); }
        if (cc.far) { viewerState.camera.far = cc.far; viewerState.camera.updateProjectionMatrix(); }
        viewerState.controls.update();
    }
    configureControls(viewerState.controls, viewerState.renderer, spaceDim);
    onResize();
}

// ── App state + init ──────────────────────────────────────

const viewerState = {
    renderer: null,
    camera: null,
    controls: null,
    quadCamera: null,
    scene: null,
    quad: null,
    material: null,
};

let _rebuilding = false;

// Diagnostic guard: set once the render loop has hit a fatal error so we stop
// scheduling frames and keep the console readable while the root cause is fixed.
let _renderLoopStopped = false;

let _structureKey = null;

function structureKey(list) {
    const parts = ['d:' + activeDistance, 'o:' + activeOpacity];
    for (const obj of list) {
        const kind = obj.sdfKind || 'analytic';
        const combine = obj.combine || 'union';
        const alg = obj.sdfKind === 'mv_sdf' ? (obj.algebra || '?') : '';
        const smooth = obj.smoothness != null ? obj.smoothness : '';
        parts.push(`${kind}/${combine}/${alg}/${smooth}`);
    }
    return parts.join('|');
}

function warnUnsignedBooleans(list) {
    if (activeDistance !== 'magnitude' && activeDistance !== 'grade') return;
    const bad = list.some(
        (o) => o.combine === 'intersection' || o.combine === 'subtract'
    );
    if (bad) {
        console.warn(
            "[sdf_viewer] 'intersection'/'subtract' require a signed distance " +
            "function, but '" + activeDistance + "' is unsigned"
        );
    }
}

function applyDataUniforms(u, list) {
    const actualRows = buildMaterialRows(list);
    const rows = padMaterialRows(actualRows);
    u.uMaterial.value.forEach((v, i) => v.set(rows[i][0], rows[i][1], rows[i][2], rows[i][3]));
    u.uMaterialCount.value = actualRows.length;
    const { uM, uObjectParams } = buildAlgebraUniforms(list);
    u.u_M.value = uM;
    u.u_ObjectParams.value = uObjectParams;
}

function rebuildProgram() {
    if (!_shaderParts || !viewerState.renderer) return;
    const list = objects.length ? objects : DEFAULT_OBJECTS;
    const key = structureKey(list);
    warnUnsignedBooleans(list);

    // Data-only change (same object kinds/combines/embeds + same distance/
    // opacity): update uniforms in place without recompiling the shader.
    if (_structureKey === key && viewerState.material) {
        applyDataUniforms(viewerState.material.uniforms, list);
        return;
    }

    _structureKey = key;
    _rebuilding = true;
    const material = new THREE.ShaderMaterial({
        vertexShader: VERTEX_SHADER,
        fragmentShader: buildFragment(),
        uniforms: buildUniforms(),
        glslVersion: THREE.GLSL3,
        depthWrite: false,
        depthTest: false,
    });
    viewerState.quad.material = material;
    // Wait a frame for three.js to compile; if it fails, the raw program
    // logs the driver error to the console (no silent fallback).
    viewerState.material = material;
    _rebuilding = false;
}

function formatShaderError(gl, shader, type) {
    const log = gl.getShaderInfoLog(shader).trim();
    const source = gl.getShaderSource(shader);
    const m = /ERROR: 0:(\d+)/.exec(log);
    if (!m) return `${type}\n\n${log}`;
    const errLine = parseInt(m[1], 10);
    const lines = source.split('\n');
    const from = Math.max(errLine - 6, 0);
    const to = Math.min(errLine + 6, lines.length);
    const ctx = [];
    for (let i = from; i < to; i++) {
        ctx.push(`${i + 1 === errLine ? '>' : ' '} ${i + 1}: ${lines[i]}`);
    }
    return `${type}\n\n${log}\n\n${ctx.join('\n')}`;
}

async function init() {
    let renderer;
    try {
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    } catch (e) {
        console.error('WebGL renderer creation failed:', e);
        showError('SDF viewer requires WebGL2, which is not available.');
        return;
    }
    if (!renderer.capabilities.isWebGL2) {
        showError('SDF viewer requires WebGL2.');
        renderer.dispose();
        return;
    }

    // Diagnostic guard: if the shader fails to compile/link, three.js reports
    // it on first use; stop the loop too so the "current program is not linked"
    // WebGL warnings can't spam every frame and hide the original error.
    renderer.debug.onShaderError = (gl, program, glVertexShader, glFragmentShader) => {
        _renderLoopStopped = true;
        console.error(
            'THREE.WebGLProgram: Shader Error (render loop stopped) - ' +
            'VALIDATE_STATUS ' + gl.getProgramParameter(program, gl.VALIDATE_STATUS) + '\n\n' +
            'Program Info Log: ' + gl.getProgramInfoLog(program).trim() + '\n' +
            formatShaderError(gl, glVertexShader, 'VERTEX') + '\n' +
            formatShaderError(gl, glFragmentShader, 'FRAGMENT')
        );
    };

    const container = document.getElementById('viewer-container') || document.body;
    container.appendChild(renderer.domElement);
    renderer.setPixelRatio(window.devicePixelRatio);

    viewerState.renderer = renderer;
    viewerState.camera = createCamera(3, window.innerWidth / window.innerHeight);
    viewerState.controls = setupControls(viewerState.camera, renderer);
    viewerState.quadCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    viewerState.scene = new THREE.Scene();

    await _loadShaderSources();

    viewerState.quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), undefined);
    viewerState.quad.frustumCulled = false;
    viewerState.scene.add(viewerState.quad);
    rebuildProgram();

    window.addEventListener('resize', onResize);
    if (typeof ResizeObserver !== 'undefined' && container) {
        const ro = new ResizeObserver(() => onResize());
        ro.observe(container);
    }
    onResize();

    connectWebSocket();
    animate();

    window.__tanga_ready = true;
}

function onResize() {
    const container = document.getElementById('viewer-container');
    const width = container?.clientWidth || window.innerWidth;
    const height = container?.clientHeight || window.innerHeight;
    if (viewerState.renderer && viewerState.camera && viewerState.controls) {
        handleResize(viewerState.camera, viewerState.renderer, null, sceneConfig?.space_dim || 3, width, height);
    }
}

function animate() {
    if (_renderLoopStopped) return;

    const { renderer, camera, controls, quadCamera, scene, material } = viewerState;
    if (!renderer || !camera || !controls || !scene || !material) {
        requestAnimationFrame(animate);
        return;
    }

    try {
        controls.update();
        camera.updateMatrixWorld();

        const u = material.uniforms;
        if (u) {
            u.uResolution.value.set(renderer.domElement.width, renderer.domElement.height);
            u.uCameraPosition.value.copy(camera.position);
            u.uCameraWorldMatrix.value.copy(camera.matrixWorld);
            u.uCameraProjectionMatrixInverse.value.copy(camera.projectionMatrixInverse);
            u.uCameraNear.value = camera.near;
            u.uCameraFar.value = camera.far;
        }

        renderer.render(scene, quadCamera);
    } catch (e) {
        _renderLoopStopped = true;
        console.error('[sdf_viewer] render loop stopped after an error:', e);
        return;
    }

    requestAnimationFrame(animate);
}

init().catch((e) => {
    console.error('SDF viewer initialization failed:', e);
    showError('The SDF viewer could not start due to an unexpected error.');
});