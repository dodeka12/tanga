// Shared utilities for Tanga entity/operator renderers.
// Phase 5: Used by per-entity modules and the factory dispatcher.

import * as THREE from 'three';

/**
 * Create a MeshPhongMaterial with sensible defaults for Tanga entities.
 *
 * Critical: depthWrite is disabled for translucent materials (opacity < 0.99)
 * to prevent depth-sorting artifacts.
 */
export function makeMaterial(color, opacity = 1.0, doubleSided = false) {
    const c = typeof color === 'string' ? new THREE.Color(color) : color;
    return new THREE.MeshPhongMaterial({
        color: c,
        opacity,
        transparent: opacity < 1.0,
        depthWrite: opacity >= 0.99,
        side: doubleSided ? THREE.DoubleSide : THREE.FrontSide,
    });
}

/**
 * Create a quaternion that rotates the Y-axis to point along the given direction.
 * Used to orient cylinders (lines), cones (direction arrows), and planes.
 */
export function rotationFromDirection(dx, dy, dz) {
    const dir = new THREE.Vector3(dx, dy, dz).normalize();
    const up = new THREE.Vector3(0, 1, 0);
    return new THREE.Quaternion().setFromUnitVectors(up, dir);
}

/**
 * Create a quaternion that rotates the Z-axis to point along the given normal.
 * Used to orient toruses (circles) and planes.
 */
export function rotationFromNormal(nx, ny, nz) {
    const normal = new THREE.Vector3(nx, ny, nz).normalize();
    return new THREE.Quaternion().setFromUnitVectors(
        new THREE.Vector3(0, 0, 1), normal
    );
}

/**
 * Tag a mesh with entity metadata for click detection and debugging.
 */
export function tagEntity(mesh, ent) {
    mesh.userData = { entityId: ent.id, kind: ent.kind, data: ent };
}

/**
 * Parse a color from an entity dict, using the style object if available.
 * Falls back to flat ent.color, then the provided fallback.
 */
export function parseColor(ent, fallback = '#ffffff') {
    if (ent.color) return ent.color;
    return fallback;
}

/**
 * Read a rendering parameter, preferring ent.style.* (Phase 4c) over flat ent.*.
 *
 * @param {object} ent - The entity JSON dict.
 * @param {string} key - The camelCase key (e.g. "size", "tubeRadius").
 * @param {*} fallback - Default value if neither source has the key.
 * @returns {*}
 */
export function styleParam(ent, key, fallback) {
    if (ent.style && ent.style[key] !== undefined) return ent.style[key];
    if (ent[key] !== undefined) return ent[key];
    return fallback;
}

/**
 * Create a 3D arrow group (cylinder shaft + cone head) oriented along a direction.
 *
 * @param {THREE.Color|string} color
 * @param {number} opacity
 * @param {number[]} vec - Direction vector [x, y, z].
 * @param {number} length - Total arrow length.
 * @param {number[]} origin - Start point [x, y, z].
 * @returns {THREE.Group}
 */
export function createArrow(color, opacity, vec, length, origin) {
    const g = new THREE.Group();
    const sl = length * 0.75, sr = 0.06;
    const hl = length * 0.25, hr = 0.15;
    const col = typeof color === 'string' ? new THREE.Color(color) : color;
    const shaft = new THREE.Mesh(
        new THREE.CylinderGeometry(sr, sr, sl, 8, 1),
        makeMaterial(col, opacity)
    );
    shaft.position.y = sl / 2;
    g.add(shaft);
    const head = new THREE.Mesh(
        new THREE.ConeGeometry(hr, hl, 8, 1),
        makeMaterial(col, opacity)
    );
    head.position.y = sl + hl / 2;
    g.add(head);
    const d = new THREE.Vector3(vec[0], vec[1], vec[2]).normalize();
    g.setRotationFromQuaternion(
        new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), d)
    );
    g.position.set(origin[0], origin[1], origin[2]);
    return g;
}

/**
 * Add a wireframe overlay to a parent mesh/group using ``WireframeGeometry``
 * and ``LineSegments`` (solid or dashed).
 *
 * @param {THREE.Mesh|THREE.Group} parent - The parent to attach the overlay to.
 * @param {THREE.BufferGeometry} geometry - The geometry whose edges to render.
 * @param {THREE.Color|string} color - Wireframe color.
 * @param {object|null} dashPattern - Dash config dict with ``dash_size``,
 *     ``gap_size``, ``scale``, or ``null`` for solid lines.
 */
export function addWireframeOverlay(parent, geometry, color, dashPattern, opacity = 1.0) {
    const wireGeo = new THREE.WireframeGeometry(geometry);
    const c = typeof color === 'string' ? new THREE.Color(color) : color;
    const useDash = dashPattern && dashPattern.dash_size > 0;
    const material = useDash
        ? new THREE.LineDashedMaterial({
            color: c,
            dashSize: dashPattern.dash_size,
            gapSize: dashPattern.gap_size,
            scale: dashPattern.scale || 1.0,
            opacity: opacity,
            transparent: opacity < 1.0,
        })
        : new THREE.LineBasicMaterial({ color: c, opacity: opacity, transparent: opacity < 1.0 });
    const lines = new THREE.LineSegments(wireGeo, material);
    if (useDash) {
        const pos = wireGeo.getAttribute('position');
        const distances = new Float32Array(pos.count);
        for (let i = 0; i < pos.count; i += 2) {
            const dx = pos.getX(i + 1) - pos.getX(i);
            const dy = pos.getY(i + 1) - pos.getY(i);
            const dz = pos.getZ(i + 1) - pos.getZ(i);
            const len = Math.sqrt(dx * dx + dy * dy + dz * dz);
            distances[i] = 0;
            distances[i + 1] = len;
        }
        wireGeo.setAttribute('lineDistance', new THREE.BufferAttribute(distances, 1));
    }
    parent.add(lines);
}

/**
 * Create a group of concentric expanding rings (for Dilator types).
 *
 * @param {THREE.Color|string} color
 * @param {number} opacity
 * @param {number} count - Number of rings.
 * @param {number} maxR - Max ring radius.
 * @param {number[]} origin - Center position [x, y, z].
 * @returns {THREE.Group}
 */
export function createDilatorRings(color, opacity, count, maxR, origin) {
    const g = new THREE.Group();
    const minR = 0.3;
    const col = typeof color === 'string' ? new THREE.Color(color) : color;
    for (let i = 0; i < count; i++) {
        const t = count > 1 ? i / (count - 1) : 0.5;
        const r = minR + t * (maxR - minR);
        const torus = new THREE.Mesh(
            new THREE.TorusGeometry(r, 0.02, 8, 64),
            makeMaterial(col, opacity * (0.4 + 0.6 * t))
        );
        torus.rotation.x = i % 2 === 0 ? 0 : Math.PI / 2;
        g.add(torus);
    }
    g.position.set(origin[0], origin[1], origin[2]);
    return g;
}