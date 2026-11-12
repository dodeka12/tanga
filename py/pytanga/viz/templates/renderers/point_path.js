// PointPath renderer — renders connected line segments from an ordered
// list of 3D points with optional per-vertex colors.
// Uses three.js Line2 (LineSegments2) fat lines so `line_thickness` is
// honored as a screen-space pixel width.

import * as THREE from 'three';
import {
    applyOpacityUpdate,
    applyStyleUpdate,
    makeFatSegmentsColored,
    makeFatSegmentsFromFlat,
    parseColor,
    styleParam,
    tagEntity,
} from './utils.js';
import { styleNeedsRebuild } from './style-diff.js';
import { rewriteFatLinePositions } from './fat-line-update.js';

/**
 * Return true when any entry of ``ent.colors`` is a real colour (non-null).
 * A path with no real per-point colour is drawn uniform-coloured.
 */
export function hasVertexColors(ent) {
    return (ent.colors || []).some((c) => c !== null && c !== undefined);
}

/**
 * Flatten an ordered list of points into fat-line segment data.
 *
 * Each consecutive pair of points forms one segment, so ``n`` points produce
 * ``2 * (n - 1)`` vertex positions.  Returns ``{ positions, vertexColors }``
 * where ``vertexColors`` is null unless ``hasVertexColors`` was true; null
 * per-point colours fall back to ``uniformColor``.
 */
export function flattenPath(points, perPointColors, uniformColor) {
    const hasAnyVertexColor = (perPointColors || []).some(
        (c) => c !== null && c !== undefined
    );

    const n = points.length;
    const numVertices = Math.max(0, (n - 1) * 2);
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

    return { positions, vertexColors };
}

/**
 * Create a fat line for a PointPath entity JSON dict.
 *
 * ent.points: [[x,y,z], ...]
 * ent.colors: ["#ff0000", null, "#00ff00", ...]  — null = use uniform fallback
 * ent.color: "#ffffff"  — uniform fallback color
 * ent.opacity: 1.0
 * ent.line_thickness: 2  — screen-space pixel width
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
    const lineWidth = styleParam(ent, 'line_thickness', 2);

    const hasAnyVertexColor = hasVertexColors(ent);
    const { positions, vertexColors } = flattenPath(points, perPointColors, uniformColor);

    const line = hasAnyVertexColor
        ? makeFatSegmentsColored(positions, vertexColors, opacity, lineWidth)
        : makeFatSegmentsFromFlat(positions, uniformColor, opacity, lineWidth);
    tagEntity(line, ent);
    return line;
}

export function updatePointPath(mesh, ent, prev) {
    if (!prev) return false;
    // Coloured ↔ uniform switches the material (vertexColors flag) → recreate.
    if (hasVertexColors(ent) !== hasVertexColors(prev)) return false;
    // Non-cheap style fields (line_thickness, …) are create-time inputs.
    if (styleNeedsRebuild(ent, prev)) return false;
    const points = ent.points || [];
    if (points.length < 2) return false; // degenerate → recreate
    if (!mesh.geometry || typeof mesh.geometry.setPositions !== 'function') return false;

    const colored = hasVertexColors(ent);
    const { positions, vertexColors } = flattenPath(
        points,
        ent.colors || [],
        parseColor(ent, '#ffffff')
    );
    rewriteFatLinePositions(mesh.geometry, positions);
    if (colored && vertexColors) mesh.geometry.setColors(vertexColors);
    mesh.geometry.computeBoundingBox();
    mesh.geometry.computeBoundingSphere();
    if (colored) {
        // Vertex colours come from the attributes; the colour block would
        // tint the white base colour, so apply opacity only.
        applyOpacityUpdate(mesh, ent);
    } else {
        applyStyleUpdate(mesh, ent);
    }
    if (mesh.material && mesh.material.dashed) mesh.computeLineDistances();
    return true;
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