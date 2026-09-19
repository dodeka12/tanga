// Tanga Viewer — nice tick computation (port of py/pytanga/viz/_scale.py).
// Pure ES module: no `three`/DOM dependencies, so it is Node-testable and is
// shared by the live viewer and the HTML-export bundle.

const DEFAULT_TICK_FORMAT = '.4g';

/**
 * Format a number using a Python-style format specifier (`.Nf` or `.Ng`).
 * Matches Python's `format(value, fmt)` for the common tick-label cases
 * (integers, simple decimals, and powers of 10).
 *
 * @param {string} fmt  e.g. ".4g" or ".2f"
 * @param {number} value
 * @returns {string}
 */
export function formatValue(fmt, value) {
    const v = Number(value);
    if (!Number.isFinite(v)) return String(value);
    const m = /^\.(\d+)([fFgG])$/.exec(fmt || '');
    if (!m) return String(v);
    const digits = parseInt(m[1], 10);
    const kind = m[2].toLowerCase();
    if (kind === 'f') return v.toFixed(digits);
    return _pyFormatG(v, digits);
}

/**
 * Python `format(v, '.Ng')` — significant digits, fixed vs scientific per the
 * same `-4 <= exp < precision` threshold Python's 'g' uses.
 */
function _pyFormatG(value, precision) {
    if (value === 0) return '0';
    const exp = Math.floor(Math.log10(Math.abs(value)));
    if (exp >= -4 && exp < precision) {
        const decimals = Math.max(0, precision - 1 - exp);
        const s = value.toFixed(decimals);
        if (s.indexOf('.') === -1) return s;
        return s.replace(/\.?0+$/, '');
    }
    const [mantissa, e] = value.toExponential(precision - 1).split('e');
    const ei = Number(e);
    const sign = ei < 0 ? '-' : '+';
    const trimmed = mantissa.replace(/\.?0+$/, '');
    return `${trimmed}e${sign}${String(Math.abs(ei)).padStart(2, '0')}`;
}

/**
 * Normalize an explicit interval list to sorted, positive, de-duplicated
 * values.  Returns `null` for empty/`null` input so callers fall back to the
 * auto-generated 1/2/5 steps.
 *
 * @param {Array<number>|null|undefined} intervals
 * @returns {Array<number>|null}
 */
export function normalizeIntervals(intervals) {
    if (!Array.isArray(intervals) || intervals.length === 0) return null;
    const vals = [...new Set(
        intervals.map(Number).filter((v) => Number.isFinite(v) && v > 0)
    )];
    vals.sort((a, b) => a - b);
    return vals.length ? vals : null;
}

/**
 * Return nice ticks covering `[lo, hi]` (port of `nice_linear_ticks`).
 *
 * Picks the smallest allowed step that is at least `span / maxTicks`.  When
 * `intervals` is given it is the list of allowed absolute step values; when
 * omitted it falls back to the classic 1/2/5 × 10^k steps.
 *
 * @param {number} lo
 * @param {number} hi
 * @param {number} [maxTicks=8]
 * @param {string} [fmt=DEFAULT_TICK_FORMAT]
 * @param {Array<number>|null} [intervals=null]
 * @returns {Array<[number, string]>}
 */
export function niceLinearTicks(lo, hi, maxTicks = 8, fmt = DEFAULT_TICK_FORMAT, intervals = null) {
    let a = Number(lo);
    let b = Number(hi);
    if (a > b) [a, b] = [b, a];
    if (!Number.isFinite(a) || !Number.isFinite(b)) return [];
    const span = b - a;
    if (span === 0) return [[a, formatValue(fmt, a)]];
    if (span < 0) return [];

    const rawStep = span / Math.max(1, Math.floor(Number(maxTicks) || 1));
    const steps = normalizeIntervals(intervals);
    let step;
    if (steps) {
        step = steps.find((s) => s >= rawStep);
        if (step === undefined) step = steps[steps.length - 1];
    } else {
        const magnitude = Math.pow(10, Math.floor(Math.log10(rawStep)));
        step = 10 * magnitude;
        for (const candidate of [1, 2, 5, 10]) {
            if (candidate * magnitude >= rawStep) {
                step = candidate * magnitude;
                break;
            }
        }
    }

    const ticks = [];
    const start = Math.ceil(a / step);
    const epsilon = step * 1e-9;
    let i = 0;
    let value = start * step;
    while (value <= b + epsilon && ticks.length < 1000) {
        // Multiply by an integer index each step (rather than accumulating
        // `t += step`) so the tick at zero lands on exactly 0 instead of a
        // tiny float residue like 3.4e-18.
        ticks.push([value, formatValue(fmt, value)]);
        i += 1;
        value = (start + i) * step;
    }
    return ticks;
}

/**
 * Return integer-power-of-`base` ticks covering `[lo, hi]` (port of
 * `log_ticks`). The range must be strictly positive.
 *
 * @param {number} lo
 * @param {number} hi
 * @param {number} [base=10]
 * @param {string} [fmt=DEFAULT_TICK_FORMAT]
 * @returns {Array<[number, string]>}
 */
export function logTicks(lo, hi, base = 10, fmt = DEFAULT_TICK_FORMAT) {
    let a = Number(lo);
    let b = Number(hi);
    if (a > b) [a, b] = [b, a];
    if (a <= 0) throw new Error(`log scale range must be strictly positive, got ${a}`);
    const bse = Number(base);
    if (!(bse > 1)) throw new Error(`log scale base must be > 1, got ${bse}`);

    const eps = 1e-12;
    const kStart = Math.ceil(Math.log(a) / Math.log(bse) - eps);
    const kEnd = Math.floor(Math.log(b) / Math.log(bse) + eps);

    const ticks = [];
    for (let k = kStart; k <= kEnd; k++) {
        const value = Math.pow(bse, k);
        ticks.push([value, formatValue(fmt, value)]);
    }
    return ticks;
}
