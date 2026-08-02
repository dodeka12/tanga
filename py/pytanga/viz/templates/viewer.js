// Tanga 3D Viewer — Main entry point
// Sets up Three.js scene, WebSocket client, entity registry, and render loop.

window.__tanga_ready = true;

import * as THREE from 'three';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { setupControls } from './controls.js';
import { createEntityMesh, removeEntityMesh } from './renderers/factory.js';
import { startTween, updateTweens, cancelTween } from './animator.js';
import { setWebSocket, handleControlsDefine, handleControlsClear } from './controls-panel.js';
import { attachGroup, detachGroup, detachAll } from './controls-attached.js';

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
// Scene name from URL path: "/" → "", "/scene1" → "scene1"
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
    // ── Viewer container ── all DOM elements go inside this div
    // so we can resize it for capture without affecting the viewport.
    window._viewerContainer = document.getElementById('viewer-container');

    // WebGL Renderer — preserveDrawingBuffer:true so html2canvas can
    // read the framebuffer for DOM overlay capture.
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.shadowMap.enabled = false;
    window._viewerContainer.appendChild(renderer.domElement);

    // CSS2D Renderer — for entity labels
    window._labelRenderer = new CSS2DRenderer();
    window._labelRenderer.setSize(window.innerWidth, window.innerHeight);
    window._labelRenderer.domElement.style.position = 'absolute';
    window._labelRenderer.domElement.style.top = '0px';
    window._labelRenderer.domElement.style.pointerEvents = 'none';
    window._viewerContainer.appendChild(window._labelRenderer.domElement);

    // Scene
    scene = new THREE.Scene();
    scene.fog = null;

    // Camera (defaults, overridden by scene_config)
    camera = new THREE.PerspectiveCamera(50, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.set(8, 6, 10);
    camera.lookAt(0, 0, 0);

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

    // Controls
    controls = setupControls(camera, renderer);
    window.addEventListener('resize', onResize);

    // ── Ctrl+S screenshot shortcut ──────────────────────────
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

function onResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    if (window._labelRenderer) {
        window._labelRenderer.setSize(window.innerWidth, window.innerHeight);
    }
    // Restore container to full viewport
    if (window._viewerContainer) {
        window._viewerContainer.style.width = '100%';
        window._viewerContainer.style.height = '100%';
    }
}

// ── WebSocket Client ────────────────────────────────────────
let _reconnectAttempts = 0;
let _savedTitle = document.title || 'Tanga 3D Viewer';

function connectWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${location.host}/ws`;

    _reconnectAttempts++;
    console.log('[tanga] connecting to ' + url + ' (attempt ' + _reconnectAttempts + ')');
    updateStatusIndicator('connecting', _reconnectAttempts);
    document.title = 'Connecting… — ' + _savedTitle;

    ws = new WebSocket(url);

    ws.onopen = () => {
        console.log('[tanga] connected to ' + url);
        setStatus('connected');
        setWebSocket(ws);
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
        _reconnectAttempts = 0;
        updateStatusIndicator('connected');
        document.title = _savedTitle;
        // Send ready with scene name, optional browser_id, and viewer_name
        const readyPayload = { type: 'ready', scene: _myScene };
        if (_browserId) readyPayload.browser_id = _browserId;
        if (_viewerName) readyPayload.viewer_name = _viewerName;
        ws.send(JSON.stringify(readyPayload));
    };

    ws.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            handleMessage(msg);
        } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
        }
    };

    ws.onclose = (event) => {
        console.warn('[tanga] disconnected (code ' + event.code + '), retrying in 800ms');
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

/**
 * Update the status dot and optional attempt counter label.
 */
function updateStatusIndicator(state, attempts) {
    const el = document.getElementById('status');
    if (!el) return;
    el.className = state === 'connected' ? 'connected' : 'disconnected';

    // Show attempt count as a small label next to the dot
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
    if (config.background_color) {
        scene.background = new THREE.Color(config.background_color);
    }
    const extent = config.space_extent || 10;

    // Grid
    if (window._gridHelper) {
        scene.remove(window._gridHelper);
        window._gridHelper.geometry.dispose();
        window._gridHelper.material.dispose();
    }
    if (config.show_grid !== false) {
        const gs = extent * 2;
        window._gridHelper = new THREE.GridHelper(gs, Math.max(gs, 20), 0x444466, 0x222244);
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

    // Camera
    const cc = config.camera;
    if (cc) {
        if (cc.position) camera.position.set(cc.position[0], cc.position[1], cc.position[2]);
        if (cc.target) controls.target.set(cc.target[0], cc.target[1], cc.target[2]);
        if (cc.fov) { camera.fov = cc.fov; camera.updateProjectionMatrix(); }
        if (cc.near) { camera.near = cc.near; camera.updateProjectionMatrix(); }
        if (cc.far) { camera.far = cc.far; camera.updateProjectionMatrix(); }
        controls.update();
    }

    // ── Title ──
    if (config.title !== undefined) {
        renderTitle(config.title);
    }

    // ── Annotation (from scene_config, no style — uses defaults) ──
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
    titleElement.textContent = titleText;
}

// ── Annotation Panel ──────────────────────────────────────────
let annotationPanel = null;

function renderAnnotation(mdText, styleData) {
    removeAnnotation();

    const s = styleData || {};

    const container = document.createElement('div');

    // Render markdown to HTML
    if (typeof marked !== 'undefined') {
        container.innerHTML = marked.parse(mdText);
    } else {
        container.textContent = mdText;
    }

    // Render KaTeX formulas
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

    // Apply style properties from the overlay message, falling back to defaults
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

    // Inject scoped CSS for rendered content
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
        .annotation-container .katex { font-size: 1.05em; }
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
    if (entityMeshes.size === 0) return;
    const box = new THREE.Box3();
    entityMeshes.forEach(m => box.expandByObject(m));
    const center = new THREE.Vector3();
    box.getCenter(center);
    const size = new THREE.Vector3();
    box.getSize(size);
    const maxDim = Math.max(size.x, size.y, size.z, 1);
    const distance = maxDim * 1.5 + 2;

    const cc = sceneConfig?.camera;
    if (!cc || !cc.target) controls.target.copy(center);
    if (!cc || !cc.position) {
        camera.position.set(center.x + distance * 0.6, center.y + distance * 0.5, center.z + distance * 0.7);
        camera.lookAt(controls.target);
    }
    if (!cc || !cc.near) camera.near = Math.max(0.01, distance * 0.001);
    if (!cc || !cc.far) camera.far = distance * 10;
    camera.updateProjectionMatrix();
    controls.update();
}

// ── Helper: rotate mesh to point along a direction vector ───
function rotationFromDirection(dx, dy, dz) {
    const direction = new THREE.Vector3(dx, dy, dz).normalize();
    const quaternion = new THREE.Quaternion();
    quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction);
    return quaternion;
}

// ── In-place entity updates for frame streaming ─────────────
function inPlaceUpdate(ent) {
    const mesh = entityMeshes.get(ent.id);
    if (!mesh) return false;

    const previous = entityData.get(ent.id);

    // Position update
    if (ent.position) {
        mesh.position.set(ent.position[0], ent.position[1], ent.position[2]);
    }

    // Direction/vector update (for arrows, lines, etc.)
    if (ent.vector || ent.direction) {
        const vec = ent.vector || ent.direction;
        const origin = ent.origin || [0, 0, 0];
        mesh.position.set(origin[0], origin[1], origin[2]);
        mesh.setRotationFromQuaternion(rotationFromDirection(vec[0], vec[1], vec[2]));
    }

    // Center update (for spheres, circles)
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

    // Check if structural change requires full rebuild
    if (ent.radius !== undefined && ent.radius !== previous?.radius) return false;
    if (ent.extent !== undefined && ent.extent !== previous?.extent) return false;
    if (ent.length !== undefined && ent.length !== previous?.length) return false;
    if (ent.kind !== undefined && ent.kind !== previous?.kind) return false;

    return true;
}

// ── Message Handler ─────────────────────────────────────────
/** Attach browser_id to an outgoing message payload. */
function _withBrowserId(payload) {
    if (_browserId) payload.browser_id = _browserId;
    return payload;
}

/** Check if a scene-scoped message targets this browser's scene. */
function _forMyScene(msg) {
    // If no scene field, or scene matches ours, it's for us
    return !msg.scene || msg.scene === _myScene;
}

function handleMessage(msg) {
    // ── Global messages (always processed) ──
    if (msg.type === 'browser_id') {
        _browserId = msg.browser_id;
        console.log('[tanga] browser_id = ' + _browserId);
        if (_viewerName) console.log('[tanga] viewer_name = ' + _viewerName);
        return;
    }
    if (msg.type === 'navigate') {
        const target = msg.scene || '';
        let newUrl = target ? '/' + target : '/';
        if (_viewerName) {
            newUrl += '?viewer=' + encodeURIComponent(_viewerName);
        }
        console.log('[tanga] navigating to ' + newUrl);
        window.location.href = newUrl;
        return;
    }
    if (msg.type === 'scene_list') {
        _availableScenes = msg.scenes || [];
        console.log('[tanga] available scenes: ' + _availableScenes.join(', '));
        return;
    }

    // ── Scene-scoped messages: filter by scene ──
    if (msg.type === 'scene_config' || msg.type === 'scene_update') {
        if (!_forMyScene(msg)) return;
    }
    if (msg.type === 'controls_define' || msg.type === 'controls_clear') {
        if (!_forMyScene(msg)) return;
    }

    if (msg.type === 'clear_all') {
        // Remove all scene objects (handles reconnect with a new server session)
        entityMeshes.forEach((mesh) => removeEntityMesh(mesh));
        entityMeshes.clear();
        entityData.clear();
        labelObjects.forEach((lbl) => {
            lbl.removeFromParent();
            if (lbl.element) lbl.element.remove();
        });
        labelObjects.clear();
        sceneObjects.forEach((obj) => {
            if (obj.obj && obj.obj.removeFromParent) obj.obj.removeFromParent();
            if (obj.el) obj.el.remove();
        });
        sceneObjects.clear();
        removeAnnotation();
        if (titleElement) {
            titleElement.remove();
            titleElement = null;
        }
        handleControlsClear();
        detachAll();
        cameraPositioned = false;
    } else if (msg.type === 'scene_config') {
        applySceneConfig(msg);
    } else if (msg.type === 'scene_update') {
        if (msg.removed) {
            for (const id of msg.removed) {
                // Clean up from all registries
                const mesh = entityMeshes.get(id);
                if (mesh) {
                    // Clean up attached control groups before removing the mesh
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
                    // In-place update: preserves attached labels, avoids mesh recreation
                    updateEntity(obj);
                } else {
                    upsertObject(obj);
                }
            }
        }
        // Backward compat: old format with separate entities/labels arrays
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
        if (!cameraPositioned && entityMeshes.size > 0) {
            const cc = sceneConfig?.camera;
            if (!cc || (!cc.position && !cc.target)) fitCameraToScene();
            cameraPositioned = true;
        }
    } else if (msg.type === 'animate') {
        handleAnimate(msg);
    } else if (msg.type === 'timeline') {
        handleTimeline(msg);
    } else if (msg.type === 'screenshot') {
        // Programmatic screenshot request from Python.
        // Resize the renderer + CSS2D renderer to target dimensions
        // with pixelRatio=1 for exact-pixel output.
        // Hide status indicator during capture
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
        // Force a render at the current size
        renderer.render(scene, camera);
        if (window._labelRenderer) {
            window._labelRenderer.render(scene, camera);
        }
        const w = renderer.domElement.width;
        const h = renderer.domElement.height;

        // Capture container contents at exact renderer size.
        // html2canvas (with preserveDrawingBuffer=true) renders the
        // WebGL canvas + labels + title + annotation in one pass.
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
            // Fallback: WebGL only
            ws.send(JSON.stringify({
                type: 'screenshot:data',
                request_id: msg.request_id,
                data: renderer.domElement.toDataURL('image/png'),
            }));
        }
    } else if (msg.type === 'controls_define') {
        handleControlsDefine(msg);
        // Route attached groups to the CSS2DRenderer module
        const controls = msg.controls || [];
        const groups = msg.groups || [];
        for (const g of groups) {
            if (g.parentId) {
                attachGroup(g, controls, entityMeshes);
            }
        }
    } else if (msg.type === 'controls_clear') {
        handleControlsClear();
        detachAll();
    } else if (msg.type === 'restore_size') {
        // Restore renderer to fill the browser window after capture
        if (_savedPixelRatio !== null) {
            renderer.setPixelRatio(_savedPixelRatio);
            _savedPixelRatio = null;
        }
        // Restore status indicator
        const statusEl2 = document.getElementById('status');
        if (statusEl2) {
            statusEl2.style.display = _savedStatusDisplay || 'block';
            _savedStatusDisplay = null;
        }
        onResize();
    }
}

// ── Unified Object Management ──────────────────────────────

function upsertObject(msg) {
    // Remove previous instance
    const old = sceneObjects.get(msg.id);
    if (old) {
        if (old.obj && old.obj.removeFromParent) old.obj.removeFromParent();
        if (old.el) old.el.remove();
        sceneObjects.delete(msg.id);
    }
    // Also clean legacy maps
    entityMeshes.delete(msg.id);
    entityData.delete(msg.id);
    labelObjects.delete(msg.id);

    if (msg.layer === 'scene') {
        const mesh = createEntityMesh(msg);
        if (mesh) {
            scene.add(mesh);
            sceneObjects.set(msg.id, { obj: mesh, layer: 'scene' });
            entityMeshes.set(msg.id, mesh);
            entityData.set(msg.id, { ...msg });
        }
    } else if (msg.layer === 'overlay') {
        // Annotations handle everything themselves (fixed-position, appended to body)
        if (msg.kind === 'annotation') {
            if (!msg.text) return;
            renderAnnotation(msg.text, msg.style || null);
            // Track the panel element in sceneObjects so it gets cleaned up on removal
            if (annotationPanel) {
                sceneObjects.set(msg.id, { obj: null, el: annotationPanel, layer: 'overlay' });
            }
            return;
        }

        const el = buildOverlayElement(msg);
        if (!el) return;

        let css2d = null;
        if (msg.parentId) {
            // Wrap label in a container. CSS2DRenderer positions the OUTER
            // (container) element. We apply offset_2d and alignment on the
            // INNER element (the label div from buildOverlayElement).
            const container = document.createElement('div');
            container.appendChild(el);
            css2d = new CSS2DObject(container);
            const pos = msg.position || [0, 0, 0];
            css2d.position.set(pos[0], pos[1], pos[2]);
            // CSS2DRenderer centers the container: translate(-50%,-50%) translate(Xpx, Ypx)
            // We counter that centering with align and add pixel offset on el:
            const off2d = msg.style?.offset_2d || [0, 0];
            const align = msg.style?.align || [0.5, 0.5];
            const tx = (0.5 - align[0]) * 100;
            const ty = (0.5 - align[1]) * 100;
            el.style.transform = `translate(${off2d[0]}px, ${off2d[1]}px) translate(${tx}%, ${ty}%)`;
            const parentObj = sceneObjects.get(msg.parentId);
            if (parentObj && parentObj.obj) {
                parentObj.obj.add(css2d);
                // Track label on parent so it can be re-attached after rebuild
                parentObj.obj.userData._labels = parentObj.obj.userData._labels || [];
                parentObj.obj.userData._labels.push(msg.id);
                css2d.userData._parentId = msg.parentId;
            } else {
                scene.add(css2d);
            }
            labelObjects.set(msg.id, css2d);
        } else {
            // Fixed positioning: absolute DOM
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
            // Render KaTeX formulas in label text ($...$ and $$...$$)
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
            // Delegate to the shared renderAnnotation function with style
            renderAnnotation(msg.text, msg.style || null);
            return annotationPanel;  // return the existing panel element
        }
        default:
            console.warn('Unknown overlay kind: ' + msg.kind);
            return null;
    }
}

// ── Label Management (backward compat) ─────────────────────

function upsertLabel(lbl) {
    if (!lbl.text) return;

    // Remove existing label with this id
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

    // Render KaTeX formulas in label text ($...$ and $$...$$)
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
        // Track label on parent so it can be re-attached after rebuild
        parentMesh.userData._labels = parentMesh.userData._labels || [];
        parentMesh.userData._labels.push(lbl.id);
        labelObj.userData._parentId = lbl.parentId;
    } else {
        scene.add(labelObj);
    }

    labelObjects.set(lbl.id, labelObj);
}

function updateEntity(ent) {
    const id = ent.id;
    const existing = entityData.get(id);

    if (!existing) {
        const mesh = createEntityMesh(ent);
        if (mesh) {
            scene.add(mesh);
            entityMeshes.set(id, mesh);
        }
        entityData.set(id, { ...ent });
        return;
    }

    // Try in-place update first (for frame streaming performance)
    if (inPlaceUpdate(ent)) {
        // Update stored data with merged properties
        entityData.set(id, { ...existing, ...ent });
        return;
    }

    // Full rebuild for structural changes (radius, extent, kind change)
    const oldMesh = entityMeshes.get(id);
    const attachedLabels = oldMesh ? (oldMesh.userData._labels || []).slice() : [];
    if (oldMesh) removeEntityMesh(oldMesh);
    entityMeshes.delete(id);
    const mesh = createEntityMesh({ ...existing, ...ent });
    if (mesh) {
        scene.add(mesh);
        entityMeshes.set(id, mesh);
        // Re-attach labels that were orphaned by the old mesh removal
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
        const delay = (step.at || 0) * 1000; // seconds → milliseconds
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