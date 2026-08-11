// Tanga Viewer — Main entry point
// Sets up Three.js scene, WebSocket client, entity registry, and render loop.
// All dimension‑specific logic lives in view_mode.js.

window.__tanga_ready = true;

import * as THREE from 'three';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { setupControls } from './controls.js';
import { createEntityMesh, removeEntityMesh } from './renderers/factory.js';
import { startTween, updateTweens, cancelTween } from './animator.js';
import { setWebSocket, handleControlsDefine, handleControlsClear } from './controls-panel.js';
import { attachGroup, detachGroup, detachAll } from './controls-attached.js';
import { createCamera, configureControls, fitCamera, handleResize, applyOverlayDrawOrder, switchToCamera, createGrid } from './view_mode.js';
import { initInteraction, registerInteractive, unregisterInteractive, clearAllInteractive, setWebSocket as setInteractionWebSocket } from './interaction.js';

// ── State ───────────────────────────────────────────────────
const sceneObjects = new Map();   // id → {obj, layer, el?}
const entityMeshes = new Map();   // id → THREE.Object3D (backward compat for render loop / tween / camera)
const entityData = new Map();     // id → raw JSON entity data (backward compat)
const labelObjects = new Map();   // id → CSS2DObject (backward compat for render loop)

let scene, camera, renderer, controls;
let ws = null;
let reconnectTimer = null;
let sceneConfig = null;
let cameraPositioned = false;
let _savedPixelRatio = null;     // saved during screenshot capture
let _savedStatusDisplay = null;  // saved during screenshot capture

// ── Scene & browser identity ──────────────────────────────────
let _myScene = (() => {
    const path = window.location.pathname.replace(/\/+$/, '');
    return path === '' ? '' : path.replace(/^\//, '');
})();
let _browserId = null;
let _viewerName = (() => {
    const params = new URLSearchParams(window.location.search);
    return params.get('viewer') || null;
})();
let _availableScenes = [];

// ── Scene Setup ──────────────────────────────────────────────
function initScene() {
    window._viewerContainer = document.getElementById('viewer-container');

    let webglOk = true;
    try {
        // WebGL Renderer
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.shadowMap.enabled = false;
        window._viewerContainer.appendChild(renderer.domElement);
    } catch (e) {
        console.warn('WebGL renderer failed — falling back to headless mode:', e.message);
        webglOk = false;
        renderer = null;
    }

    // CSS2D Renderer
    try {
        window._labelRenderer = new CSS2DRenderer();
        window._labelRenderer.setSize(window.innerWidth, window.innerHeight);
        window._labelRenderer.domElement.style.position = 'absolute';
        window._labelRenderer.domElement.style.top = '0px';
        window._labelRenderer.domElement.style.pointerEvents = 'none';
        window._viewerContainer.appendChild(window._labelRenderer.domElement);
    } catch (e) {
        window._labelRenderer = null;
    }

    // Scene (always created — works even without a renderer)
    scene = new THREE.Scene();
    scene.fog = null;

    // Camera — delegates to view_mode.js for 2D/3D creation
    camera = createCamera(
        sceneConfig?.space_dim || 3,
        window.innerWidth / window.innerHeight,
        sceneConfig?.space_extent || 10
    );

    // Lights
    scene.add(new THREE.AmbientLight(0xffffff, 0.5));
    const d1 = new THREE.DirectionalLight(0xffffff, 0.8);
    d1.position.set(10, 20, 10);
    scene.add(d1);
    const d2 = new THREE.DirectionalLight(0xffffff, 0.3);
    d2.position.set(-5, -2, -8);
    scene.add(d2);

    // Grid & Axes (placeholders, rebuilt by applySceneConfig)
    window._gridHelper = new THREE.GridHelper(20, 20, 0x444466, 0x222244);
    scene.add(window._gridHelper);
    window._axesHelper = new THREE.AxesHelper(5);
    scene.add(window._axesHelper);

    // Controls — only if WebGL is available (needs renderer.domElement)
    if (webglOk && renderer) {
        controls = setupControls(camera, renderer);
        // Initialize interaction system
        initInteraction(camera, renderer.domElement, controls, ws);
        // Ctrl+S screenshot shortcut
        window.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                const dataUrl = renderer.domElement.toDataURL('image/png');
                const now = new Date();
                const ts = now.toISOString().replace(/[:.]/g, '-').slice(0, 19);
                const link = document.createElement('a');
                link.download = `tanga_${ts}.png`;
                link.href = dataUrl;
                link.click();
            }
        });
    }

    window.addEventListener('resize', onResize);

}

