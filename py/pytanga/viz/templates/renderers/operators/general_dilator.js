// GeneralDilator renderer — expanding rings + optional translation arrow.
// Phase 6: Moved from inline factory.js to dedicated operator module.

import { styleParam,  parseColor, createArrow, createDilatorRings } from '../utils.js';


export function createGeneralDilator(ent) {
    const color = parseColor(ent, '#ffcc88');
    const opacity = styleParam(ent, 'opacity', 0.6);
    const g = createDilatorRings(
        color,
        opacity,
        ent.ringCount || 4,
        ent.maxRadius || 3.0,
        ent.origin || [0, 0, 0]
    );
    if (ent.translator) {
        const tv = ent.translator.vector || [1, 0, 0];
        const tl =
            Math.sqrt(tv[0] ** 2 + tv[1] ** 2 + tv[2] ** 2) * 1.5;
        const arrowG = createArrow(color, 0.7, tv, tl, [0, 0, 0]);
        g.add(arrowG);
    }
    return g;
}