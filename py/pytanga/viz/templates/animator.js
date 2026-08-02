// Keyframe tween engine for Tanga 3D Viewer.

import * as THREE from 'three';

const tweens = new Map();

const EASING = {
    linear: (t) => t,
    'ease-in': (t) => t * t,
    'ease-out': (t) => t * (2 - t),
    'ease-in-out': (t) => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t,
};

export function startTween(id, target, duration, easing, entityMeshes) {
    const mesh = entityMeshes.get(id);
    if (!mesh) return;

    const start = {
        position: mesh.position.clone(),
        scale: mesh.scale.clone(),
        rotation: new THREE.Euler().setFromQuaternion(mesh.quaternion),
    };
    mesh.traverse(child => {
        if (child.material && child.material.opacity !== undefined) {
            start.opacity = child.material.opacity;
        }
    });

    tweens.set(id, {
        start,
        target: { ...target },
        duration,
        easing: EASING[easing] || EASING['ease-in-out'],
        startTime: performance.now() / 1000,
    });
}

export function updateTweens(entityMeshes) {
    if (tweens.size === 0) return false;
    const now = performance.now() / 1000;
    let hasActive = false;

    for (const [id, tween] of tweens) {
        const mesh = entityMeshes.get(id);
        if (!mesh) { tweens.delete(id); continue; }

        const elapsed = now - tween.startTime;
        let t = Math.min(elapsed / tween.duration, 1.0);
        t = tween.easing(t);

        if (tween.target.position) {
            mesh.position.lerpVectors(tween.start.position, new THREE.Vector3(...tween.target.position), t);
        }
        if (tween.target.rotation) {
            const tr = new THREE.Euler(...tween.target.rotation);
            mesh.rotation.set(
                tween.start.rotation.x + (tr.x - tween.start.rotation.x) * t,
                tween.start.rotation.y + (tr.y - tween.start.rotation.y) * t,
                tween.start.rotation.z + (tr.z - tween.start.rotation.z) * t,
            );
        }
        if (tween.target.opacity !== undefined) {
            const from = tween.start.opacity ?? 1.0;
            const val = from + (tween.target.opacity - from) * t;
            mesh.traverse(child => {
                if (child.material && child.material.opacity !== undefined) {
                    child.material.opacity = val;
                    child.material.transparent = val < 1.0;
                    child.material.depthWrite = val >= 0.99;
                    child.material.needsUpdate = true;
                }
            });
        }
        if (tween.target.scale) {
            mesh.scale.lerpVectors(tween.start.scale, new THREE.Vector3(...tween.target.scale), t);
        }

        if (t >= 1.0) { tweens.delete(id); } else { hasActive = true; }
    }
    return hasActive;
}

export function cancelTween(id) {
    if (id) tweens.delete(id); else tweens.clear();
}