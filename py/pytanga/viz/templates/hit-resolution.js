// SPDX-License-Identifier: Apache-2.0
// Copyright 2021 Christian Perwass
//
// Pure, DOM-free hit-resolution helpers for the interaction controller.
//
// `orderHitCandidates` puts the raycast hits in pick order (explicit
// `hit_priority` desc → screen-space marker → distance asc → input order);
// `resolveHitTarget` then walks that order and returns the first candidate
// whose interaction triggers match the gesture, falling back to the pane's
// surface (the background candidate).  Extracted so the arbitration is
// unit-testable with `node --test` (mirrors the repo convention of keeping pure
// logic out of DOM/WebGL modules).

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

// Pick precedence of one interaction config.  Missing/NaN => 0, so an older
// backend payload (no `hit_priority`) keeps today's behaviour.
export function hitPriority(config) {
    const value = config ? config.hit_priority : 0;
    return Number.isFinite(value) ? value : 0;
}

// Order candidates best-first: hit_priority desc → screen-space marker before
// world-space body → distance asc → input order (stable).
//
// A candidate is `{ objectId, intersect, screenSpace }`; `getConfig(id)`
// returns the target's interaction config (or null).
export function orderHitCandidates(candidates, getConfig) {
    return (candidates || [])
        .map((candidate, index) => ({ candidate, index }))
        .sort((a, b) => {
            const pa = hitPriority(getConfig(a.candidate.objectId));
            const pb = hitPriority(getConfig(b.candidate.objectId));
            if (pa !== pb) return pb - pa;
            const sa = a.candidate.screenSpace ? 1 : 0;
            const sb = b.candidate.screenSpace ? 1 : 0;
            if (sa !== sb) return sb - sa;
            const da = a.candidate.intersect?.distance ?? Infinity;
            const db = b.candidate.intersect?.distance ?? Infinity;
            if (da !== db) return da - db;
            return a.index - b.index;
        })
        .map((entry) => entry.candidate);
}

// Resolve which target receives a gesture.
//
// `candidates` is a best-first list of `{ objectId, intersect }` as produced by
// `orderHitCandidates`; `surface` is the pane's `{ objectId, intersect }`
// background candidate (or null).  `getConfig(id)` returns the target's
// interaction config (or null).  Returns the chosen target or null.
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
