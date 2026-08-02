// Translator renderer — arrow (cylinder shaft + cone head).
// Phase 6: Moved from inline factory.js to dedicated operator module.

import { styleParam,  parseColor, createArrow } from '../utils.js';


export function createTranslator(ent) {
    const color = parseColor(ent, '#44aaff');
    const opacity = styleParam(ent, 'opacity', 0.9);
    const vec = ent.vector || [1, 0, 0];
    const len = ent.length || 3.0;
    return createArrow(color, opacity, vec, len, ent.origin || [0, 0, 0]);
}