function onResize() {
    handleResize(
        camera,
        renderer,
        window._labelRenderer,
        window._viewerContainer,
        sceneConfig?.space_dim || 3
    );
}

// ── WebSocket Client ────────────────────────────────────────
let _reconnectAttempts = 0;
let _savedTitle = document.title || 'Tanga Viewer';

function connectWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${location.host}/ws`;

    _reconnectAttempts++;
    updateStatusIndicator('connecting', _reconnectAttempts);
    document.title = 'Connecting… — ' + _savedTitle;

    ws = new WebSocket(url);

    ws.onopen = () => {
        const pageToken = window.__tanga_page_token
            || new URLSearchParams(window.location.search).get('token');
        console.log('[tanga] WS connected (attempt=' + _reconnectAttempts
            + ', token=' + (pageToken || 'none') + ')');
        setStatus('connected');
        setWebSocket(ws);
        setInteractionWebSocket(ws);
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
        _reconnectAttempts = 0;
        updateStatusIndicator('connected');
        document.title = _savedTitle;
        const readyPayload = { type: 'ready', scene: _myScene };
        if (_browserId) readyPayload.browser_id = _browserId;
        if (_viewerName) readyPayload.viewer_name = _viewerName;
        if (pageToken) readyPayload.page_token = pageToken;
        ws.send(JSON.stringify(readyPayload));
    };

    ws.onmessage = (event) => {
        try {
            handleMessage(JSON.parse(event.data));
        } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
        }
    };

    ws.onclose = (event) => {
        console.warn('[tanga] WS closed (code=' + event.code + '), retrying in 800ms');
        setStatus('disconnected');
        updateStatusIndicator('disconnected');
        reconnectTimer = setTimeout(connectWebSocket, 800);
        document.title = 'Disconnected — ' + _savedTitle;
    };

    ws.onerror = () => { /* onclose will fire next */ };
}

function setStatus(cls) {
    const el = document.getElementById('status');
    if (!el) return;
    el.className = cls;
}

function updateStatusIndicator(state, attempts) {
    const el = document.getElementById('status');
    if (!el) return;
    el.className = state === 'connected' ? 'connected' : 'disconnected';

    let labelEl = document.getElementById('status-label');
    if (state === 'connecting' && attempts > 0) {
        if (!labelEl) {
            labelEl = document.createElement('span');
            labelEl.id = 'status-label';
            labelEl.style.position = 'fixed';
            labelEl.style.top = '8px';
            labelEl.style.right = '26px';
            labelEl.style.color = '#888';
            labelEl.style.fontFamily = 'sans-serif';
            labelEl.style.fontSize = '11px';
            labelEl.style.pointerEvents = 'none';
            labelEl.style.zIndex = '11';
            document.body.appendChild(labelEl);
        }
        labelEl.textContent = 'attempt ' + attempts;
        labelEl.style.display = '';
    } else if (labelEl) {
        labelEl.style.display = 'none';
    }
}

// ── Scene Config ─────────────────────────────────────────────
function applySceneConfig(config) {
    sceneConfig = config;
    const spaceDim = config.space_dim || 3;

    if (config.background_color) {
        scene.background = new THREE.Color(config.background_color);
    }
    const extent = config.space_extent || 10;

    // Grid — delegates to view_mode.js for XY-plane (2D) vs XZ-plane (3D)
    if (window._gridHelper) {
        scene.remove(window._gridHelper);
        window._gridHelper.geometry.dispose();
        window._gridHelper.material.dispose();
    }
    if (config.show_grid !== false) {
        window._gridHelper = createGrid(scene, extent, spaceDim);
        scene.add(window._gridHelper);
    }

    // Axes
    if (window._axesHelper) {
        scene.remove(window._axesHelper);
        window._axesHelper.geometry?.dispose();
        window._axesHelper.material?.dispose();
    }
    if (config.show_axes !== false) {
        window._axesHelper = new THREE.AxesHelper(extent);
        scene.add(window._axesHelper);
    }

    // Switch to 2D orthographic camera if needed — must happen before
    // user-configured camera overrides (cc.position etc.) because
    // switchToCamera replaces the camera object entirely.
    camera = switchToCamera(camera, controls, spaceDim, extent);

    // Camera (user-configured)
    const cc = config.camera;
    if (cc) {
        if (cc.position) camera.position.set(cc.position[0], cc.position[1], cc.position[2]);
        if (cc.target) controls.target.set(cc.target[0], cc.target[1], cc.target[2]);
        if (cc.fov) { camera.fov = cc.fov; camera.updateProjectionMatrix(); }
        if (cc.near) { camera.near = cc.near; camera.updateProjectionMatrix(); }
        if (cc.far) { camera.far = cc.far; camera.updateProjectionMatrix(); }
        controls.update();
    }

    // Controls & renderer — delegates to view_mode.js
    configureControls(controls, renderer, spaceDim);

    // Title
    if (config.title !== undefined) {
        renderTitle(config.title);
    }

    // Annotation
    if (config.annotation) {
        renderAnnotation(config.annotation, null);
    } else if (config.annotation === '') {
        removeAnnotation();
    }
}

// ── Title Overlay ─────────────────────────────────────────────
let titleElement = null;

function renderTitle(titleText) {
    if (!titleElement) {
        titleElement = document.createElement('div');
        titleElement.style.position = 'absolute';
        titleElement.style.top = '10px';
        titleElement.style.left = '50%';
        titleElement.style.transform = 'translateX(-50%)';
        titleElement.style.color = '#ffffff';
        titleElement.style.fontFamily = 'sans-serif';
        titleElement.style.fontSize = '20px';
        titleElement.style.fontWeight = 'bold';
        titleElement.style.background = 'rgba(0, 0, 0, 0.6)';
        titleElement.style.padding = '6px 20px';
        titleElement.style.borderRadius = '4px';
        titleElement.style.pointerEvents = 'none';
        titleElement.style.zIndex = '5';
        window._viewerContainer.appendChild(titleElement);
    }
    titleElement.textContent = '';  // clear first
    titleElement.innerHTML = titleText;
    if (typeof renderMathInElement !== 'undefined') {
        try {
            renderMathInElement(titleElement, {
                delimiters: [
                    { left: '$$', right: '$$', display: true },
                    { left: '$', right: '$', display: false },
                ],
                throwOnError: false,
            });
        } catch (e) { /* ignore */ }
    }
}

// ── Annotation Panel ──────────────────────────────────────────
let annotationPanel = null;

function renderAnnotation(mdText, styleData) {
    removeAnnotation();

    const s = styleData || {};

    const container = document.createElement('div');

    if (typeof marked !== 'undefined') {
        container.innerHTML = marked.parse(mdText);
    } else {
        container.textContent = mdText;
    }

    if (typeof renderMathInElement !== 'undefined') {
        try {
            renderMathInElement(container, {
                delimiters: [
                    { left: '$$', right: '$$', display: true },
                    { left: '$', right: '$', display: false },
                ],
                throwOnError: false,
            });
        } catch (e) {
            console.warn('KaTeX rendering error:', e);
        }
    }

    container.style.position = 'absolute';
    container.style.bottom = '0px';
    container.style.left = '50%';
    container.style.transform = 'translateX(-50%)';
    container.style.width = s.width || '100%';
    container.style.maxWidth = s.max_width || '800px';
    container.style.maxHeight = s.max_height || '250px';
    container.style.overflowY = 'auto';
    container.style.fontFamily = s.font_family || 'sans-serif';
    container.style.fontSize = (s.font_size || 13) + 'px';
    container.style.color = s.color || '#cccccc';
    container.style.backgroundColor = s.background || 'rgba(0, 0, 0, 0.75)';
    container.style.padding = s.padding || '10px 16px';
    container.style.borderRadius = s.border_radius || '4px';
    container.style.zIndex = '5';
    container.style.lineHeight = '1.5';
    container.className = 'annotation-container';

    const linkColor = s.link_color || '#88ccff';
    const codeBg = s.code_background || 'rgba(255,255,255,0.1)';
    const styleEl = document.createElement('style');
    styleEl.textContent = `
        .annotation-container h1, .annotation-container h2, .annotation-container h3,
        .annotation-container h4, .annotation-container h5, .annotation-container h6 {
            margin-top: 0.6em; margin-bottom: 0.3em;
        }
        .annotation-container h1 { font-size: 1.3em; }
        .annotation-container h2 { font-size: 1.15em; }
        .annotation-container h3 { font-size: 1.05em; }
        .annotation-container p { margin: 0.3em 0; }
        .annotation-container a { color: ${linkColor}; }
        .annotation-container code {
            background: ${codeBg}; padding: 1px 4px; border-radius: 3px;
        }
        .annotation-container pre {
            background: rgba(0,0,0,0.3); padding: 8px; border-radius: 4px; overflow-x: auto;
        }
        .annotation-container hr {
            border: 0; border-top: 1px solid rgba(255,255,255,0.2); margin: 0.5em 0;
        }
    `;
    container.appendChild(styleEl);

    window._viewerContainer.appendChild(container);
    annotationPanel = container;
}

function removeAnnotation() {
    if (annotationPanel) {
        annotationPanel.remove();
        annotationPanel = null;
    }
}

function fitCameraToScene() {
    fitCamera(entityMeshes, camera, controls, sceneConfig?.space_dim || 3);
}

// ── Helper: rotate mesh to point along a direction vector ───
function rotationFromDirection(dx, dy, dz) {
    const direction = new THREE.Vector3(dx, dy, dz).normalize();
    const quaternion = new THREE.Quaternion();
    quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction);
    return quaternion;
}

// ── Numeric tolerance helper ─────────────────────────────────
function _approx(a, b, eps = 1e-9) {
    return Math.abs(a - b) < eps;
}

// ── In-place entity updates for frame streaming ─────────────
function inPlaceUpdate(ent) {
    const mesh = entityMeshes.get(ent.id);
    if (!mesh) return false;

    const previous = entityData.get(ent.id);

    // Position update
    if (ent.position) {
        mesh.position.set(ent.position[0], ent.position[1], ent.position[2]);
        applyOverlayDrawOrder(mesh, ent.position[2] || 0, sceneConfig?.space_dim || 3);
    }

    // Direction/vector update
    if (ent.vector || ent.direction) {
        const vec = ent.vector || ent.direction;
        const origin = ent.origin || [0, 0, 0];
        // Line entities position their cylinder mesh at the midpoint
        // (origin + dir * len/2), not at origin.  Other direction-based
        // entities (Direction arrow groups, etc.) sit at origin.
        if (ent.kind === 'Line') {
            const len = (ent.length !== undefined) ? ent.length : (previous?.length ?? 20.0);
            const d = new THREE.Vector3(vec[0], vec[1], vec[2]).normalize();
            mesh.position.set(
                origin[0] + d.x * len / 2,
                origin[1] + d.y * len / 2,
                origin[2] + d.z * len / 2
            );
        } else {
            mesh.position.set(origin[0], origin[1], origin[2]);
        }
        mesh.setRotationFromQuaternion(rotationFromDirection(vec[0], vec[1], vec[2]));
    }

    // Center update
    if (ent.center) {
        mesh.position.set(ent.center[0], ent.center[1], ent.center[2]);
    }

    // Opacity update
    if (ent.opacity !== undefined && ent.opacity !== (previous?.opacity)) {
        const val = ent.opacity;
        mesh.traverse(child => {
            if (child.material && child.material.opacity !== undefined) {
                child.material.opacity = val;
                child.material.transparent = val < 1.0;
                child.material.depthWrite = val >= 0.99;
                child.material.needsUpdate = true;
            }
        });
    }

    // Color update
    if (ent.color && ent.color !== previous?.color) {
        const c = new THREE.Color(ent.color);
        mesh.traverse(child => {
            if (child.material && child.material.color) {
                child.material.color.copy(c);
            }
        });
    }

    // Scale update
    if (ent.scale) {
        mesh.scale.set(ent.scale[0], ent.scale[1], ent.scale[2]);
    }

    // PointPath requires full rebuild on any change
    if (ent.kind === 'PointPath') return false;

    // Structural changes require full rebuild (tolerance-aware)
    if (ent.radius !== undefined && (!previous || !_approx(ent.radius, previous.radius))) return false;
    if (ent.extent !== undefined && (!previous || !_approx(ent.extent, previous.extent))) return false;
    if (ent.length !== undefined && (!previous || !_approx(ent.length, previous.length))) return false;
    if (ent.kind !== undefined && ent.kind !== previous?.kind) return false;

    return true;
}

// ── Message Handler ─────────────────────────────────────────
function _forMyScene(msg) {
    return !msg.scene || msg.scene === _myScene;
}

function handleMessage(msg) {
    if (msg.type === 'browser_id') {
        _browserId = msg.browser_id;
        return;
    }
    if (msg.type === 'navigate') {
        const target = msg.scene || '';
        let newUrl = target ? '/' + target : '/';
        if (_viewerName) {
            newUrl += '?viewer=' + encodeURIComponent(_viewerName);
        }
        window.location.href = newUrl;
        return;
    }
    if (msg.type === 'scene_list') {
        _availableScenes = msg.scenes || [];
        return;
    }

    if (msg.type === 'scene_config' || msg.type === 'scene_update') {
        if (!_forMyScene(msg)) return;
    }
    if (msg.type === 'controls_define' || msg.type === 'controls_clear') {
        if (!_forMyScene(msg)) return;
    }

    if (msg.type === 'clear_all') {
        console.log('[clear_all] Resetting scene — objects:', sceneObjects.size, 'meshes:', entityMeshes.size, 'labels:', labelObjects.size);
        // Remove all scene children (entities, lights, grid, axes)
        while (scene.children.length > 0) {
            const child = scene.children[0];
            scene.remove(child);
            if (child.geometry) child.geometry.dispose();
            if (child.material) {
                if (Array.isArray(child.material)) {
                    child.material.forEach(m => m.dispose());
                } else {
                    child.material.dispose();
                }
            }
        }
        // Remove all CSS2D objects from the label renderer
        if (window._labelRenderer && window._labelRenderer.domElement) {
            window._labelRenderer.domElement.innerHTML = '';
        }
        // Clear maps
        clearAllInteractive();
        entityMeshes.clear();
        entityData.clear();
        labelObjects.clear();
        sceneObjects.clear();
        // Clear overlays
        removeAnnotation();
        if (titleElement) {
            titleElement.remove();
            titleElement = null;
        }
        handleControlsClear();
        detachAll();
        cameraPositioned = false;
        // Rebuild default lights
        scene.add(new THREE.AmbientLight(0xffffff, 0.5));
        const d1 = new THREE.DirectionalLight(0xffffff, 0.8);
        d1.position.set(10, 20, 10);
        scene.add(d1);
        const d2 = new THREE.DirectionalLight(0xffffff, 0.3);
        d2.position.set(-5, -2, -8);
        scene.add(d2);
        console.log('[clear_all] Scene reset complete');
    } else if (msg.type === 'scene_config') {
        applySceneConfig(msg);
    } else if (msg.type === 'scene_update') {
        if (msg.removed) {
            for (const id of msg.removed) {
                unregisterInteractive(id);
                const mesh = entityMeshes.get(id);
                if (mesh) {
                    if (mesh.userData._attachedGroups) {
                        for (const groupId of mesh.userData._attachedGroups) {
                            detachGroup(groupId);
                        }
                    }
                    removeEntityMesh(mesh);
                }
                entityMeshes.delete(id);
                entityData.delete(id);
                const oldObj = sceneObjects.get(id);
                if (oldObj) {
                    if (oldObj.obj && oldObj.obj.removeFromParent) oldObj.obj.removeFromParent();
                    if (oldObj.el) oldObj.el.remove();
                    sceneObjects.delete(id);
                }
                const lbl = labelObjects.get(id);
                if (lbl) {
                    lbl.removeFromParent();
                    if (lbl.element) lbl.element.remove();
                    labelObjects.delete(id);
                }
                cancelTween(id);
            }
        }
        if (msg.objects) {
            for (const obj of msg.objects) {
                if (obj.layer === 'scene' && entityMeshes.has(obj.id)) {
                    updateEntity(obj);
                } else {
                    upsertObject(obj);
                }
            }
        }
        if (msg.entities) {
            for (const ent of msg.entities) {
                updateEntity(ent);
            }
        }
        if (msg.labels) {
            for (const lbl of msg.labels) {
                upsertLabel(lbl);
            }
        }
        if (msg.fit_camera) {
            fitCameraToScene();
        }
    } else if (msg.type === 'animate') {
        handleAnimate(msg);
    } else if (msg.type === 'timeline') {
        handleTimeline(msg);
    } else if (msg.type === 'screenshot') {
        handleScreenshot(msg);
    } else if (msg.type === 'controls_define') {
        handleControlsDefine(msg);
        const controls2 = msg.controls || [];
        const groups = msg.groups || [];
        for (const g of groups) {
            if (g.parentId) {
                attachGroup(g, controls2, entityMeshes);
            }
        }
    } else if (msg.type === 'controls_clear') {
        handleControlsClear();
        detachAll();
    } else if (msg.type === 'restore_size') {
        if (_savedPixelRatio !== null) {
            renderer.setPixelRatio(_savedPixelRatio);
            _savedPixelRatio = null;
        }
        const statusEl2 = document.getElementById('status');
        if (statusEl2) {
            statusEl2.style.display = _savedStatusDisplay || 'block';
            _savedStatusDisplay = null;
        }
        onResize();
    }
}

function handleScreenshot(msg) {
    const statusEl = document.getElementById('status');
    if (statusEl) {
        _savedStatusDisplay = statusEl.style.display;
        statusEl.style.display = 'none';
    }

    if (msg.width && msg.height) {
        const w = msg.width, h = msg.height;
        _savedPixelRatio = renderer.getPixelRatio();
        renderer.setPixelRatio(1);
        renderer.setSize(w, h);
        camera.aspect = w / h;
        camera.updateProjectionMatrix();
        if (window._labelRenderer) {
            window._labelRenderer.setSize(w, h);
        }
        if (window._viewerContainer) {
            window._viewerContainer.style.width = w + 'px';
            window._viewerContainer.style.height = h + 'px';
        }
    }
    renderer.render(scene, camera);
    if (window._labelRenderer) {
        window._labelRenderer.render(scene, camera);
    }
    const w = renderer.domElement.width;
    const h = renderer.domElement.height;

    if (typeof html2canvas !== 'undefined') {
        html2canvas(window._viewerContainer, {
            width: w,
            height: h,
            windowWidth: w,
            windowHeight: h,
            backgroundColor: null,
            scale: 1,
        }).then(domCanvas => {
            ws.send(JSON.stringify({
                type: 'screenshot:data',
                request_id: msg.request_id,
                data: domCanvas.toDataURL('image/png'),
            }));
        }).catch(err => {
            console.warn('html2canvas failed, falling back to webgl only:', err);
            ws.send(JSON.stringify({
                type: 'screenshot:data',
                request_id: msg.request_id,
                data: renderer.domElement.toDataURL('image/png'),
            }));
        });
    } else {
        ws.send(JSON.stringify({
            type: 'screenshot:data',
            request_id: msg.request_id,
            data: renderer.domElement.toDataURL('image/png'),
        }));
    }
}

// ── Unified Object Management ──────────────────────────────

async function upsertObject(msg) {
    const old = sceneObjects.get(msg.id);
    if (old) {
        if (old.obj && old.obj.removeFromParent) old.obj.removeFromParent();
        if (old.el) old.el.remove();
        sceneObjects.delete(msg.id);
    }
    entityMeshes.delete(msg.id);
    entityData.delete(msg.id);
    labelObjects.delete(msg.id);

    if (msg.layer === 'scene') {
        const mesh = await createEntityMesh(msg);
        if (mesh) {
            if (msg.position) {
                applyOverlayDrawOrder(mesh, msg.position[2] || 0, sceneConfig?.space_dim || 3);
            }
            scene.add(mesh);
            sceneObjects.set(msg.id, { obj: mesh, layer: 'scene' });
            entityMeshes.set(msg.id, mesh);
            entityData.set(msg.id, { ...msg });
            // ── Interaction ──
            if (msg.interaction) {
                registerInteractive(msg.id, mesh, msg.interaction);
            }
        }
    } else if (msg.layer === 'overlay') {
        if (msg.kind === 'annotation') {
            if (!msg.text) return;
            renderAnnotation(msg.text, msg.style || null);
            if (annotationPanel) {
                sceneObjects.set(msg.id, { obj: null, el: annotationPanel, layer: 'overlay' });
            }
            return;
        }

        const el = buildOverlayElement(msg);
        if (!el) return;

        let css2d = null;
        if (msg.parentId) {
            const container = document.createElement('div');
            container.appendChild(el);
            css2d = new CSS2DObject(container);
            const pos = msg.position || [0, 0, 0];
            css2d.position.set(pos[0], pos[1], pos[2]);
            const off2d = msg.style?.offset_2d || [0, 0];
            const align = msg.style?.align || [0.5, 0.5];
            const tx = (0.5 - align[0]) * 100;
            const ty = (0.5 - align[1]) * 100;
            el.style.transform = `translate(${off2d[0]}px, ${off2d[1]}px) translate(${tx}%, ${ty}%)`;
            const parentObj = sceneObjects.get(msg.parentId);
            if (parentObj && parentObj.obj) {
                parentObj.obj.add(css2d);
                parentObj.obj.userData._labels = parentObj.obj.userData._labels || [];
                parentObj.obj.userData._labels.push(msg.id);
                css2d.userData._parentId = msg.parentId;
            } else {
                scene.add(css2d);
            }
            labelObjects.set(msg.id, css2d);
        } else {
            el.style.position = 'absolute';
            const off = msg.offset || [10, 10];
            el.style.top = off[1] + 'px';
            if (msg.anchor === 'top-right') {
                el.style.right = off[0] + 'px';
            } else {
                el.style.left = off[0] + 'px';
            }
            document.body.appendChild(el);
        }
        sceneObjects.set(msg.id, { obj: css2d, el, layer: 'overlay' });
    }
}

function buildOverlayElement(msg) {
    switch (msg.kind) {
        case 'label': {
            if (!msg.text) return null;
            const div = document.createElement('div');
            div.textContent = msg.text;
            const s = msg.style || {};
            div.style.fontFamily = s.font_family || 'sans-serif';
            div.style.fontSize = (s.font_size || 14) + 'px';
            div.style.color = s.color || '#ffffff';
            div.style.backgroundColor = s.background || 'rgba(0, 0, 0, 0.6)';
            div.style.padding = '2px 6px';
            div.style.borderRadius = '3px';
            div.style.userSelect = 'none';
            div.style.whiteSpace = 'nowrap';
            if (typeof renderMathInElement !== 'undefined') {
                try {
                    renderMathInElement(div, {
                        delimiters: [
                            { left: '$$', right: '$$', display: true },
                            { left: '$', right: '$', display: false },
                        ],
                        throwOnError: false,
                    });
                } catch (e) {
                    console.warn('KaTeX label rendering error:', e);
                }
            }
            return div;
        }
        case 'annotation': {
            if (!msg.text) return null;
            renderAnnotation(msg.text, msg.style || null);
            return annotationPanel;
        }
        default:
            console.warn('Unknown overlay kind: ' + msg.kind);
            return null;
    }
}

function upsertLabel(lbl) {
    if (!lbl.text) return;

    const existing = labelObjects.get(lbl.id);
    if (existing) {
        existing.removeFromParent();
        if (existing.element) existing.element.remove();
        labelObjects.delete(lbl.id);
    }

    const div = document.createElement('div');
    div.textContent = lbl.text;
    const s = lbl.style || {};
    div.style.fontFamily = s.font_family || 'sans-serif';
    div.style.fontSize = (s.font_size || 14) + 'px';
    div.style.color = s.color || '#ffffff';
    div.style.backgroundColor = s.background || 'rgba(0, 0, 0, 0.6)';
    div.style.padding = '2px 6px';
    div.style.borderRadius = '3px';
    div.style.userSelect = 'none';
    div.style.whiteSpace = 'nowrap';

    if (typeof renderMathInElement !== 'undefined') {
        try {
            renderMathInElement(div, {
                delimiters: [
                    { left: '$$', right: '$$', display: true },
                    { left: '$', right: '$', display: false },
                ],
                throwOnError: false,
            });
        } catch (e) {
            console.warn('KaTeX label rendering error:', e);
        }
    }

    const labelObj = new CSS2DObject(div);
    const pos = lbl.position || [0, 0, 0];
    const off = s.offset || [0, 0.3, 0];
    labelObj.position.set(pos[0] + off[0], pos[1] + off[1], pos[2] + off[2]);

    if (lbl.parentId && entityMeshes.has(lbl.parentId)) {
        const parentMesh = entityMeshes.get(lbl.parentId);
        parentMesh.add(labelObj);
        parentMesh.userData._labels = parentMesh.userData._labels || [];
        parentMesh.userData._labels.push(lbl.id);
        labelObj.userData._parentId = lbl.parentId;
    } else {
        scene.add(labelObj);
    }

    labelObjects.set(lbl.id, labelObj);
}

async function updateEntity(ent) {
    const id = ent.id;
    const existing = entityData.get(id);

    if (!existing) {
        const mesh = await createEntityMesh(ent);
        if (mesh) {
            if (ent.position) {
                applyOverlayDrawOrder(mesh, ent.position[2] || 0, sceneConfig?.space_dim || 3);
            }
            scene.add(mesh);
            entityMeshes.set(id, mesh);
        }
        entityData.set(id, { ...ent });
        return;
    }

    if (inPlaceUpdate(ent)) {
        entityData.set(id, { ...existing, ...ent });
        return;
    }

    const oldMesh = entityMeshes.get(id);
    const attachedLabels = oldMesh ? (oldMesh.userData._labels || []).slice() : [];
    if (oldMesh) removeEntityMesh(oldMesh);
    entityMeshes.delete(id);
    const mesh = await createEntityMesh({ ...existing, ...ent });
    if (mesh) {
        const pos = ent.position || existing?.position;
        if (pos) {
            applyOverlayDrawOrder(mesh, pos[2] || 0, sceneConfig?.space_dim || 3);
        }
        scene.add(mesh);
        entityMeshes.set(id, mesh);
        mesh.userData._labels = [];
        for (const lblId of attachedLabels) {
            const labelObj = labelObjects.get(lblId);
            if (labelObj) {
                mesh.add(labelObj);
                mesh.userData._labels.push(lblId);
            }
        }
    }
    entityData.set(id, { ...existing, ...ent });
}

function handleAnimate(msg) {
    if (!msg.animations) return;
    for (const anim of msg.animations) {
        startTween(
            anim.id,
            anim.target,
            anim.duration || 1.0,
            anim.easing || 'ease-in-out',
            entityMeshes
        );
    }
}

function handleTimeline(msg) {
    if (!msg.steps) return;
    for (const step of msg.steps) {
        const delay = (step.at || 0) * 1000;
        setTimeout(() => {
            handleAnimate({ animations: [step.animate] });
        }, delay);
    }
}

// ── Render Loop ─────────────────────────────────────────────
function animate() {
    requestAnimationFrame(animate);
    controls.update();
    updateTweens(entityMeshes);
    renderer.render(scene, camera);
    if (window._labelRenderer) {
        window._labelRenderer.render(scene, camera);
    }
}

// ── Bootstrap ───────────────────────────────────────────────
initScene();
connectWebSocket();
animate();
