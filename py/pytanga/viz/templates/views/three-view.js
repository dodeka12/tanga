// Tanga Viewer — `ThreeJsView`: renders a single scene inside a View pane.
// Owns its Three.js scene/camera/renderer/controls, the per-scene object
// registry, and the per-scene message handling.  Extracted from viewer.js so
// the same logic can back the single-scene viewer and a split-view pane.

import * as THREE from 'three';
import { CSS2DRenderer } from 'three/addons/renderers/CSS2DRenderer.js';
import { View } from './view.js';
import { BannerView } from './banner-view.js';
import { setupControls } from '../controls.js';
import { createEntityMesh, removeEntityMesh, updateEntityMesh } from '../renderers/factory.js';
import { buildSceneObject, buildOverlay, removeObject, applyTransformToObject } from '../scene-builder.js';
import { startTween, updateTweens, cancelTween } from '../animator.js';
import { handleControlsDefine, handleControlsClear } from '../controls-panel.js';
import { attachGroup, detachGroup, detachAll } from '../controls-attached.js';
import { createCamera, configureControls, fitCamera, handleResize, switchToCamera } from '../view_mode.js';
import { updateLineResolutions, applyStyleUpdate, entityRequiresRebuild } from '../renderers/utils.js';
import { initInteraction, registerInteractive, unregisterInteractive, clearAllInteractive, setSpaceDim, setCamera } from '../interaction.js';

// ── WebGL1 SDF fallback warning banner ──────────────────────
// SDF proxies need GLSL3 + `gl_FragDepth` (WebGL2). On WebGL1 those objects
// are skipped and a single yellow warning banner is shown (mirrors the
// version-mismatch banner pattern in viewer.js).

let _sdfWebGL2WarningShown = false;

function _showSdfWebGL2Warning() {
    if (_sdfWebGL2WarningShown) return;
    _sdfWebGL2WarningShown = true;

    const banner = document.createElement('div');
    banner.style.position = 'fixed';
    banner.style.top = '0';
    banner.style.left = '0';
    banner.style.right = '0';
    banner.style.zIndex = '100001';
    banner.style.background = '#ffc107';
    banner.style.color = '#1a1a2e';
    banner.style.fontFamily = 'sans-serif';
    banner.style.fontSize = '13px';
    banner.style.padding = '10px 16px';
    banner.style.display = 'flex';
    banner.style.alignItems = 'center';
    banner.style.justifyContent = 'center';
    banner.style.gap = '12px';
    banner.style.lineHeight = '1.5';
    banner.style.boxShadow = '0 2px 6px rgba(0, 0, 0, 0.3)';

    const text = document.createElement('span');
    text.textContent = 'SDF objects require WebGL2 — they are hidden in this viewer.';

    const btn = document.createElement('button');
    btn.textContent = 'Dismiss';
    btn.style.padding = '4px 12px';
    btn.style.background = '#1a1a2e';
    btn.style.color = '#ffffff';
    btn.style.border = 'none';
    btn.style.borderRadius = '3px';
    btn.style.cursor = 'pointer';
    btn.style.fontWeight = 'bold';
    btn.onclick = () => banner.remove();

    banner.appendChild(text);
    banner.appendChild(btn);
    document.body.insertBefore(banner, document.body.firstChild);
}

function _applyOverlayAnchor(el, anchor) {
    el.style.top = 'auto';
    el.style.right = 'auto';
    el.style.bottom = 'auto';
    el.style.left = 'auto';
    switch (anchor) {
        case 'top-left':
            el.style.top = '8px';
            el.style.left = '8px';
            break;
        case 'top-right':
            el.style.top = '8px';
            el.style.right = '8px';
            break;
        case 'bottom-left':
            el.style.bottom = '8px';
            el.style.left = '8px';
            break;
        case 'bottom-right':
        default:
            el.style.bottom = '8px';
            el.style.right = '8px';
            break;
    }
}

