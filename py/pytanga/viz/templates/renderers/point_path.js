// PointPath renderer — renders connected line segments from an ordered
// list of 3D points with optional per-vertex colors.
// Uses THREE.Line with BufferGeometry for efficiency.

import * as THREE from 'three';
import {
    makeMaterial,
    parseColor,
    styleParam,
    tagEntity,
} from './utils.js';

/**
 * Create a THREE.Line for a PointPath entity JSON dict.
 *
 * ent.points: [[x,y,z], ...]
 * ent.colors: ["#ff0000", null, "#00ff00", ...]  — null = use uniform fallback
 * ent.color: "#ffffff"  — uniform fallback color
 * ent.opacity: 1.0
 * ent.line_thickness: 0.03
 */
export function createPointPath(ent) {
    const points = ent.points || [];
    if (points.length < 2) {
        // Need at least 2 points for a line segment
        return new THREE.Group();
    }

    const perPointColors = ent.colors || [];
    const uniformColor = parseColor(ent, '#ffffff');
    const opacity = styleParam(ent, 'opacity', 1.0);

    // Determine if we should use per-vertex colors
    const hasAnyVertexColor = perPointColors.some(c => c !== null && c !== undefined);
    const perVertexFields = hasAnyVertexColor ? { vertexColors: true } : {};

    // Build segment pairs: each consecutive pair of points forms one segment
    // For n points we have n-1 segments, so 2*(n-1) positions
    const n = points.length;
    const numVertices = (n - 1) * 2;
    const positions = new Float32Array(numVertices * 3);
    let vertexColors = null;
    if (hasAnyVertexColor) {
        vertexColors = new Float32Array(numVertices * 3);
    }

    for (let i = 0; i < n - 1; i++) {
        const p0 = points[i];
        const p1 = points[i + 1];
        const vi = i * 2;

        // Vertex i*2
        positions[vi * 3] = p0[0];
        positions[vi * 3 + 1] = p0[1];
        positions[vi * 3 + 2] = p0[2];

        // Vertex i*2 + 1
        positions[(vi + 1) * 3] = p1[0];
        positions[(vi + 1) * 3 + 1] = p1[1];
        positions[(vi + 1) * 3 + 2] = p1[2];

        if (hasAnyVertexColor) {
            const c0 = _resolveColor(perPointColors[i], uniformColor);
            const c1 = _resolveColor(perPointColors[i + 1], uniformColor);
            vertexColors[vi * 3] = c0.r;
            vertexColors[vi * 3 + 1] = c0.g;
            vertexColors[vi * 3 + 2] = c0.b;
            vertexColors[(vi + 1) * 3] = c1.r;
            vertexColors[(vi + 1) * 3 + 1] = c1.g;
            vertexColors[(vi + 1) * 3 + 2] = c1.b;
        }
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    if (hasAnyVertexColor) {
        geometry.setAttribute('color', new THREE.BufferAttribute(vertexColors, 3));
    }

    const material = new THREE.LineBasicMaterial({
        color: hasAnyVertexColor ? 0xffffff : uniformColor,
        opacity: opacity,
        transparent: opacity < 1.0,
        depthWrite: opacity >= 0.99,
        ...perVertexFields,
    });

    const line = new THREE.LineSegments(geometry, material);
    tagEntity(line, ent);
    return line;
}

/**
 * Resolve a per-point color to an {r, g, b} object (0-1 range).
 * If the color is null/undefined, returns the parsed uniform color.
 */
function _resolveColor(colorHex, uniformColor) {
    if (colorHex === null || colorHex === undefined) {
        return uniformColor;
    }
    return new THREE.Color(colorHex);
}