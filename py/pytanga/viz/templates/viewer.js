// Tanga Viewer — Main entry point (bootstrap).
// Owns the WebSocket connection, browser identity, reconnect/status UI, and
// the global screenshot + animation-stop bindings.  Scene rendering is
// delegated to a single `ThreeJsView` (see views/three-view.js).

window.__tanga_ready = true;

import { applyOverlayAnchor } from './views/three-view.js';
import { buildViewTree, collectSceneRoutes, collectViewByIds } from './views/build.js';
import { getOverlay } from './overlay.js';
import { applyControlValue } from './controls-panel.js';
import { setWebSocket as setEventsWebSocket } from './events.js';
import {
    handleBannerDefine,
    handleBannerRemove,
    handleBannerClear,
} from './banner.js';
import {
    handleDialogDefine,
    handleDialogRemove,
    handleDialogClear,
} from './dialog.js';
import {
    handleFileBrowserShow,
    handleFileBrowserListing,
    handleFileBrowserClose,
} from './file-browser.js';
import {
    handleEditorDefine,
} from './editor.js';
import { handleThemeDefine } from './themes.js';
import { updateLineResolutions } from './renderers/utils.js';
import { handleResize } from './view_mode.js';

// ── State ───────────────────────────────────────────────────
let ws = null;
let reconnectTimer = null;
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

// Layout mode: `?view=<name>` (param present) → single page showing a split
// layout.  `null` → single-scene mode (existing behaviour).
let _layoutName = (() => {
    const params = new URLSearchParams(window.location.search);
    return params.has('view') ? (params.get('view') || '') : null;
})();
let _layoutRoot = null;
let _sceneRoutes = new Map();  // scene -> {sceneViews, controlViews}
let _viewById = new Map();     // view_id -> ThreeJsView (per-pane camera)
let _globalOverlayViews = [];  // views mounted into the global overlay singleton

// Per-scene browser-side animation stop binding.
let _animationStopConfig = { enabled: false, key: null, modifiers: [] };
// Per-scene browser-side full-server stop binding (opt-in).
let _serverStopConfig = { enabled: false, key: null, modifiers: [] };

// Frontend build hash injected into the served HTML; compared against the
// value the backend advertises over the WebSocket handshake to detect a
// stale, cached copy of the viewer.
const _frontendVersion =
    (typeof window !== 'undefined' && window.__tanga_frontend_version) || null;

// ── Helpers ─────────────────────────────────────────────────
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

function _shortenTitle(text, max = 40) {
    if (!text) return '';
    if (text.length <= max) return text;
    return text.slice(0, max - 1).trimEnd() + '…';
}

function _forMyScene(msg) {
    return !msg.scene || msg.scene === _myScene;
}

function _stopKeyMatches(event, config) {
    if (!config.enabled || !config.key) return false;
    if ((event.key || '').toLowerCase() !== String(config.key).toLowerCase()) {
        return false;
    }
    for (const mod of config.modifiers) {
        switch (mod) {
            case 'ctrl':
                if (!(event.ctrlKey || event.metaKey)) return false;
                break;
            case 'shift':
                if (!event.shiftKey) return false;
                break;
            case 'alt':
                if (!event.altKey) return false;
                break;
            case 'meta':
                if (!event.metaKey) return false;
                break;
            default:
                return false;
        }
    }
    return true;
}

function _handleAnimationStopKey(event) {
    // Scope: full-server stop takes precedence over the per-scene stop.
    const serverMatch = _stopKeyMatches(event, _serverStopConfig);
    const sceneMatch = !serverMatch && _stopKeyMatches(event, _animationStopConfig);
    if (!serverMatch && !sceneMatch) return;
    // Don't hijack keys while the user is editing text.
    const target = event.target;
    if (target && (
        target.tagName === 'INPUT'
        || target.tagName === 'TEXTAREA'
        || target.isContentEditable
    )) return;
    event.preventDefault();
    if (ws && ws.readyState === WebSocket.OPEN) {
        _log('ws-send', 'type=animation_stop scene=' + (_myScene || '')
            + ' scope=' + (serverMatch ? 'server' : 'scene'));
        ws.send(JSON.stringify({
            type: 'animation_stop',
            scene: _myScene,
            scope: serverMatch ? 'server' : 'scene',
            browser_id: _browserId,
        }));
    }
}