/** Renders a single named scene; `View` supplies extent + resize observation. */
export class ThreeJsView extends View {
    constructor(sceneName, ws = null, cameraOverride = null, viewId = null) {
        super();
        this.sceneName = sceneName || '';
        this._ws = ws;
        this._cameraOverride = cameraOverride || null;
        this.viewId = viewId || null;
        this._browserId = null;

        this.sceneObjects = new Map(); // id → {obj, mesh, data, layer, el?}
        this.scene = new THREE.Scene();
        this.scene.fog = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.labelRenderer = null;
        this.sceneConfig = null;
        this.cameraPositioned = false;
        this._titleElement = null;
        this._annotationPanel = null;
        this._overlays = [];
        this._banners = new Map();
        this._isWebGL2 = false;

        this.el.classList.add('tanga-three-view');
        this.el.style.position = 'relative';
        this.el.style.overflow = 'hidden';
        this.el.style.width = '100%';
        this.el.style.height = '100%';

        this._initScene();
    }

    // ── context setters ────────────────────────────────────────

    setWebSocket(ws) { this._ws = ws; }
    setBrowserId(id) { this._browserId = id; }

    // ── overlay ─────────────────────────────────────────────────

    /**
     * Mount an overlay view (e.g. a `GroupView`) over the canvas, anchored by
     * its `position` (`top-left`/`top-right`/`bottom-left`/`bottom-right`).
     */
    addOverlay(view) {
        view.mount(this.el);
        const el = view.el;
        el.style.position = 'absolute';
        el.style.zIndex = '20';
        _applyOverlayAnchor(el, view.position || 'bottom-right');
        this._overlays.push(view);
        return view;
    }

    _log(phase, detail) {
        const parts = ['[tanga:' + phase + ']'];
        if (this._browserId) parts.push('id=' + this._browserId);
        if (this.sceneName) parts.push('scene=' + this.sceneName);
        if (detail) parts.push(detail);
        console.log(parts.join(' '));
    }

    // ── scene setup ────────────────────────────────────────────

    _initScene() {
        let webglOk = true;
        try {
            this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
            this.renderer.setPixelRatio(window.devicePixelRatio);
            this.renderer.setSize(this.width || window.innerWidth, this.height || window.innerHeight);
            this.renderer.shadowMap.enabled = false;
            this.el.appendChild(this.renderer.domElement);
            this._isWebGL2 = !!this.renderer.capabilities.isWebGL2;
        } catch (e) {
            console.warn('WebGL renderer failed — falling back to headless mode:', e.message);
            webglOk = false;
            this.renderer = null;
        }

        try {
            this.labelRenderer = new CSS2DRenderer();
            this.labelRenderer.setSize(this.width || window.innerWidth, this.height || window.innerHeight);
            this.labelRenderer.domElement.style.position = 'absolute';
            this.labelRenderer.domElement.style.top = '0px';
            this.labelRenderer.domElement.style.pointerEvents = 'none';
            this.el.appendChild(this.labelRenderer.domElement);
        } catch (e) {
            this.labelRenderer = null;
        }

        this.camera = createCamera(
            this.sceneConfig?.space_dim || 3,
            (this.width || window.innerWidth) / Math.max(1, this.height || window.innerHeight)
        );

        this._addDefaultLights();

        if (webglOk && this.renderer) {
            this.controls = setupControls(this.camera, this.renderer);
            initInteraction(this.camera, this.renderer.domElement, this.controls, this._ws);
        }
    }

    _addDefaultLights() {
        this.scene.add(new THREE.AmbientLight(0xffffff, 0.5));
        const d1 = new THREE.DirectionalLight(0xffffff, 0.8);
        d1.position.set(10, 20, 10);
        this.scene.add(d1);
        const d2 = new THREE.DirectionalLight(0xffffff, 0.3);
        d2.position.set(-5, -2, -8);
        this.scene.add(d2);
    }

    // ── sizing / render ────────────────────────────────────────

    _onExtentChanged() { this.resize(); }

    resize() {
        const width = this.width || window.innerWidth;
        const height = this.height || window.innerHeight;
        if (this.camera) {
            handleResize(this.camera, this.renderer, this.labelRenderer, this.sceneConfig?.space_dim || 3, width, height);
        }
        updateLineResolutions();
    }

    fitCamera() {
        if (!this.camera) return;
        fitCamera(this.sceneObjects, this.camera, this.controls, this.sceneConfig?.space_dim || 3);
    }

    render() {
        if (!this.renderer || !this.camera) return;
        if (this.controls) this.controls.update();
        updateTweens(this.sceneObjects);
        this.renderer.render(this.scene, this.camera);
        if (this.labelRenderer) this.labelRenderer.render(this.scene, this.camera);
    }

