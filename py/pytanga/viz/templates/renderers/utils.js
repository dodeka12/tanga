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
            await renderToCanvas(ctx, text, contentW, contentH, scaledFontSize, color);
        } else {
            drawPlainText(ctx, text, contentW, contentH, scaledFontSize, color);
        }
    } catch (err) {
        console.warn('createTextureLabel: rendering failed', err);
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
