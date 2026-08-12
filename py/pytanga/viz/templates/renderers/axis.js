// Axis renderer — a coordinate axis with ticks and optional CSS2D value labels.
// Renders a line from `start` to `end`, perpendicular tick marks at major/
// minor intervals, and value labels at major intervals.

import * as THREE from 'three';
import { CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { makeMaterial, parseColor, styleParam, tagEntity } from './utils.js';

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

export function createAxis(ent) {
    const group = new THREE.Group();

    const start = new THREE.Vector3(...(ent.start || [0, 0, 0]));
    const end = new THREE.Vector3(...(ent.end || [1, 0, 0]));
    const dir = end.clone().sub(start);
    const length = dir.length();
    if (length < 1e-9) return group;
    dir.normalize();

    const color = parseColor(ent, '#888888');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const major = Math.abs(ent.majorInterval || 1.0);
    const minor = ent.minorInterval != null ? Math.abs(ent.minorInterval) : null;
    const labelAtMajor = ent.labelAtMajor !== false;
    const labelFormat = ent.labelFormat || '.1f';
    const decimals = _parseDecimals(labelFormat);
    const labelSize = ent.labelSize || 12;
    const showTicks = ent.showTicks !== false;

    const perp = perpendicularTo(dir);
    const tickLen = Math.max(length * 0.02, styleParam(ent, 'line_thickness', 0.03) * 4);

    const lineMaterial = makeMaterial(color, opacity);

    function addSegment(a, b) {
        const geo = new THREE.BufferGeometry().setFromPoints([a, b]);
        const line = new THREE.Line(geo, lineMaterial);
        line.renderOrder = 1;
        group.add(line);
        return line;
    }

    function formatValue(value) {
        if (Number.isInteger(value)) return String(value);
        return value.toFixed(decimals);
    }

    // Main axis line
    addSegment(start, end);

    // Ticks
    if (showTicks && major > 0) {
        const majorIntervals = Math.floor(length / major);

        for (let i = 1; i <= majorIntervals; i++) {
            const t = i * major;
            const p = start.clone().addScaledVector(dir, t);

            // Major tick + optional value label
            const ma = p.clone().addScaledVector(perp, tickLen);
            const mb = p.clone().addScaledVector(perp, -tickLen);
            addSegment(ma, mb, tickLen);

            if (labelAtMajor) {
                const value = i * major;
                const div = document.createElement('div');
                div.textContent = formatValue(value);
                div.style.color = typeof color === 'string' ? color : '#' + color.getHexString();
                div.style.fontSize = labelSize + 'px';
                div.style.fontFamily = 'sans-serif';
                div.style.textShadow = '0 0 4px rgba(0,0,0,0.8)';
                div.style.pointerEvents = 'none';
                const label = new CSS2DObject(div);
                label.position.copy(p).addScaledVector(perp, tickLen * 2.5);
                group.add(label);
            }
        }

        // Minor ticks
        if (minor && minor > 0 && minor < major) {
            const minorIntervals = Math.floor(length / minor);
            const halfLen = tickLen * 0.5;
            for (let i = 1; i <= minorIntervals; i++) {
                // Skip positions that coincide with a major tick
                if (Math.abs(i * minor % major) < 1e-6) continue;
                const t = i * minor;
                const p = start.clone().addScaledVector(dir, t);
                const ma = p.clone().addScaledVector(perp, halfLen);
                const mb = p.clone().addScaledVector(perp, -halfLen);
                addSegment(ma, mb, halfLen);
            }
        }
    }

    // Optional axis name label at the end
    if (ent.label) {
        const div = document.createElement('div');
        div.textContent = ent.label;
        div.style.color = typeof color === 'string' ? color : '#' + color.getHexString();
        div.style.fontSize = Math.round(labelSize * 1.15) + 'px';
        div.style.fontWeight = 'bold';
        div.style.fontFamily = 'sans-serif';
        div.style.textShadow = '0 0 4px rgba(0,0,0,0.8)';
        div.style.pointerEvents = 'none';
        const label = new CSS2DObject(div);
        label.position.copy(end).addScaledVector(dir, tickLen * 3);
        group.add(label);
    }

    tagEntity(group, ent);
    return group;
}