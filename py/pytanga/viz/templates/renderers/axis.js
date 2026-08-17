// Axis renderer — a coordinate axis line with optional value labels and a
// name label placed at the end of the axis.  No tick marks are drawn.

import * as THREE from 'three';
import { CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { makeFatLine, parseColor, styleParam } from './utils.js';

/**
 * Parse a Python-style float format specifier (e.g. ".2f") into a number of
 * decimal places.  Returns 1 for unrecognised formats.
 */
function _parseDecimals(fmt) {
    const m = /^\.(\d+)f$/.exec(fmt);
    return m ? parseInt(m[1], 10) : 1;
}

/**
 * Compute a normalized vector perpendicular to `v`.
 * The result is deterministic (no randomness).
 */
function perpendicularTo(v) {
    const x = Math.abs(v.x), y = Math.abs(v.y), z = Math.abs(v.z);
    if (x <= y && x <= z) {
        return new THREE.Vector3(0, -v.z, v.y).normalize();
    }
    if (y <= x && y <= z) {
        return new THREE.Vector3(-v.z, 0, v.x).normalize();
    }
    return new THREE.Vector3(-v.y, v.x, 0).normalize();
}

/**
 * Draw a single coordinate axis into `group`.
 *
 * `axis` is a JSON dict with the same shape as a standalone Axis entity:
 * `start`, `end`, `majorInterval`, `labelAtMajor`, `labelFormat`, `labelSize`,
 * `valueStart`, `valueStep`, `label`, and a resolved `style` (plus optional
 * flat `color`/`opacity`).
 *
 * The value labels are controlled by ``axis.style.label_style`` (a
 * ``LabelStyle`` dict with ``font_size``, ``color``, ``align``,
 * ``offset_2d`` and ``offset_local``) and ``axis.style.label_at_major``.
 * These are shared by `createAxis`, `createAxes2D`, and `createAxes3D` so
 * every axis is drawn identically.  `offset_local` is applied in the axis
 * local frame: x = along the axis, y = perpendicular (label separation),
 * z = binormal (``cross(dir, perp)``).
 */
export function addAxis(group, axis) {
    const start = new THREE.Vector3(...(axis.start || [0, 0, 0]));
    const end = new THREE.Vector3(...(axis.end || [1, 0, 0]));
    const dir = end.clone().sub(start);
    const length = dir.length();
    if (length < 1e-9) return;
    dir.normalize();

    const color = parseColor(axis, '#888888');
    const colorHex = typeof color === 'string' ? color : '#' + color.getHexString();
    const opacity = styleParam(axis, 'opacity', 0.9);
    const lineWidth = styleParam(axis, 'line_thickness', 1);
    const major = Math.abs(axis.majorInterval || 1.0);

    // Value-label style (LabelStyle dict embedded in the resolved Axis style).
    const labelStyle = (axis.style && axis.style.label_style) || {};
    const labelAtMajor = axis.style && axis.style.label_at_major !== undefined
        ? axis.style.label_at_major
        : axis.labelAtMajor !== false;

    const labelFormat = axis.labelFormat || '.1f';
    const decimals = _parseDecimals(labelFormat);
    const labelSize = axis.labelSize || 12;
    const valueLabelSize = labelStyle.font_size ?? labelSize;
    const valueLabelColor = labelStyle.color ?? colorHex;
    const valueStart = axis.valueStart != null ? axis.valueStart : 0.0;
    const valueStep = axis.valueStep != null ? axis.valueStep : 1.0;

    const perp = perpendicularTo(dir);
    const binormal = new THREE.Vector3().crossVectors(dir, perp).normalize();

    // Baseline perpendicular separation between the axis line and its value
    // labels.  Zero so that with no explicit offset the label centre lies
    // exactly on the axis; use LabelStyle.offset_local to move it further.
    const valueLabelOffset = 0.0;

    // 3D label offset in the axis local frame:
    //   [0] along the axis, [1] perpendicular separation, [2] binormal.
    const offLocal = labelStyle.offset_local || [0, 0, 0];

    function addSegment(a, b) {
        const line = makeFatLine([a, b], color, opacity, lineWidth);
        group.add(line);
        return line;
    }

    function formatValue(value) {
        if (Number.isInteger(value)) return String(value);
        return value.toFixed(decimals);
    }

    function makeLabel(text, opts = {}) {
        const {
            bold = false,
            fontSize = labelSize,
            fontColor = colorHex,
            align = null,
            offset = null,
            rotation = 0,
        } = opts;

        const content = document.createElement('div');
        content.textContent = text;
        content.style.color = fontColor;
        content.style.fontSize = Math.round(fontSize * (bold ? 1.15 : 1.0)) + 'px';
        content.style.fontFamily = 'sans-serif';
        if (bold) content.style.fontWeight = 'bold';
        content.style.textShadow = '0 0 4px rgba(0,0,0,0.8)';
        content.style.pointerEvents = 'none';
        content.style.whiteSpace = 'nowrap';

        const ax = align ? align[0] : 0.5;
        const ay = align ? align[1] : 0.5;
        const ox = offset ? offset[0] : 0;
        const oy = offset ? offset[1] : 0;
        const tx = (0.5 - ax) * 100;
        const ty = (0.5 - ay) * 100;
        content.style.transformOrigin = `${ax * 100}% ${ay * 100}%`;
        content.style.transform = `translate(${ox}px, ${oy}px) translate(${tx}%, ${ty}%) rotate(${rotation}deg)`;

        // CSS2DRenderer repositions the element it wraps each frame, so the
        // styled content must be nested inside an outer element.  Otherwise
        // the align/offset transform on `content` would be overwritten.
        const wrapper = document.createElement('div');
        wrapper.style.pointerEvents = 'none';
        wrapper.appendChild(content);
        return new CSS2DObject(wrapper);
    }

    // Axis line
    addSegment(start, end);

    // Value labels at major intervals (no tick marks).
    if (labelAtMajor && major > 0) {
        const count = Math.floor(length / major);
        for (let i = 1; i <= count; i++) {
            const t = i * major;
            const value = valueStart + i * major * valueStep;
            const p = start.clone().addScaledVector(dir, t);
            const labelPos = p.clone()
                .addScaledVector(dir, offLocal[0] || 0)
                .addScaledVector(perp, (offLocal[1] || 0) + valueLabelOffset)
                .addScaledVector(binormal, offLocal[2] || 0);

            const label = makeLabel(formatValue(value), {
                fontSize: valueLabelSize,
                fontColor: valueLabelColor,
                align: labelStyle.align || null,
                offset: labelStyle.offset_2d || null,
                rotation: labelStyle.rotation || 0,
            });
            label.position.copy(labelPos);
            group.add(label);
        }
    }

    // Axis name label at the end of the axis.
    if (axis.label) {
        const label = makeLabel(axis.label, { bold: true });
        label.position.copy(end);
        group.add(label);
    }
}

/**
 * Create a standalone Axis entity (one line with its own style).
 */
export function createAxis(ent) {
    const group = new THREE.Group();
    addAxis(group, ent);
    return group;
}