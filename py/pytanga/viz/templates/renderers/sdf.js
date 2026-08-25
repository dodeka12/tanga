// Per-object SDF renderer for the standard viewer (Phase 3).
//
// Builds a bounding-volume proxy mesh: a BoxGeometry sized to the object's
// local-space AABB `bound` plus a ShaderMaterial whose fragment shader
// ray-marches that one object's distance field in local space and writes
// `gl_FragDepth`, so the standard depth buffer occludes it against meshes and
// other SDF proxies. Reuses the SDF viewer's `emitTree`, GLSL library, and
// directional-light uniform model (shared via `sdf/lighting.js`).

import * as THREE from 'three';
import {
    buildProxyFragment,
    buildProxyVertex,
    MAX_GROUP_MEMBERS,
    MAX_STEPS,
} from './sdf/glsl.js';
import {
    DEFAULT_LIGHTING,
    MAX_LIGHTS,
    parseHexColor,
    parseLighting,
    setLightUniforms,
} from './sdf/lighting.js';

let _shaderParts = null;

async function _loadShaderParts() {
    if (_shaderParts) return _shaderParts;
    // Standalone HTML exports inline the GLSL as a global (there is no server
    // to fetch the .glsl files from); the live viewer fetches them instead.
    if (typeof window !== 'undefined' && window.__tanga_sdf_shaders) {
        _shaderParts = window.__tanga_sdf_shaders;
        return _shaderParts;
    }
    const base = new URL('./', import.meta.url);
    const [common, primitives, combinators, proxy] = await Promise.all([
        fetch(new URL('../sdf/shaders/sdf_common.glsl', base)).then((r) => r.text()),
        fetch(new URL('../sdf/shaders/primitives.glsl', base)).then((r) => r.text()),
        fetch(new URL('../sdf/shaders/combinators.glsl', base)).then((r) => r.text()),
        fetch(new URL('./sdf/proxy.glsl', base)).then((r) => r.text()),
    ]);
    _shaderParts = { common, primitives, combinators, proxy };
    return _shaderParts;
}

function _maxSteps(ent) {
    const v = ent.style && ent.style.max_steps;
    return typeof v === 'number' ? v : MAX_STEPS;
}

function _softShadows(ent) {
    return !ent.style || ent.style.soft_shadows !== false;
}

// Compose a member's position/rotation (Euler XYZ)/scale into a world matrix,
// and return its INVERSE (the shader transforms points into the member's local
// space before evaluating its SDF).
function _memberInvTransform(member) {
    const t = member.transform || {};
    const pos = t.position || [0, 0, 0];
    const rot = t.rotation || [0, 0, 0];
    const scale = t.scale || [1, 1, 1];
    const m = new THREE.Matrix4().compose(
        new THREE.Vector3(pos[0], pos[1], pos[2]),
        new THREE.Quaternion().setFromEuler(new THREE.Euler(rot[0], rot[1], rot[2], 'XYZ')),
        new THREE.Vector3(scale[0], scale[1], scale[2]),
    );
    return m.invert();
}

function _buildUniforms(ent) {
    const [r, g, b] = parseHexColor(ent.color);
    const uniforms = {
        uColor: { value: new THREE.Color(r, g, b) },
        uOpacity: { value: typeof ent.opacity === 'number' ? ent.opacity : 1.0 },
        uMaxSteps: { value: _maxSteps(ent) },
        uSoftShadows: { value: _softShadows(ent) ? 1.0 : 0.0 },
        uBoundHalf: { value: new THREE.Vector3() },
        uModelMatrix: { value: new THREE.Matrix4() },
        uProjectionMatrix: { value: new THREE.Matrix4() },
        uHover: { value: new THREE.Color(0x000000) },
        uLightCount: { value: 0 },
        uLightDir: { value: Array.from({ length: MAX_LIGHTS }, () => new THREE.Vector3()) },
        uLightColor: { value: Array.from({ length: MAX_LIGHTS }, () => new THREE.Vector3()) },
        uAmbientColor: { value: new THREE.Vector3() },
    };
    setLightUniforms(uniforms, parseLighting(DEFAULT_LIGHTING));

    if (ent.members) {
        // The shader declares the full array, so pad unused slots with identity.
        const invs = ent.members.map(_memberInvTransform);
        while (invs.length < MAX_GROUP_MEMBERS) invs.push(new THREE.Matrix4());
        uniforms.uMemberInvTransform = { value: invs };
    }

    return uniforms;
}

