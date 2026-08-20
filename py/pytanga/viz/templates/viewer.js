// Tanga Viewer — Main entry point
// Sets up Three.js scene, WebSocket client, entity registry, and render loop.
// All dimension‑specific logic lives in view_mode.js.

window.__tanga_ready = true;

import * as THREE from 'three';
import { CSS2DRenderer } from 'three/addons/renderers/CSS2DRenderer.js';
import { setupControls } from './controls.js';
import { createEntityMesh, removeEntityMesh, updateEntityMesh } from './renderers/factory.js';
import { buildSceneObject, buildOverlay, removeObject, applyTransformToObject } from './scene-builder.js';
import { startTween, updateTweens, cancelTween } from './animator.js';
import { setWebSocket, handleControlsDefine, handleControlsClear } from './controls-panel.js';
import { attachGroup, detachGroup, detachAll } from './controls-attached.js';
import { createCamera, configureControls, fitCamera, handleResize, switchToCamera } from './view_mode.js';
import { updateLineResolutions, applyStyleUpdate } from './renderers/utils.js';
import { initInteraction, registerInteractive, unregisterInteractive, clearAllInteractive, setWebSocket as setInteractionWebSocket, setSpaceDim } from './interaction.js';

// ── State ───────────────────────────────────────────────────
const sceneObjects = new Map();   // id → {obj, mesh, data, layer, el?}

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

// Frontend build hash injected into the served HTML; compared against the
// value the backend advertises over the WebSocket handshake to detect a
// stale, cached copy of the viewer.
const _frontendVersion =
    (typeof window !== 'undefined' && window.__tanga_frontend_version) || null;

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
        window.innerWidth / window.innerHeight
    );

    // Lights
    scene.add(new THREE.AmbientLight(0xffffff, 0.5));
    const d1 = new THREE.DirectionalLight(0xffffff, 0.8);
    d1.position.set(10, 20, 10);
    scene.add(d1);
    const d2 = new THREE.DirectionalLight(0xffffff, 0.3);
    d2.position.set(-5, -2, -8);
    scene.add(d2);

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

    // Observe the render container so container/iframe resizes (and the
    // initial layout settling) recompute the camera, not just window resizes.
    if (typeof ResizeObserver !== 'undefined' && window._viewerContainer) {
        window._viewerResizeObserver = new ResizeObserver(() => onResize());
        window._viewerResizeObserver.observe(window._viewerContainer);
    }

}

function onResize() {
    const container = window._viewerContainer;
    const width = container?.clientWidth || window.innerWidth;
    const height = container?.clientHeight || window.innerHeight;
    handleResize(
        camera,
        renderer,
        window._labelRenderer,
        sceneConfig?.space_dim || 3,
        width,
        height
    );
    updateLineResolutions();
}

// ── WebSocket Client ────────────────────────────────────────
let _reconnectAttempts = 0;
let _savedTitle = document.title || 'Tanga Viewer';

// Auto-reconnect: retry at a fixed 2s interval for the first minute after a
// disconnect, then stop (manual reconnect via the button remains available).
const _RECONNECT_INTERVAL_MS = 2000;
const _RECONNECT_WINDOW_MS = 60000;
let _reconnectDeadline = 0;  // timestamp when auto-reconnect should stop (0 = none)

// Single-flight guard: increment on teardown so stale onopen/onclose
// handlers from superseded sockets are ignored.
let _wsGeneration = 0;