// ── WebSocket Client ────────────────────────────────────────
let _reconnectAttempts = 0;
let _savedTitle = document.title || 'Tanga Viewer';

const _RECONNECT_INTERVAL_MS = 2000;
const _RECONNECT_WINDOW_MS = 60000;
let _reconnectDeadline = 0;
let _wsGeneration = 0;

function closeActiveWs() {
    if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
        _log('ws-teardown', 'closing active socket readyState=' + ws.readyState);
        _wsGeneration++;
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
            _wsGeneration++;
            try { ws.close(); } catch (_) {}
            ws = null;
            if (_reconnectDeadline && Date.now() < _reconnectDeadline) {
                connectWebSocket();
            }
        }
    }, _RECONNECT_INTERVAL_MS);

    ws.onopen = () => {
        if (gen !== _wsGeneration) return;
        clearTimeout(connectWatchdog);
        const pageToken = window.__tanga_page_token
            || new URLSearchParams(window.location.search).get('token');
        _log('ws-open', 'attempt=' + _reconnectAttempts + ' token=' + (pageToken || 'none'));
        setStatus('connected');
        setEventsWebSocket(ws);
        _setWsOnAllViews(ws);
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
        _reconnectAttempts = 0;
        _reconnectDeadline = 0;
        hideReconnectButton();
        updateStatusIndicator('connected');
        document.title = _savedTitle;
        const readyPayload = _layoutName !== null
            ? { type: 'ready', layout: _layoutName, scene: '' }
            : { type: 'ready', scene: _myScene };
        if (_browserId) readyPayload.browser_id = _browserId;
        if (_viewerName) readyPayload.viewer_name = _viewerName;
        if (pageToken) readyPayload.page_token = pageToken;
        _log('ws-send', 'type=ready ' + (_layoutName !== null ? ('layout=' + _layoutName) : ('scene=' + (_myScene || ''))) + ' token=' + (pageToken || 'none'));
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
    const url = new URL(window.location.href);
    url.searchParams.set('t', Date.now().toString());
    window.location.replace(url.toString());
}

function showVersionMismatchBanner(serverVersion, clientVersion) {
    if (_versionBannerEl) return;

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

// ── Screenshot ───────────────────────────────────────────────
function handleScreenshot(msg) {
    const active = _activeSceneView();
    if (!active || !active.renderer) return;

    const statusEl = document.getElementById('status');
    if (statusEl) {
        _savedStatusDisplay = statusEl.style.display;
        statusEl.style.display = 'none';
    }

    if (msg.width && msg.height) {
        const w = msg.width, h = msg.height;
        _savedPixelRatio = active.renderer.getPixelRatio();
        active.renderer.setPixelRatio(1);
        handleResize(active.camera, active.renderer, active.labelRenderer, active.sceneConfig?.space_dim || 3, w, h);
        updateLineResolutions();
        if (window._viewerContainer) {
            window._viewerContainer.style.width = w + 'px';
            window._viewerContainer.style.height = h + 'px';
        }
    }
    active.renderer.render(active.scene, active.camera);
    if (active.labelRenderer) {
        active.labelRenderer.render(active.scene, active.camera);
    }
    const w = active.renderer.domElement.width;
    const h = active.renderer.domElement.height;

    const send = (data) => {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'screenshot:data',
                request_id: msg.request_id,
                data,
            }));
        }
    };

    if (typeof html2canvas !== 'undefined') {
        html2canvas(window._viewerContainer, {
            width: w,
            height: h,
            windowWidth: w,
            windowHeight: h,
            backgroundColor: null,
            scale: 1,
        }).then((domCanvas) => {
            send(domCanvas.toDataURL('image/png'));
        }).catch((err) => {
            console.warn('html2canvas failed, falling back to webgl only:', err);
            send(active.renderer.domElement.toDataURL('image/png'));
        });
    } else {
        send(active.renderer.domElement.toDataURL('image/png'));
    }
}