export async function createSdfProxy(ent) {
    const parts = await _loadShaderParts();

    const bound = ent.bound || { min: [-1, -1, -1], max: [1, 1, 1] };
    const half = [
        (bound.max[0] - bound.min[0]) / 2,
        (bound.max[1] - bound.min[1]) / 2,
        (bound.max[2] - bound.min[2]) / 2,
    ];
    const center = [
        (bound.min[0] + bound.max[0]) / 2,
        (bound.min[1] + bound.max[1]) / 2,
        (bound.min[2] + bound.max[2]) / 2,
    ];

    const uniforms = _buildUniforms(ent);
    uniforms.uBoundHalf.value.set(half[0], half[1], half[2]);

    const material = new THREE.ShaderMaterial({
        vertexShader: buildProxyVertex(),
        fragmentShader: buildProxyFragment(ent, parts),
        uniforms,
        transparent: uniforms.uOpacity.value < 0.99,
        depthWrite: true,
        depthTest: true,
        glslVersion: THREE.GLSL3,
        side: THREE.FrontSide,
    });

    const geometry = new THREE.BoxGeometry(half[0] * 2, half[1] * 2, half[2] * 2);
    const mesh = new THREE.Mesh(geometry, material);
    // The bound is centred at the object origin, so the box centre is [0,0,0];
    // keep the computation for hand-crafted (non-centred) bounds.
    mesh.position.set(center[0], center[1], center[2]);
    mesh.frustumCulled = true;

    // The depth write needs the live model/projection matrices in the fragment
    // shader (three.js only auto-provides them to the vertex shader).
    mesh.onBeforeRender = (_renderer, _scene, camera) => {
        material.uniforms.uModelMatrix.value.copy(mesh.matrixWorld);
        material.uniforms.uProjectionMatrix.value.copy(camera.projectionMatrix);
    };

    mesh.userData.sdfKind = ent.sdfKind || null;
    return mesh;
}

// Resize the proxy box + march bounds to a (possibly updated) `bound`. Used by
// `updateSdfProxy` so an SdfGroup can resize its proxy as members move without
// recompiling the shader.
function _resizeProxyBox(mesh, ent) {
    const bound = ent.bound || { min: [-1, -1, -1], max: [1, 1, 1] };
    const half = [
        (bound.max[0] - bound.min[0]) / 2,
        (bound.max[1] - bound.min[1]) / 2,
        (bound.max[2] - bound.min[2]) / 2,
    ];
    const center = [
        (bound.min[0] + bound.max[0]) / 2,
        (bound.min[1] + bound.max[1]) / 2,
        (bound.min[2] + bound.max[2]) / 2,
    ];
    const oldGeometry = mesh.geometry;
    mesh.geometry = new THREE.BoxGeometry(half[0] * 2, half[1] * 2, half[2] * 2);
    if (oldGeometry) oldGeometry.dispose();
    mesh.position.set(center[0], center[1], center[2]);
    mesh.material.uniforms.uBoundHalf.value.set(half[0], half[1], half[2]);
}

export function updateSdfProxy(mesh, ent) {
    const mat = mesh.material;
    if (!mat || !mat.uniforms) return true;
    const [r, g, b] = parseHexColor(ent.color);
    mat.uniforms.uColor.value.setRGB(r, g, b);
    mat.uniforms.uOpacity.value = typeof ent.opacity === 'number' ? ent.opacity : 1.0;
    mat.uniforms.uMaxSteps.value = _maxSteps(ent);
    mat.uniforms.uSoftShadows.value = _softShadows(ent) ? 1.0 : 0.0;
    mat.transparent = mat.uniforms.uOpacity.value < 0.99;

    if (ent.members && mat.uniforms.uMemberInvTransform) {
        // Update each member's inverse transform uniform in place, then resize
        // the proxy box to the (recomputed) union AABB.
        const invs = mat.uniforms.uMemberInvTransform.value;
        ent.members.forEach((m, i) => {
            if (invs[i]) invs[i].copy(_memberInvTransform(m));
        });
        _resizeProxyBox(mesh, ent);
    }

    return true;
}

export function disposeSdfProxy(mesh) {
    if (!mesh) return;
    if (mesh.geometry) mesh.geometry.dispose();
    if (mesh.material) mesh.material.dispose();
}
