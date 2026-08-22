// SDF Viewer — WebGL2 ray-marched viewer entry point.
//
// Renders a single composed signed-distance field via a fullscreen-quad
// raymarcher. It reuses the standard viewer's camera (`view_mode.js`) and
// OrbitControls (`controls.js`) so the default/custom camera matches the
// non-SDF viewer 1:1.

import * as THREE from 'three';
import { createCamera } from '../view_mode.js';
import { setupControls } from '../controls.js';

// ── Fullscreen-quad vertex shader ──────────────────────────
// The quad's local XY is used directly as clip-space; the fragment shader
// reconstructs the ray from the shared perspective camera.

const VERTEX_SHADER = /* glsl */ `
void main() {
    gl_Position = vec4(position.xy, 0.0, 1.0);
}
`;

// ── Shader source assembly ─────────────────────────────────
// The GLSL snippets are fetched from their files at runtime (single source of
// truth). Assemble order mirrors the plan: common → primitives → combinators →
// raymarch body.

async function _loadShaderSources() {
    const base = new URL('./shaders/', import.meta.url);
    const [common, primitives, combinators, raymarch] = await Promise.all([
        fetch(new URL('sdf_common.glsl', base)).then((r) => r.text()),
        fetch(new URL('primitives.glsl', base)).then((r) => r.text()),
        fetch(new URL('combinators.glsl', base)).then((r) => r.text()),
        fetch(new URL('raymarch.glsl', base)).then((r) => r.text()),
    ]);
    return {
        fragment: [common, primitives, combinators, raymarch].join('\n'),
        vertex: VERTEX_SHADER,
    };
}

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

async function init() {
    // WebGLRenderer: three.js r168 uses WebGL2 when available.
    let renderer;
    try {
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    } catch (e) {
        console.error('WebGL renderer creation failed:', e);
        showError('SDF viewer requires WebGL2, which is not available.');
        return;
    }

    // Hard gate: no silent WebGL1 fallback.
    if (!renderer.capabilities.isWebGL2) {
        showError('SDF viewer requires WebGL2.');
        renderer.dispose();
        return;
    }

    const container = document.getElementById('viewer-container') || document.body;
    container.appendChild(renderer.domElement);
    renderer.setPixelRatio(window.devicePixelRatio);

    // Shared camera + controls (camera parity with the standard viewer).
    const camera = createCamera(3, window.innerWidth / window.innerHeight);
    const controls = setupControls(camera, renderer);

    // Identity camera for the fullscreen quad.
    const quadCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    const scene = new THREE.Scene();

    const { fragment, vertex } = await _loadShaderSources();
    const material = new THREE.ShaderMaterial({
        vertexShader: vertex,
        fragmentShader: fragment,
        uniforms: {
            uResolution: { value: new THREE.Vector2() },
            uCameraPosition: { value: new THREE.Vector3() },
            uCameraWorldMatrix: { value: new THREE.Matrix4() },
            uCameraProjectionMatrixInverse: { value: new THREE.Matrix4() },
            uCameraNear: { value: 0.1 },
            uCameraFar: { value: 1000.0 },
        },
        glslVersion: THREE.GLSL3,
        depthWrite: false,
        depthTest: false,
    });

    const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), material);
    quad.frustumCulled = false;
    scene.add(quad);

    function resize() {
        const width = container.clientWidth || window.innerWidth;
        const height = container.clientHeight || window.innerHeight;
        renderer.setSize(width, height);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
    }

    window.addEventListener('resize', resize);
    resize();

    function animate() {
        requestAnimationFrame(animate);
        controls.update();
        camera.updateMatrixWorld();

        const u = material.uniforms;
        u.uResolution.value.set(
            renderer.domElement.width,
            renderer.domElement.height
        );
        u.uCameraPosition.value.copy(camera.position);
        u.uCameraWorldMatrix.value.copy(camera.matrixWorld);
        u.uCameraProjectionMatrixInverse.value.copy(camera.projectionMatrixInverse);
        u.uCameraNear.value = camera.near;
        u.uCameraFar.value = camera.far;

        renderer.render(scene, quadCamera);
    }

    animate();
    window.__tanga_ready = true;
}

init().catch((e) => {
    console.error('SDF viewer initialization failed:', e);
    showError('The SDF viewer could not start due to an unexpected error.');
});