    clearAll() {
        this._log('init', 'clear_all → resetting scene (objects=' + this.sceneObjects.size + ')');
        while (this.scene.children.length > 0) {
            const child = this.scene.children[0];
            this.scene.remove(child);
            if (child.geometry) child.geometry.dispose();
            if (child.material) {
                if (Array.isArray(child.material)) {
                    child.material.forEach((m) => m.dispose());
                } else {
                    child.material.dispose();
                }
            }
        }
        if (this.labelRenderer && this.labelRenderer.domElement) {
            this.labelRenderer.domElement.innerHTML = '';
        }
        clearAllInteractive();
        this.sceneObjects.clear();
        this._removeAnnotation();
        if (this._titleElement) {
            this._titleElement.remove();
            this._titleElement = null;
        }
        handleControlsClear();
        detachAll();
        this._clearBanners();
        this.cameraPositioned = false;
        this._addDefaultLights();
    }

    // ── scene config / overlays ────────────────────────────────

    _applySceneConfig(config) {
        this.sceneConfig = config;
        const spaceDim = config.space_dim || 3;
        // A per-pane camera override (SceneView(scene, camera=…)) wins over the
        // scene's own camera; otherwise fall back to the scene config.
        const cameraConfig = this._cameraOverride || config.camera;

        if (config.background_color) {
            this.scene.background = new THREE.Color(config.background_color);
        }

        this._applyCamera(cameraConfig);

        configureControls(this.controls, this.renderer, spaceDim);
        setSpaceDim(spaceDim);
        this.resize();

        if (config.title !== undefined) {
            this._renderTitle(config.title);
            this.emit('titlechange', { title: config.title });
        }

        if (config.annotation) {
            this._renderAnnotation(config.annotation, null);
        } else if (config.annotation === '') {
            this._removeAnnotation();
        }
    }

    /**
     * Apply a camera config to this pane's camera + orbit controls.  Shared by
     * `_applySceneConfig` and `setCamera`.
     */
    _applyCamera(cameraConfig) {
        const spaceDim = (this.sceneConfig && this.sceneConfig.space_dim) || 3;

        this.camera = switchToCamera(this.camera, this.controls, spaceDim, cameraConfig || null);
        setCamera(this.camera);

        const cc = cameraConfig || {};
        if (cc.position) this.camera.position.set(cc.position[0], cc.position[1], cc.position[2]);
        if (cc.target) this.controls.target.set(cc.target[0], cc.target[1], cc.target[2]);
        if (cc.fov) { this.camera.fov = cc.fov; this.camera.updateProjectionMatrix(); }
        if (cc.near) { this.camera.near = cc.near; this.camera.updateProjectionMatrix(); }
        if (cc.far) { this.camera.far = cc.far; this.camera.updateProjectionMatrix(); }
        this.controls.update();
    }

    /**
     * Move this pane's camera at runtime (per-pane `view_camera` message).
     * Passing `null`/`undefined` reverts to the scene's own camera.
     */
    setCamera(cameraConfig) {
        this._cameraOverride = cameraConfig || null;
        const effective = this._cameraOverride || (this.sceneConfig && this.sceneConfig.camera);
        this._applyCamera(effective);
        this.resize();
    }

    _renderTitle(titleText) {
        if (!this._titleElement) {
            this._titleElement = document.createElement('div');
            this._titleElement.style.position = 'absolute';
            this._titleElement.style.top = '10px';
            this._titleElement.style.left = '50%';
            this._titleElement.style.transform = 'translateX(-50%)';
            this._titleElement.style.color = '#ffffff';
            this._titleElement.style.fontFamily = 'sans-serif';
            this._titleElement.style.fontSize = '20px';
            this._titleElement.style.fontWeight = 'bold';
            this._titleElement.style.background = 'rgba(0, 0, 0, 0.6)';
            this._titleElement.style.padding = '6px 20px';
            this._titleElement.style.borderRadius = '4px';
            this._titleElement.style.pointerEvents = 'none';
            this._titleElement.style.zIndex = '5';
            this.el.appendChild(this._titleElement);
        }
        this._titleElement.textContent = '';
        this._titleElement.innerHTML = titleText;
        if (typeof renderMathInElement !== 'undefined') {
            try {
                renderMathInElement(this._titleElement, {
                    delimiters: [
                        { left: '$$', right: '$$', display: true },
                        { left: '$', right: '$', display: false },
                    ],
                    throwOnError: false,
                });
            } catch (e) { /* ignore */ }
        }
    }