// ── Connection diagnostics ──────────────────────────────────
// Detailed console logging for the connection/reconnection flow, so the
// transcript can be correlated with the backend's `WS connect`/`WS ready`/
// `WS disconnect` log lines.  Every WebSocket state transition, sent message,
// and received message is logged with a monotonic timestamp and the
// browser/viewer/scene identity.
function _log(phase, detail) {
    const t = (typeof performance !== 'undefined' && performance.now)
        ? (performance.now() / 1000).toFixed(3) : '0';
    const parts = ['[tanga:' + phase + ' t=' + t + ']'];
    if (_browserId) parts.push('id=' + _browserId);
    if (_viewerName) parts.push('viewer=' + _viewerName);
    if (_myScene) parts.push('scene=' + _myScene);
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
        setWebSocket(ws);
        setInteractionWebSocket(ws);
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
        _reconnectAttempts = 0;
        _reconnectDeadline = 0;  // connected — clear any pending reconnect window
        hideReconnectButton();
        updateStatusIndicator('connected');
        document.title = _savedTitle;
        const readyPayload = { type: 'ready', scene: _myScene };
        if (_browserId) readyPayload.browser_id = _browserId;
        if (_viewerName) readyPayload.viewer_name = _viewerName;
        if (pageToken) readyPayload.page_token = pageToken;
        _log('ws-send', 'type=ready scene=' + (_myScene || '') + ' token=' + (pageToken || 'none'));
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
        // _log('ws-msg', 'type=' + (msg.type || 'unknown') + ' size=' + event.data.length);
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

function setStatus(cls) {
    const el = document.getElementById('status');
    if (!el) return;
    el.className = cls;
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
    // mode: 'reconnect' (normal reconnect) or 'page-reload' (full refresh)
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

// ── Scene Config ─────────────────────────────────────────────
function applySceneConfig(config) {
    sceneConfig = config;
    const spaceDim = config.space_dim || 3;

    if (config.background_color) {
        scene.background = new THREE.Color(config.background_color);
    }

    // Camera — switchToCamera handles "2d" / "3d" / default-2D camera types.
    // Must happen before user-configured position/target overrides are
    // applied because switchToCamera may replace the camera object.
    camera = switchToCamera(camera, controls, spaceDim, config.camera);

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

    // Tell the interaction module about the current space dimension
    setSpaceDim(spaceDim);

    // Recompute the camera from the real container size now that the camera
    // type has been switched — the switch itself may have used a stale
    // window.innerWidth/innerHeight (e.g. before the page finished laying out).
    onResize();

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
    fitCamera(sceneObjects, camera, controls, sceneConfig?.space_dim || 3);
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

// ── Message Handler ─────────────────────────────────────────
function _forMyScene(msg) {
    return !msg.scene || msg.scene === _myScene;
}

async function handleMessage(msg) {
    if (msg.type === 'browser_id') {
        _browserId = msg.browser_id;
        _log('init', 'browser_id=' + msg.browser_id);
        if (msg.frontend_version && _frontendVersion
            && msg.frontend_version !== _frontendVersion) {
            showVersionMismatchBanner(msg.frontend_version, _frontendVersion);
        }
        return;
    }
    if (msg.type === 'navigate') {
        _log('init', 'navigate → scene=' + (msg.scene || ''));
        const target = msg.scene || '';
        let newUrl = target ? '/' + target : '/';
        if (_viewerName) {
            newUrl += '?viewer=' + encodeURIComponent(_viewerName);
        }
        window.location.href = newUrl;
        return;
    }
    if (msg.type === 'scene_list') {
        _log('init', 'scene_list scenes=' + JSON.stringify(msg.scenes || []));
        _availableScenes = msg.scenes || [];
        return;
    }

    if (msg.type === 'scene_config' || msg.type === 'scene_update' || msg.type === 'object_update') {
        if (!_forMyScene(msg)) return;
    }
    if (msg.type === 'controls_define' || msg.type === 'controls_clear') {
        if (!_forMyScene(msg)) return;
    }

    if (msg.type === 'clear_all') {
        _log('init', 'clear_all → resetting scene (objects=' + sceneObjects.size + ')');
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
    } else if (msg.type === 'scene_config') {
        _log('init', 'scene_config name=' + (msg.name || '') + ' space_dim=' + msg.space_dim);
        applySceneConfig(msg);
    } else if (msg.type === 'scene_update') {
        _log('init', 'scene_update objects=' + (msg.objects ? msg.objects.length : 0) + ' removed=' + (msg.removed ? msg.removed.length : 0));
        if (msg.removed) {
            for (const id of msg.removed) {
                removeSceneObject(id);
            }
        }
        if (msg.objects) {
            for (const obj of msg.objects) {
                await upsertObject(obj);
            }
        }
        if (msg.fit_camera) {
            fitCameraToScene();
        }
        // Acknowledge full-state sync so the server only starts streaming
        // incremental updates after this tab has rebuilt the scene (this
        // closes the reconnect/init race).
        if (ws && ws.readyState === WebSocket.OPEN) {
            _log('ws-send', 'type=scene_synced browser_id=' + _browserId);
            ws.send(JSON.stringify({ type: 'scene_synced', browser_id: _browserId }));
        }
    } else if (msg.type === 'object_update') {
        // _log('init', 'object_update patches=' + (msg.patches ? msg.patches.length : 0) + ' removed=' + (msg.removed ? msg.removed.length : 0));
        if (msg.removed) {
            for (const id of msg.removed) {
                removeSceneObject(id);
            }
        }
        if (msg.patches) {
            for (const patch of msg.patches) {
                await applyObjectPatch(patch);
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
        _log('init', 'controls_define controls=' + (msg.controls ? msg.controls.length : 0) + ' groups=' + (msg.groups ? msg.groups.length : 0));
        handleControlsDefine(msg);
        const controls2 = msg.controls || [];
        const groups = msg.groups || [];
        for (const g of groups) {
            if (g.parentId) {
                attachGroup(g, controls2, sceneObjects);
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
        // Clear the temporary screenshot size so the container returns to its
        // CSS 100%×100% layout before recomputing the camera from its real size.
        if (window._viewerContainer) {
            window._viewerContainer.style.width = '';
            window._viewerContainer.style.height = '';
        }
        updateLineResolutions();
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
        // Reuse the shared resize path so a 2D ortho frustum is recomputed for
        // the capture size (not just the perspective aspect).
        handleResize(camera, renderer, window._labelRenderer, sceneConfig?.space_dim || 3, w, h);
        updateLineResolutions();
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
        if (old.layer === 'scene' && old.obj) {
            // removeEntityMesh also detaches nested CSS2D label elements, so
            // rebuilding a scene object (e.g. axes) leaves no ghost labels.
            removeEntityMesh(old.obj);
        } else if (old.obj && old.obj.removeFromParent) {
            old.obj.removeFromParent();
        }
        if (old.el) old.el.remove();
        sceneObjects.delete(msg.id);
    }
    if (msg.layer === 'scene') {
        const entry = await buildSceneObject(msg, scene, sceneObjects);
        if (entry && msg.interaction) {
            registerInteractive(msg.id, entry.obj, msg.interaction);
        }
    } else if (msg.layer === 'overlay') {
        if (msg.kind === 'annotation') {
            if (!msg.text) return;
            renderAnnotation(msg.text, msg.style || null);
            if (annotationPanel) {
                sceneObjects.set(msg.id, { obj: null, mesh: null, data: { ...msg }, el: annotationPanel, layer: 'overlay' });
            }
            return;
        }

        buildOverlay(msg, scene, sceneObjects);
    }
}

function removeSceneObject(id) {
    unregisterInteractive(id);
    const entry = sceneObjects.get(id);
    if (entry && entry.layer === 'scene' && entry.obj && entry.obj.userData._attachedGroups) {
        for (const groupId of entry.obj.userData._attachedGroups) {
            detachGroup(groupId);
        }
    }
    removeObject(id, sceneObjects);
    cancelTween(id);
}

async function applyObjectPatch(patch) {
    const id = patch.id;
    const aspect = patch.aspect;
    const value = patch.value || {};

    if (aspect === 'full') {
        await upsertObject(value);
        return;
    }

    const entry = sceneObjects.get(id);
    if (!entry) return;

    if (aspect === 'content') {
        await updateEntityContent(id, value);
        return;
    }

    if (aspect === 'transform') {
        if (entry.obj) applyTransformToObject(entry.obj, value);
        return;
    }

    if (aspect === 'style') {
        if (value.style && entry.obj) {
            const prev = entry.data || {};
            entry.data = { ...prev, style: { ...(prev.style || {}), ...value.style } };
            if (entry.obj.isObject3D) applyStyleUpdate(entry.obj, entry.data);
        }
        return;
    }
}

async function updateEntityContent(id, content) {
    const entry = sceneObjects.get(id);
    if (!entry || entry.layer !== 'scene' || !entry.mesh) return;
    const prev = entry.data || {};

    if (updateEntityMesh(entry.mesh, content, prev)) {
        entry.data = { ...prev, ...content };
        return;
    }

    // Structural change — rebuild the mesh in place, keeping the node
    // wrapper (transform) and parent intact.
    const newMesh = await createEntityMesh({ ...prev, ...content });
    if (!newMesh) return;

    if (entry.obj === entry.mesh) {
        // Identity transform: the mesh IS the node. Re-attach any labels
        // that were children of the old mesh.
        const attachedLabels = (entry.obj.userData._labels || []).slice();
        const parent = entry.obj.parent;
        removeEntityMesh(entry.obj);
        entry.obj = newMesh;
        entry.mesh = newMesh;
        newMesh.userData.parentId = prev.parent_id || null;
        newMesh.userData._labels = [];
        if (parent) parent.add(newMesh); else scene.add(newMesh);
        for (const lblId of attachedLabels) {
            const lblEntry = sceneObjects.get(lblId);
            if (lblEntry && lblEntry.obj) {
                newMesh.add(lblEntry.obj);
                newMesh.userData._labels.push(lblId);
            }
        }
    } else {
        // Wrapped: replace the child mesh inside the wrapper Group.
        removeEntityMesh(entry.mesh);
        entry.obj.add(newMesh);
        entry.mesh = newMesh;
    }
    entry.data = { ...prev, ...content };
    if (prev.interaction) {
        registerInteractive(id, entry.obj, prev.interaction);
    }
}

function handleAnimate(msg) {
    if (!msg.animations) return;
    for (const anim of msg.animations) {
        startTween(
            anim.id,
            anim.target,
            anim.duration || 1.0,
            anim.easing || 'ease-in-out',
            sceneObjects
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
    updateTweens(sceneObjects);
    renderer.render(scene, camera);
    if (window._labelRenderer) {
        window._labelRenderer.render(scene, camera);
    }
}

// ── Bootstrap ───────────────────────────────────────────────
initScene();
connectWebSocket();
animate();
