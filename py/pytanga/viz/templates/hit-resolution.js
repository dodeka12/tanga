// SPDX-License-Identifier: Apache-2.0
// Copyright 2021 Christian Perwass
//
// Pure, DOM-free hit-resolution helpers for the interaction controller.
//
// `resolveHitTarget` walks candidate hits nearest→furthest and returns the first
// whose interaction triggers match the gesture; the pane's surface is the
// furthest (background) candidate.  Extracted so the arbitration is unit-testable
// with `node --test` (mirrors the repo convention of keeping pure logic out of
// DOM/WebGL modules).

// Return the subset of `config.triggers` matching the gesture (event type + mouse
// button + held modifiers).  Modifiers match exactly: a trigger with no
// `modifiers` fires only when no modifiers are held (not "any modifier").
export function matchTriggers(config, eventType, button, modifiers) {
    if (!config || !Array.isArray(config.triggers)) return [];
    return config.triggers.filter((t) => {
        if (t.event_type !== eventType) return false;
        if (t.mouse_button != null && t.mouse_button !== button) return false;
        const reqMods = t.modifiers || [];
        if (modifiers.size !== reqMods.length) return false;
        for (const m of reqMods) {
            if (!modifiers.has(m)) return false;
        }
        return true;
    });
}

// Resolve which target receives a gesture.
//
// `candidates` is an ordered (nearest→furthest) list of `{ objectId, intersect }`;
// `surface` is the pane's `{ objectId, intersect }` background candidate (or
// null).  `getConfig(id)` returns the target's interaction config (or null).
// Returns the chosen target or null.
export function resolveHitTarget(candidates, surface, getConfig, eventType, button, modifiers) {
    for (const candidate of candidates || []) {
        const config = getConfig(candidate.objectId);
        if (matchTriggers(config, eventType, button, modifiers).length > 0) {
            return candidate;
        }
    }
    if (surface) {
        const config = getConfig(surface.objectId);
        if (matchTriggers(config, eventType, button, modifiers).length > 0) {
            return surface;
        }
    }
    return null;
}