    _renderAnnotation(mdText, styleData) {
        this._removeAnnotation();

        const s = styleData || {};
        const container = document.createElement('div');

        if (typeof marked !== 'undefined') {
            container.innerHTML = marked.parse(mdText, { breaks: true });
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

        this.el.appendChild(container);
        this._annotationPanel = container;
    }

    _removeAnnotation() {
        if (this._annotationPanel) {
            this._annotationPanel.remove();
            this._annotationPanel = null;
        }
    }

    // ── per-scene message handling ─────────────────────────────

    async handleMessage(msg) {
        if (msg.type === 'clear_all') {
            this.clearAll();
        } else if (msg.type === 'scene_config') {
            this._log('init', 'scene_config name=' + (msg.name || '') + ' space_dim=' + msg.space_dim);
            this._applySceneConfig(msg);
        } else if (msg.type === 'scene_update') {
            this._log('init', 'scene_update objects=' + (msg.objects ? msg.objects.length : 0) + ' removed=' + (msg.removed ? msg.removed.length : 0));
            if (msg.removed) {
                for (const id of msg.removed) this._removeSceneObject(id);
            }
            if (msg.objects) {
                for (const obj of msg.objects) await this._upsertObject(obj);
            }
            if (msg.fit_camera) this.fitCamera();
            if (this._ws && this._ws.readyState === WebSocket.OPEN) {
                this._log('ws-send', 'type=scene_synced browser_id=' + this._browserId);
                this._ws.send(JSON.stringify({ type: 'scene_synced', browser_id: this._browserId }));
            }
        } else if (msg.type === 'object_update') {
            if (msg.removed) {
                for (const id of msg.removed) this._removeSceneObject(id);
            }
            if (msg.patches) {
                for (const patch of msg.patches) await this._applyObjectPatch(patch);
            }
            if (msg.fit_camera) this.fitCamera();
        } else if (msg.type === 'animate') {
            this._handleAnimate(msg);
        } else if (msg.type === 'timeline') {
            this._handleTimeline(msg);
        } else if (msg.type === 'controls_define') {
            this._log('init', 'controls_define controls=' + (msg.controls ? msg.controls.length : 0) + ' groups=' + (msg.groups ? msg.groups.length : 0));
            handleControlsDefine(msg);
            const controls2 = msg.controls || [];
            const groups = msg.groups || [];
            for (const g of groups) {
                if (g.parentId) attachGroup(g, controls2, this.sceneObjects);
            }
        } else if (msg.type === 'controls_clear') {
            handleControlsClear();
            detachAll();
        } else if (msg.type === 'banner_define') {
            this._showBanner(msg);
        } else if (msg.type === 'banner_remove') {
            this._removeBanner(msg.id);
        } else if (msg.type === 'banner_clear') {
            this._clearBanners();
        }
    }

    _showBanner(msg) {
        this._removeBanner(msg.id);
        const view = new BannerView({
            id: msg.id,
            title: msg.title,
            text: msg.text,
            align_x: msg.align_x,
            align_y: msg.align_y,
            auto_hide: msg.auto_hide,
            dismissable: msg.dismissable,
            controls: msg.controls || [],
            backdropMode: 'absolute',
            onClose: (id) => this._sendBannerClosed(id),
        });
        this._banners.set(msg.id, view);
        view.mount(this.el);
    }

    _removeBanner(id) {
        const view = this._banners.get(id);
        if (!view) return;
        this._banners.delete(id);
        view.destroy();
    }

    _clearBanners() {
        for (const id of [...this._banners.keys()]) this._removeBanner(id);
    }

    _sendBannerClosed(id) {
        if (this._ws && this._ws.readyState === WebSocket.OPEN) {
            this._ws.send(
                JSON.stringify({ type: 'banner_closed', id, browser_id: this._browserId })
            );
        }
    }

    async _upsertObject(msg) {
        const old = this.sceneObjects.get(msg.id);
        if (old) {
            if (old.layer === 'scene' && old.obj) {
                removeEntityMesh(old.obj);
            } else if (old.obj && old.obj.removeFromParent) {
                old.obj.removeFromParent();
            }
            if (old.el) old.el.remove();
            this.sceneObjects.delete(msg.id);
        }
        if (msg.layer === 'scene') {
            // SDF proxies require WebGL2 (GLSL3 + gl_FragDepth); on WebGL1 they
            // are skipped and a single yellow warning banner is shown.
            if (msg.kind === 'sdf' && !this._isWebGL2) {
                _showSdfWebGL2Warning();
                return;
            }
            const entry = await buildSceneObject(msg, this.scene, this.sceneObjects);
            if (entry && msg.interaction) {
                registerInteractive(msg.id, entry.obj, msg.interaction);
            }
        } else if (msg.layer === 'overlay') {
            if (msg.kind === 'annotation') {
                if (!msg.text) return;
                this._renderAnnotation(msg.text, msg.style || null);
                if (this._annotationPanel) {
                    this.sceneObjects.set(msg.id, { obj: null, mesh: null, data: { ...msg }, el: this._annotationPanel, layer: 'overlay' });
                }
                return;
            }
            buildOverlay(msg, this.scene, this.sceneObjects);
        }
    }

    _removeSceneObject(id) {
        unregisterInteractive(id);
        const entry = this.sceneObjects.get(id);
        if (entry && entry.layer === 'scene' && entry.obj && entry.obj.userData._attachedGroups) {
            for (const groupId of entry.obj.userData._attachedGroups) {
                detachGroup(groupId);
            }
        }
        removeObject(id, this.sceneObjects);
        cancelTween(id);
    }

    async _applyObjectPatch(patch) {
        const id = patch.id;
        const aspect = patch.aspect;
        const value = patch.value || {};

        if (aspect === 'full') {
            await this._upsertObject(value);
            return;
        }
        const entry = this.sceneObjects.get(id);
        if (!entry) return;

        if (aspect === 'content') {
            await this._updateEntityContent(id, value);
            return;
        }
        if (aspect === 'transform') {
            if (entry.obj) applyTransformToObject(entry.obj, value);
            return;
        }
        if (aspect === 'style') {
            if (value.style && entry.obj) {
                const prev = entry.data || {};
                const merged = { ...prev, style: { ...(prev.style || {}), ...value.style } };
                if (entityRequiresRebuild(merged, prev)) {
                    await this._updateEntityContent(id, merged);
                } else {
                    entry.data = merged;
                    if (entry.obj.isObject3D) applyStyleUpdate(entry.obj, merged);
                }
            }
        }
    }

    async _updateEntityContent(id, content) {
        const entry = this.sceneObjects.get(id);
        if (!entry || entry.layer !== 'scene' || !entry.mesh) return;
        const prev = entry.data || {};

        if (updateEntityMesh(entry.mesh, content, prev)) {
            entry.data = { ...prev, ...content };
            return;
        }

        const newMesh = await createEntityMesh({ ...prev, ...content });
        if (!newMesh) return;

        if (entry.obj === entry.mesh) {
            const attachedLabels = (entry.obj.userData._labels || []).slice();
            const parent = entry.obj.parent;
            removeEntityMesh(entry.obj);
            entry.obj = newMesh;
            entry.mesh = newMesh;
            newMesh.userData.parentId = prev.parent_id || null;
            newMesh.userData._labels = [];
            if (parent) parent.add(newMesh); else this.scene.add(newMesh);
            for (const lblId of attachedLabels) {
                const lblEntry = this.sceneObjects.get(lblId);
                if (lblEntry && lblEntry.obj) {
                    newMesh.add(lblEntry.obj);
                    newMesh.userData._labels.push(lblId);
                }
            }
        } else {
            removeEntityMesh(entry.mesh);
            entry.obj.add(newMesh);
            entry.mesh = newMesh;
        }
        entry.data = { ...prev, ...content };
        if (prev.interaction) {
            registerInteractive(id, entry.obj, prev.interaction);
        }
    }

    _handleAnimate(msg) {
        if (!msg.animations) return;
        for (const anim of msg.animations) {
            startTween(anim.id, anim.target, anim.duration || 1.0, anim.easing || 'ease-in-out', this.sceneObjects);
        }
    }

    _handleTimeline(msg) {
        if (!msg.steps) return;
        for (const step of msg.steps) {
            const delay = (step.at || 0) * 1000;
            setTimeout(() => {
                this._handleAnimate({ animations: [step.animate] });
            }, delay);
        }
    }
}
