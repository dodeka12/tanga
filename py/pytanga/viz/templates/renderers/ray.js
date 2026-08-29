// Per-object analytic ray renderer for the standard viewer.
//
// Builds a bounding-box proxy mesh (BoxGeometry) with a ShaderMaterial whose
// fragment shader analytically intersects the view ray with the object's
// implicit surface and writes `gl_FragDepth`, so ray objects depth-composite
// with meshes and SDF proxies in one scene.  The per-object analytic
// `intersectRay` / `normalAt` functions live in `ray/intersect.glsl`.
//
// The proxy is rasterized with `side: THREE.BackSide` so its far faces cover
// the volume whether the camera is inside or outside the box (unbounded
// quadrics fall back to a large ±10 cube, so the camera is often inside it).
// The surface normal is also flipped to face the camera in the fragment
// shader: implicit surfaces have no face culling, so open quadrics would
// otherwise shade their "back" side dark and look one-sided.

import * as THREE from 'three';
import {
    MAX_LIGHTS,
    lightPreamble,
    parseHexColor,
    parseLighting,
    setLightUniforms,
} from './sdf/lighting.js';

let _rayShaderParts = null;

async function _loadRayShaderParts() {
    if (_rayShaderParts) return _rayShaderParts;
    // Standalone HTML exports inline the GLSL as a global (there is no server
    // to fetch the .glsl files from); the live viewer fetches them instead.
    if (typeof window !== 'undefined' && window.__tanga_ray_shaders) {
        _rayShaderParts = window.__tanga_ray_shaders;
        return _rayShaderParts;
    }
    const base = new URL('./', import.meta.url);
    const intersect = await fetch(new URL('./ray/intersect.glsl', base)).then((r) => r.text());
    const quadric = await fetch(new URL('./ray/quadric.glsl', base)).then((r) => r.text());
    _rayShaderParts = { intersect, quadric };
    return _rayShaderParts;
}

const _VERTEX = `
out vec3 vLocalPos;
flat out vec3 vCameraLocal;

void main() {
    vLocalPos = position;
    // Camera position in the mesh's local space (same for every vertex).
    vCameraLocal = (inverse(modelMatrix) * vec4(cameraPosition, 1.0)).xyz;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

const _FRAGMENT = `
uniform vec3 uBoundHalf;
uniform vec3 uColor;
uniform float uOpacity;
uniform mat4 uModelMatrix;
uniform mat4 uProjectionMatrix;

in vec3 vLocalPos;
flat in vec3 vCameraLocal;

out vec4 fragColor;

${lightPreamble}

// Per-object analytic intersection (injected from ray/intersect.glsl).
__INTERSECT__

vec3 shade(vec3 p, vec3 n, vec3 ro) {
    vec3 col = uColor * uAmbientColor;
    for (int i = 0; i < MAX_LIGHTS; i++) {
        if (i >= uLightCount) break;
        vec3 L = normalize(uLightDir[i]);
        float dif = max(dot(n, L), 0.0);
        col += uColor * uLightColor[i] * dif;
    }
    float dist = length(p - ro);
    float fog = 1.0 - exp(-0.05 * dist);
    vec3 bg = vec3(0.10, 0.10, 0.18);
    return mix(col, bg, fog);
}

