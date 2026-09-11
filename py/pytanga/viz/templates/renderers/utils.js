// Shared utilities for Tanga entity/operator renderers.
// Phase 5: Used by per-entity modules and the factory dispatcher.

import * as THREE from 'three';
import { Line2 } from 'three/addons/lines/Line2.js';
import { LineSegments2 } from 'three/addons/lines/LineSegments2.js';
import { LineMaterial } from 'three/addons/lines/LineMaterial.js';
import { LineGeometry } from 'three/addons/lines/LineGeometry.js';
import { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js';
import { styleNeedsRebuild } from './style-diff.js';
import { sendLog } from '../events.js';

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

// ── Fat lines (screen-space width) ──────────────────────────
//
// THREE.Line + LineBasicMaterial cannot vary their width: WebGL caps line
// width at 1px on most platforms.  For axes/grid overlays we instead use
// three.js `Line2` fat lines, whose `linewidth` is expressed in
// screen-space pixels (worldUnits: false) and therefore stays constant
// on screen regardless of zoom.

function _lineResolution() {
    const pr = (typeof window !== 'undefined' && window.devicePixelRatio) || 1;
    const w = (typeof window !== 'undefined' ? window.innerWidth : 1) * pr;
    const h = (typeof window !== 'undefined' ? window.innerHeight : 1) * pr;
    return new THREE.Vector2(Math.max(1, w), Math.max(1, h));
}

/**
 * Create a LineMaterial for a three.js `Line2` fat line.
 *
 * @param {string|THREE.Color} color
 * @param {number} opacity - 0..1
 * @param {number} lineWidth - line width in screen-space pixels
 * @returns {THREE.ShaderMaterial}
 */
const _lineMaterials = new Set();

export function makeLineMaterial(color, opacity = 1.0, lineWidth = 1.0, options = {}) {
    const c = typeof color === 'string' ? new THREE.Color(color) : color;
    const material = new LineMaterial({
        color: c,
        linewidth: Math.max(0.1, lineWidth),
        worldUnits: false,
        transparent: opacity < 1.0,
        opacity,
        depthWrite: opacity >= 0.99,
        resolution: _lineResolution(),
        vertexColors: !!options.vertexColors,
    });
    if (options.dashed) {
        material.dashed = true;
        material.dashSize = options.dashSize ?? 4;
        material.gapSize = options.gapSize ?? 2;
        material.dashScale = options.dashScale ?? 1;
    }
    _lineMaterials.add(material);
    return material;
}

/**
 * Recompute the screen resolution for every registered LineMaterial.
 * Called on window resize / screenshot capture so screen-space line widths
 * stay correct when the drawing buffer size changes.
 */
export function updateLineResolutions() {
    const res = _lineResolution();
    for (const m of _lineMaterials) {
        m.resolution.copy(res);
    }
}

function _flattenPoints(points) {
    const out = [];
    for (const p of points) out.push(p.x, p.y, p.z);
    return out;
}

function _flattenSegments(segments) {
    const out = [];
    for (const [a, b] of segments) out.push(a.x, a.y, a.z, b.x, b.y, b.z);
    return out;
}

/**
 * Create a `Line2` fat line through the given points.
 *
 * @param {THREE.Vector3[]} points
 * @param {string|THREE.Color} color
 * @param {number} opacity
 * @param {number} lineWidth - screen-space pixel width
 * @returns {Line2}
 */
export function makeFatLine(points, color, opacity = 1.0, lineWidth = 1.0) {
    const material = makeLineMaterial(color, opacity, lineWidth);
    const geometry = new LineGeometry();
    geometry.setPositions(_flattenPoints(points));
    return new Line2(geometry, material);
}

/**
 * Create a `Line2` fat line reusing an existing LineMaterial.
 *
 * @param {THREE.Vector3[]} points
 * @param {THREE.ShaderMaterial} material - a LineMaterial
 * @returns {Line2}
 */
export function makeFatLineWithMaterial(points, material) {
    const geometry = new LineGeometry();
    geometry.setPositions(_flattenPoints(points));
    return new Line2(geometry, material);
}

/**
 * Create a `LineSegments2` fat line from independent start/end segment pairs.
 *
 * @param {[THREE.Vector3, THREE.Vector3][]} segments
 * @param {string|THREE.Color} color
 * @param {number} opacity
 * @param {number} lineWidth - screen-space pixel width
 * @returns {LineSegments2}
 */
function _finalizeSegmentsLine(geometry, material) {
    const line = new LineSegments2(geometry, material);
    if (material.dashed) line.computeLineDistances();
    return line;
}

export function makeFatSegments(segments, color, opacity = 1.0, lineWidth = 1.0) {
    const material = makeLineMaterial(color, opacity, lineWidth);
    return makeFatSegmentsWithMaterial(segments, material);
}

/**
 * Create a `LineSegments2` fat line reusing an existing LineMaterial.
 *
 * @param {[THREE.Vector3, THREE.Vector3][]} segments
 * @param {THREE.ShaderMaterial} material - a LineMaterial
 * @returns {LineSegments2}
 */
export function makeFatSegmentsWithMaterial(segments, material) {
    const geometry = new LineSegmentsGeometry();
    geometry.setPositions(_flattenSegments(segments));
    return _finalizeSegmentsLine(geometry, material);
}

/**
 * Create a `LineSegments2` fat line from flat [x,y,z, x,y,z, ...] pair data.
 *
 * @param {number[]|Float32Array} flatPositions - consecutive start/end pairs
 * @param {string|THREE.Color} color
 * @param {number} opacity
 * @param {number} lineWidth - screen-space pixel width
 * @returns {LineSegments2}
 */
export function makeFatSegmentsFromFlat(flatPositions, color, opacity = 1.0, lineWidth = 1.0) {
    const material = makeLineMaterial(color, opacity, lineWidth);
    const geometry = new LineSegmentsGeometry();
    geometry.setPositions(flatPositions);
    return _finalizeSegmentsLine(geometry, material);
}

/**
 * Create a `LineSegments2` fat line from flat positions reusing a material.
 *
 * @param {number[]|Float32Array} flatPositions - consecutive start/end pairs
 * @param {THREE.ShaderMaterial} material - a LineMaterial
 * @returns {LineSegments2}
 */
export function makeFatSegmentsFromFlatWithMaterial(flatPositions, material) {
    const geometry = new LineSegmentsGeometry();
    geometry.setPositions(flatPositions);
    return _finalizeSegmentsLine(geometry, material);
}

/**
 * Create a `LineSegments2` fat line with per-segment start/end colors.
 *
 * @param {number[]|Float32Array} flatPositions - consecutive start/end pairs
 * @param {number[]|Float32Array} flatColors - flat [r,g,b, r,g,b, ...] per vertex
 * @param {number} opacity
 * @param {number} lineWidth - screen-space pixel width
 * @returns {LineSegments2}
 */
export function makeFatSegmentsColored(flatPositions, flatColors, opacity = 1.0, lineWidth = 1.0) {
    const material = makeLineMaterial('#ffffff', opacity, lineWidth, { vertexColors: true });
    const geometry = new LineSegmentsGeometry();
    geometry.setPositions(flatPositions);
    geometry.setColors(flatColors);
    return _finalizeSegmentsLine(geometry, material);
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
    // Preserve any renderer-specific userData (e.g. an SDF proxy's `sdfKind`)
    // while tagging the standard entity id/kind/data.
    const prev = mesh.userData || {};
    mesh.userData = { ...prev, entityId: ent.id, kind: ent.kind, data: ent };
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
 * Numeric equality within a small absolute tolerance.
 */
export function approxEqual(a, b, eps = 1e-9) {
    return Math.abs(a - b) < eps;
}

/**
 * Apply the common, non-structural style fields (opacity, color, scale) to a
 * mesh and its children.  Used by the shared update dispatcher and by
 * per-entity updaters so the mutations are defined in one place.
 */
export function applyStyleUpdate(mesh, ent) {
    const opacity = styleParam(ent, 'opacity', undefined);
    if (opacity !== undefined) {
        mesh.traverse((child) => {
            if (child.material && child.material.opacity !== undefined) {
                child.material.opacity = opacity;
                child.material.transparent = opacity < 1.0;
                child.material.depthWrite = opacity >= 0.99;
                child.material.needsUpdate = true;
            }
        });
    }

    const color = styleParam(ent, 'color', null);
    if (color) {
        const c = new THREE.Color(color);
        mesh.traverse((child) => {
            if (child.material && child.material.color) {
                child.material.color.copy(c);
            }
        });
    }

    if (ent.scale) {
        mesh.scale.set(ent.scale[0], ent.scale[1], ent.scale[2]);
    }
}

/**
 * Return true when an entity whose geometry derives directly from its fields
 * must be rebuilt rather than updated in place.
 *
 * ``prev`` is the previously applied merged entity dict (may be undefined for
 * a brand-new entity; callers invoking this on an in-place path always have it).
 */
export function entityRequiresRebuild(ent, prev) {
    if (ent.kind === 'PointPath') return true;
    // SDF proxies: only structural changes (tree/sdfKind) rebuild the shader;
    // member-transform changes (an SdfGroup) and style-only changes are applied
    // in place by updateSdfProxy (which also resizes the proxy box).
    if (ent.kind === 'sdf') {
        if (!prev) return false;
        if (ent.sdfKind !== prev.sdfKind) return true;
        if (JSON.stringify(ent.tree) !== JSON.stringify(prev.tree)) return true;
        return false;
    }
    // Axes/grids are drawn fresh (axis line + CSS2D value labels; many grid
    // segments) and their geometry derives from many fields, so rebuild whenever
    // their content changes — e.g. a live time axis whose ticks move each frame.
    if (ent.kind === 'Axis' || ent.kind === 'Axes2D' || ent.kind === 'Axes3D') return true;
    if (ent.kind === 'Grid') return true;
    if (ent.radius !== undefined && (!prev || !approxEqual(ent.radius, prev.radius))) return true;
    if (ent.alignCenter !== undefined && (!prev || !approxEqual(ent.alignCenter, prev.alignCenter))) return true;
    if (ent.extent !== undefined && (!prev || !approxEqual(ent.extent, prev.extent))) return true;
    if (ent.length !== undefined && (!prev || !approxEqual(ent.length, prev.length))) return true;
    if (ent.tubeRadius !== undefined && (!prev || !approxEqual(ent.tubeRadius, prev.tubeRadius))) return true;
    if (ent.angle !== undefined && (!prev || !approxEqual(ent.angle, prev.angle))) return true;
    if (ent.span_u !== undefined || ent.span_v !== undefined) {
        const a = JSON.stringify([ent.span_u ?? null, ent.span_v ?? null]);
        const b = JSON.stringify([prev?.span_u ?? null, prev?.span_v ?? null]);
        if (!prev || a !== b) return true;
    }
    if (ent.arrow !== undefined) {
        const a = JSON.stringify(ent.arrow ?? null);
        const b = JSON.stringify(prev?.arrow ?? null);
        if (!prev || a !== b) return true;
    }
    // ── Creation-only geometry fields ──────────────────────────────────────
    // These are read only by the per-kind create*() renderers and are never
    // re-applied by the generic in-place update path, so a change must rebuild
    // the mesh. (`rotation` is intentionally absent: it is applied in place by
    // updateEntityMesh for meshes that carry a top-level Euler triple, keeping
    // rotation-only animation updates rebuild-free.)
    for (const key of ['size', 'radii', 'normal', 'axis', 'startDirection', 'point', 'pointA', 'pointB', 'origin']) {
        if (ent[key] !== undefined &&
            (!prev || JSON.stringify(ent[key]) !== JSON.stringify(prev[key]))) {
            return true;
        }
    }
    for (const key of ['radiusU', 'radiusV', 'sides', 'discRadius', 'ringCount', 'maxRadius', 'pointSize']) {
        if (ent[key] !== undefined && (!prev || !approxEqual(ent[key], prev[key]))) {
            return true;
        }
    }
    // Motor nests its rotor/translator parameters; compare them structurally.
    if (ent.rotor !== undefined || ent.translator !== undefined) {
        if (!prev ||
            JSON.stringify(ent.rotor ?? null) !== JSON.stringify(prev.rotor ?? null) ||
            JSON.stringify(ent.translator ?? null) !== JSON.stringify(prev.translator ?? null)) {
            return true;
        }
    }
    if (ent.kind !== undefined && ent.kind !== prev?.kind) return true;
    // Any style field other than color/opacity must rebuild, so the per-kind
    // renderer re-reads every style parameter (size, thickness, wireframe,
    // dash patterns, texture labels, double-sided, …).
    if (styleNeedsRebuild(ent, prev)) return true;
    return false;
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
 * Build the shared rotor visualization (disc arc, outer torus, and axis line)
 * in local coordinates with the rotation axis along local +Z. Callers rotate
 * and position the returned group.
 */
export function buildRotorVisual(color, opacity, lineWidth, angle, discRadius) {
    const col = typeof color === 'string' ? new THREE.Color(color) : color;
    const dr = discRadius;
    const absA = Math.abs(angle);
    const segs = Math.max(8, Math.ceil(absA / (Math.PI / 32)));
    const g = new THREE.Group();

    // Disc arc swept by the rotation angle
    g.add(
        new THREE.Mesh(
            new THREE.RingGeometry(dr * 0.15, dr, segs, 1, 0, absA),
            new THREE.MeshBasicMaterial({
                color: col,
                opacity: opacity * 0.8,
                transparent: true,
                side: THREE.DoubleSide,
                depthWrite: false,
            })
        )
    );

    // Outer torus (full circle)
    g.add(
        new THREE.Mesh(
            new THREE.TorusGeometry(dr, 0.03, 16, 64),
            makeMaterial(col, opacity * 0.5)
        )
    );

    // Axis line
    const al = dr * 1.6;
    g.add(
        makeFatLine(
            [new THREE.Vector3(0, 0, -al), new THREE.Vector3(0, 0, al)],
            col,
            opacity,
            lineWidth
        )
    );

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
    const flatPositions = wireGeo.attributes.position.array;
    const useDash = dashPattern && dashPattern.dash_size > 0;
    const material = makeLineMaterial(
        color,
        opacity,
        1.0,
        useDash
            ? {
                dashed: true,
                dashSize: dashPattern.dash_size,
                gapSize: dashPattern.gap_size,
                dashScale: dashPattern.scale || 1.0,
            }
            : {}
    );
    const lines = makeFatSegmentsFromFlatWithMaterial(flatPositions, material);
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


// ── Texture Label Utilities ──────────────────────────────────


/**
 * Check whether a string contains $...$ (inline) or $$...$$ (display)
 * math delimiters.  Used to decide between plain-text and mixed
 * rendering modes.
 *
 * A single unpaired ``$`` is treated as plain text (no mixed mode).
 *
 * @param {string} text
 * @returns {boolean}
 */
export function hasMathDelimiters(text) {
    // Must have at least one pair of $$ or $
    return /\$\$/.test(text) || /\$[^$]+\$/.test(text);
}


/**
 * Render text (plain or with ``$...$`` / ``$$...$$`` KaTeX delimiters)
 * onto a canvas via a DOM element + ``html2canvas`` capture.
 *
 * @param {CanvasRenderingContext2D} ctx - Target canvas 2D context.
 * @param {string} text - Text with optional ``$`` / ``$$`` KaTeX delimiters.
 * @param {number} width - Target canvas width.
 * @param {number} height - Target canvas height.
 * @param {number} fontSize - Font size in px for plain text portions.
 * @param {string} color - CSS text color.
 * @returns {Promise<void>}
 */
async function renderToCanvas(ctx, text, width, height, fontSize, color) {
    if (typeof html2canvas === 'undefined') {
        throw new Error('html2canvas not available');
    }

    const div = document.createElement('div');
    div.style.position = 'absolute';
    div.style.left = '0px';
    div.style.top = '0px';
    div.style.width = width + 'px';
    div.style.height = height + 'px';
    div.style.display = 'flex';
    div.style.flexDirection = 'column';
    div.style.alignItems = 'center';
    div.style.justifyContent = 'center';
    div.style.color = color;
    div.style.fontFamily = 'sans-serif';
    div.style.fontSize = fontSize + 'px';
    div.style.lineHeight = '1.5';
    div.style.padding = '20px';
    div.style.boxSizing = 'border-box';
    div.style.background = 'transparent';
    div.style.overflow = 'hidden';
    div.innerHTML = text;

    document.body.appendChild(div);

    try {
        if (typeof renderMathInElement !== 'undefined') {
            renderMathInElement(div, {
                delimiters: [
                    { left: '$$', right: '$$', display: true },
                    { left: '$', right: '$', display: false },
                ],
                throwOnError: false,
            });
        }

        const capture = await html2canvas(div, {
            backgroundColor: null,
            scale: 1,
            width: width,
            height: height,
        });
        ctx.drawImage(capture, 0, 0);
    } finally {
        document.body.removeChild(div);
    }
}


/**
 * Render plain text centered on the canvas.
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {string} text
 * @param {number} width
 * @param {number} height
 * @param {number} fontSize
 * @param {string} color
 */
function drawPlainText(ctx, text, width, height, fontSize, color) {
    ctx.fillStyle = color;
    ctx.font = `${fontSize}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, width / 2, height / 2);
}


/**
 * Create a THREE.CanvasTexture from a label string and texture label style.
 *
 * Two modes:
 * - Text contains ``$...$`` / ``$$...$$`` delimiters: rendered via DOM +
 *   ``renderMathInElement`` + ``html2canvas`` capture.
 * - Plain text: drawn directly on canvas with ``ctx.fillText()``.
 *
 * Returns ``null`` if text is falsy or rendering fails.
 *
 * @param {string|null|undefined} text - The label content.
 * @param {object} style - TextureLabelStyle dict from the entity's style.
 *        Expected keys: repeat_u, repeat_v, offset_u, offset_v,
 *        background, resolution, color, font_size.
 * @returns {Promise<THREE.CanvasTexture|null>}
 */
export async function createTextureLabel(text, style) {
    if (!text) return null;

    const color = style.color || '#000000';
    const s = style.scale || 1.0;
    const a = style.aspect || 1.0;
    const repeatU = style.repeat_u || 1;
    const repeatV = style.repeat_v || 1;

    // Cell size: each tile gets contentW×contentH pixels.
    // Larger resolution = sharper, larger scale = larger text.
    const baseW = style.resolution || 512;
    const contentW = Math.floor(baseW / repeatU);
    const contentH = Math.floor(baseW / repeatV / 2);

    // Scale/aspect applied to font size, not canvas size.
    // scale=2 → text is 2× larger, aspect=0.5 → half as tall.
    const scaledFontSize = Math.round((style.font_size || 48) * s);

    const canvas = document.createElement('canvas');
    canvas.width = contentW;
    canvas.height = contentH;
    const ctx = canvas.getContext('2d');

    // Background fill
    const bg = (style.background && style.background !== 'transparent')
        ? style.background
        : '#ffffff';
    ctx.fillStyle = bg;
    ctx.fillRect(0, 0, contentW, contentH);

    // Apply aspect as vertical canvas scale so content is compressed
    // taller or shorter relative to the cell height.
    ctx.save();
    if (a !== 1.0) {
        ctx.translate(0, contentH * (1 - a) / 2);
        ctx.scale(1, a);
    }

    try {
        if (hasMathDelimiters(text)) {
            if (typeof html2canvas === 'undefined') {
                // Math delimiters are present but html2canvas (which rasterizes
                // the KaTeX DOM into the canvas) is unavailable.  Fall back to
                // drawing the raw source text so the label is not silently
                // dropped — plain text renders without html2canvas.
                drawPlainText(ctx, text, contentW, contentH, scaledFontSize, color);
            } else {
                await renderToCanvas(ctx, text, contentW, contentH, scaledFontSize, color);
            }
        } else {
            drawPlainText(ctx, text, contentW, contentH, scaledFontSize, color);
        }
    } catch (err) {
        console.warn('createTextureLabel: rendering failed', err);
        sendLog('warn', 'createTextureLabel: rendering failed', { source: 'utils.js', data: { error: String(err) } });
        ctx.restore();
        return null;
    }
    ctx.restore();

    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;

    if (repeatU > 1 || repeatV > 1) {
        texture.wrapS = THREE.RepeatWrapping;
        texture.wrapT = THREE.RepeatWrapping;
        texture.repeat.set(repeatU, repeatV);
    }

    const offsetU = style.offset_u;
    const offsetV = style.offset_v;
    if (offsetU || offsetV) {
        texture.offset.set(offsetU || 0, offsetV || 0);
    }

    return texture;
}
