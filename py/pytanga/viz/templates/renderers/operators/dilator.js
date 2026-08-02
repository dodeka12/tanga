// Dilator renderer — concentric expanding rings.
// Phase 6: Moved from inline factory.js to dedicated operator module.

import { styleParam, parseColor, createDilatorRings } from '../utils.js';


export function createDilator(ent) {
    return createDilatorRings(
        parseColor(ent, '#ffcc44'),
        styleParam(ent, 'opacity', 0.6),
        ent.ringCount || 4,
        ent.maxRadius || 3.0,
        ent.origin || [0, 0, 0]
    );
}