void main() {
    vec3 ro = vCameraLocal;
    vec3 rd = normalize(vLocalPos - ro);

    // Ray-box intersection with the local-space AABB [-uBoundHalf, +uBoundHalf],
    // so the analytic surface is only evaluated inside the proxy volume.
    vec3 invDir = 1.0 / rd;
    vec3 t0 = (-uBoundHalf - ro) * invDir;
    vec3 t1 = (uBoundHalf - ro) * invDir;
    vec3 tmin = min(t0, t1);
    vec3 tmax = max(t0, t1);
    float tNear = max(max(tmin.x, tmin.y), tmin.z);
    float tFar = min(min(tmax.x, tmax.y), tmax.z);
    tNear = max(tNear, 0.0);
    if (tFar <= tNear) discard;

    float t = intersectRay(ro, rd);
    if (t < tNear || t > tFar) discard;

    vec3 p = ro + rd * t;
    vec3 n = normalAt(p);
    // Implicit surfaces have no face culling: an open quadric (cone, paraboloid,
    // hyperboloid) shows its "back" side from many viewpoints, where the analytic
    // normal points away from the camera and the diffuse term would go dark.
    // Flip it so it always faces the viewer before shading.
    if (dot(n, rd) > 0.0) n = -n;
    vec3 col = shade(p, n, ro);

    // Write the hit's clip-space depth so occlusion against meshes and other
    // proxies is handled by the standard depth buffer.
    vec4 clip = uProjectionMatrix * viewMatrix * uModelMatrix * vec4(p, 1.0);
    float ndc = clip.z / clip.w;
    gl_FragDepth = ndc * 0.5 + 0.5;

    fragColor = vec4(col, uOpacity);
}
`;

function _bound(ent) {
    const b = ent.bound || { min: [-1, -1, -1], max: [1, 1, 1] };
    const half = [
        (b.max[0] - b.min[0]) / 2,
        (b.max[1] - b.min[1]) / 2,
        (b.max[2] - b.min[2]) / 2,
    ];
    const center = [
        (b.min[0] + b.max[0]) / 2,
        (b.min[1] + b.max[1]) / 2,
        (b.min[2] + b.max[2]) / 2,
    ];
    return { half, center };
}

export async function createRayProxy(ent) {
    const parts = await _loadRayShaderParts();
    const { half, center } = _bound(ent);
    const [r, g, b] = parseHexColor(ent.color);
    const opacity = typeof ent.opacity === 'number' ? ent.opacity : 1.0;
    const lighting = parseLighting(ent.lighting);
    const isQuadric = ent.rayKind === 'Quadric3D';
    const intersectSrc = isQuadric ? parts.quadric : parts.intersect;

    const uniforms = {
        uBoundHalf: { value: new THREE.Vector3(half[0], half[1], half[2]) },
        uColor: { value: new THREE.Vector3(r, g, b) },
        uOpacity: { value: opacity },
        uModelMatrix: { value: new THREE.Matrix4() },
        uProjectionMatrix: { value: new THREE.Matrix4() },
        uLightCount: { value: 0 },
        uLightDir: { value: Array.from({ length: MAX_LIGHTS }, () => new THREE.Vector3()) },
        uLightColor: { value: Array.from({ length: MAX_LIGHTS }, () => new THREE.Vector3()) },
        uAmbientColor: { value: new THREE.Vector3() },
    };
    if (isQuadric) {
        const m = ent.matrix && ent.matrix.length === 16
            ? ent.matrix
            : [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, -1];
        uniforms.uQuadric = { value: new THREE.Matrix4().set(...m) };
    }
    setLightUniforms(uniforms, lighting);

    const material = new THREE.ShaderMaterial({
        vertexShader: _VERTEX,
        fragmentShader: _FRAGMENT.replace('__INTERSECT__', intersectSrc),
        uniforms,
        transparent: opacity < 0.99,
        depthWrite: true,
        depthTest: true,
        glslVersion: THREE.GLSL3,
        side: THREE.BackSide,
    });

    const geometry = new THREE.BoxGeometry(half[0] * 2, half[1] * 2, half[2] * 2);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(center[0], center[1], center[2]);
    mesh.frustumCulled = true;

    mesh.onBeforeRender = (_renderer, _scene, camera) => {
        material.uniforms.uModelMatrix.value.copy(mesh.matrixWorld);
        material.uniforms.uProjectionMatrix.value.copy(camera.projectionMatrix);
    };

    mesh.userData.rayKind = ent.rayKind || null;
    return mesh;
}

export function updateRayProxy(mesh, ent) {
    const mat = mesh.material;
    if (!mat || !mat.uniforms) return true;
    const [r, g, b] = parseHexColor(ent.color);
    mat.uniforms.uColor.value.set(r, g, b);
    const opacity = typeof ent.opacity === 'number' ? ent.opacity : 1.0;
    mat.uniforms.uOpacity.value = opacity;
    mat.transparent = opacity < 0.99;
    return true;
}

export function disposeRayProxy(mesh) {
    if (!mesh) return;
    if (mesh.geometry) mesh.geometry.dispose();
    if (mesh.material) mesh.material.dispose();
}

