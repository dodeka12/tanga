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
    MAX_SDF_OBJECTS,
    materialColorSrc,
    materialPreamble,
    buildMaterialRows,
} from './material-table.js';

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
    return [
        common,
        primitives,
        combinators,
        materialPreamble,
        materialColorSrc,
        composeObjects(list),
        raymarch,
    ].join('\n');
}

function buildUniforms() {
    const list = objects.length ? objects : DEFAULT_OBJECTS;
    const rows = buildMaterialRows(list);
    return {
        uResolution: { value: new THREE.Vector2() },
        uCameraPosition: { value: new THREE.Vector3() },
        uCameraWorldMatrix: { value: new THREE.Matrix4() },
        uCameraProjectionMatrixInverse: { value: new THREE.Matrix4() },
        uCameraNear: { value: 0.1 },
        uCameraFar: { value: 1000.0 },
        uMaterial: { value: rows.map((r) => new THREE.Vector4(r[0], r[1], r[2], r[3])) },
        uMaterialCount: { value: rows.length },
    };
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

function connectWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${location.host}/ws`);

    ws.onopen = () => {
        setStatus('connected');
        const pageToken = window.__tanga_page_token
            || new URLSearchParams(window.location.search).get('token');
        ws.send(JSON.stringify({
            type: 'ready',
            scene: '',
            page_token: pageToken || undefined,
        }));
    };

    ws.onmessage = (event) => {
        let msg;
        try {
            msg = JSON.parse(event.data);
        } catch (e) {
            return;
        }
        handleMessage(msg);
    };

    ws.onclose = () => setStatus('disconnected');
}

async function handleMessage(msg) {
    if (msg.type === 'browser_id') {
        browserId = msg.browser_id;
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

function rebuildProgram() {
    if (!_shaderParts || !viewerState.renderer) return;
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
    requestAnimationFrame(animate);
    const { renderer, camera, controls, quadCamera, scene, material } = viewerState;
    if (!renderer || !camera || !material) return;
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
}

init().catch((e) => {
    console.error('SDF viewer initialization failed:', e);
    showError('The SDF viewer could not start due to an unexpected error.');
});