// ── Message Router ───────────────────────────────────────────
async function handleMessage(msg) {
    if (msg.type === 'browser_id') {
        _browserId = msg.browser_id;
        _log('init', 'browser_id=' + msg.browser_id);
        _setBrowserIdOnAllViews(_browserId);
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
    if (msg.type === 'animation_stop_config') {
        if ((msg.scene ?? '') === _myScene) {
            _animationStopConfig = {
                enabled: !!msg.enabled,
                key: msg.key ?? null,
                modifiers: Array.isArray(msg.modifiers) ? msg.modifiers : [],
            };
            _serverStopConfig = {
                enabled: !!msg.server_enabled,
                key: msg.server_key ?? null,
                modifiers: Array.isArray(msg.server_modifiers) ? msg.server_modifiers : [],
            };
            _log('init', 'animation_stop_config enabled=' + _animationStopConfig.enabled
                + ' key=' + _animationStopConfig.key
                + ' modifiers=' + JSON.stringify(_animationStopConfig.modifiers)
                + ' server_enabled=' + _serverStopConfig.enabled
                + ' server_key=' + _serverStopConfig.key
                + ' server_modifiers=' + JSON.stringify(_serverStopConfig.modifiers));
        }
        return;
    }
    if (msg.type === 'screenshot') {
        handleScreenshot(msg);
        return;
    }
    if (msg.type === 'restore_size') {
        const active = _activeSceneView();
        if (active) {
            if (_savedPixelRatio !== null) {
                active.renderer.setPixelRatio(_savedPixelRatio);
                _savedPixelRatio = null;
            }
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
            active.resize();
        }
        return;
    }
    if (msg.type === 'view_layout') {
        _buildLayout(msg);
        return;
    }
    if (msg.type === 'view_camera') {
        const target = _viewById.get(msg.view_id);
        if (target) target.setCamera(msg.camera);
        return;
    }

    if (msg.type === 'theme_define') {
        handleThemeDefine(msg);
        return;
    }

    if (msg.type === 'control_update') {
        applyControlValue(msg.id, msg.value);
        return;
    }

    if (msg.type === 'banner_define' || msg.type === 'banner_remove' || msg.type === 'banner_clear') {
        if (msg.scene === null || msg.scene === undefined) {
            if (msg.type === 'banner_define') handleBannerDefine(msg);
            else if (msg.type === 'banner_remove') handleBannerRemove(msg);
            else handleBannerClear();
            return;
        }
        // scene-scoped banner: fall through to scene routing below.
    }

    if (msg.type === 'dialog_define' || msg.type === 'dialog_remove' || msg.type === 'dialog_clear') {
        if (msg.scene === null || msg.scene === undefined) {
            if (msg.type === 'dialog_define') handleDialogDefine(msg, ws);
            else if (msg.type === 'dialog_remove') handleDialogRemove(msg);
            else handleDialogClear();
            return;
        }
        // scene-scoped dialog: fall through to scene routing below.
    }

    if (msg.type === 'file_browser_show' || msg.type === 'file_browser_listing' || msg.type === 'file_browser_close') {
        if (msg.type === 'file_browser_show') handleFileBrowserShow(msg);
        else if (msg.type === 'file_browser_listing') handleFileBrowserListing(msg);
        else handleFileBrowserClose(msg);
        return;
    }

    if (msg.type === 'editor_define') {
        handleEditorDefine(msg);
        return;
    }

    if (_layoutRoot !== null) {
        await _routeToScene(msg, msg.scene || '');
        return;
    }

    if (msg.type === 'scene_config' || msg.type === 'scene_update' || msg.type === 'object_update') {
        if (!_forMyScene(msg)) return;
    }
    if (msg.type === 'controls_define' || msg.type === 'controls_clear') {
        if (!_forMyScene(msg)) return;
    }
    if (msg.type === 'banner_define' || msg.type === 'banner_remove' || msg.type === 'banner_clear') {
        if (!_forMyScene(msg)) return;
    }
    if (msg.type === 'dialog_define' || msg.type === 'dialog_remove' || msg.type === 'dialog_clear') {
        if (!_forMyScene(msg)) return;
    }

    const active = _activeSceneView();
    if (active) await active.handleMessage(msg);
}

// ── Layout / routing helpers ─────────────────────────────────

function _setWsOnAllViews(ws) {
    for (const route of _sceneRoutes.values()) {
        for (const v of route.sceneViews) v.setWebSocket(ws);
    }
}

function _setBrowserIdOnAllViews(id) {
    for (const route of _sceneRoutes.values()) {
        for (const v of route.sceneViews) v.setBrowserId(id);
    }
}

function _activeSceneView() {
    const route = _sceneRoutes.get(_myScene);
    if (route && route.sceneViews.length) return route.sceneViews[0];
    return null;
}

function _destroyViewTree(view) {
    if (!view) return;
    if (Array.isArray(view.children)) {
        for (const child of [...view.children]) _destroyViewTree(child);
    }
    if (typeof view.destroy === 'function') view.destroy();
}

function _buildLayout(msg) {
    _log('init', 'view_layout name=' + (msg.name || ''));

    // Teardown the previous tree (and its global overlay views) so re-pushes
    // and reconnects don't leak ResizeObservers / DOM nodes.
    if (_layoutRoot) {
        _destroyViewTree(_layoutRoot);
        _layoutRoot.unmount();
    }
    _layoutRoot = null;
    _sceneRoutes = new Map();
    _viewById = new Map();
    const overlay = getOverlay();
    for (const view of _globalOverlayViews) {
        overlay.removeChild(view);
        if (typeof view.destroy === 'function') view.destroy();
    }
    _globalOverlayViews = [];

    _layoutRoot = buildViewTree(msg.root, ws);
    _layoutRoot.el.style.width = '100%';
    _layoutRoot.el.style.height = '100%';
    _layoutRoot.mount(window._viewerContainer);
    _sceneRoutes = collectSceneRoutes(_layoutRoot);
    _viewById = collectViewByIds(_layoutRoot);

    // Track the active scene's title for the document title.
    const active = _activeSceneView();
    if (active) {
        active.on('titlechange', (e) => {
            _savedTitle = _shortenTitle(e.detail.title) || _savedTitle;
            document.title = _savedTitle;
        });
    }

    // Global overlay views (e.g. menus) mount into the shared overlay singleton.
    for (const node of msg.overlay || []) {
        const view = buildViewTree(node, ws);
        view.el.style.position = 'absolute';
        view.el.style.pointerEvents = 'auto';
        applyOverlayAnchor(view.el, view.position || 'bottom-right');
        overlay.addChild(view);
        _globalOverlayViews.push(view);
    }
}

async function _routeToScene(msg, sceneName) {
    if (msg.type === 'clear_all') {
        for (const route of _sceneRoutes.values()) {
            for (const v of route.sceneViews) await v.handleMessage(msg);
        }
        return;
    }
    const route = _sceneRoutes.get(sceneName);
    if (!route) return;
    for (const v of route.sceneViews) await v.handleMessage(msg);
}

// ── Bootstrap ───────────────────────────────────────────────
function init() {
    window._viewerContainer = document.getElementById('viewer-container');

    // The view tree is built lazily when `view_layout` arrives (unified mode).

    // Ctrl+S screenshot shortcut.
    window.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            const active = _activeSceneView();
            if (active && active.renderer) {
                const dataUrl = active.renderer.domElement.toDataURL('image/png');
                const now = new Date();
                const ts = now.toISOString().replace(/[:.]/g, '-').slice(0, 19);
                const link = document.createElement('a');
                link.download = `tanga_${ts}.png`;
                link.href = dataUrl;
                link.click();
            }
        }
    });

    // Global animation-stop keybinding (per-scene config from the server).
    window.addEventListener('keydown', _handleAnimationStopKey);

    connectWebSocket();
    animate();
}

function animate() {
    requestAnimationFrame(animate);
    for (const route of _sceneRoutes.values()) {
        for (const v of route.sceneViews) v.render();
    }
}

init();


