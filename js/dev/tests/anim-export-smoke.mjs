// Tanga — headless Playwright smoke for animated-export frame churn (manual, not CI).
// Run `uv run python js/dev/tests/serve-anim-export-smoke.py` first, then:
//   node js/dev/tests/anim-export-smoke.mjs <base-url>
import { chromium } from 'playwright';

const base = process.argv[2] || process.env.SMOKE_URL;
if (!base) {
    console.error('usage: node anim-export-smoke.mjs <base-url>');
    process.exit(2);
}

const browser = await chromium.launch({
    // Playwright's bundled Chromium (installed via `npx playwright install chromium`);
    // identical on Linux and Windows. No `channel` — that would use a system browser.
    headless: true,
    args: ['--enable-unsafe-swiftshader', '--use-angle=swiftshader'],
});

const consoleErrors = [];
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
page.on('pageerror', (e) => consoleErrors.push(String(e)));

// Wrap the export's `window.__tanga` bridge with counters *before* the page
// scripts run.  The export assigns the bridge once (`window.__tanga = {…}`),
// so a setter lets us instrument without touching the export.
await page.addInitScript(() => {
    window.__smoke = { created: 0, updated: 0, removed: 0 };
    let _tanga;
    Object.defineProperty(window, '__tanga', {
        configurable: true,
        get: () => _tanga,
        set: (v) => {
            const wrap = (name, key) => {
                const fn = v[name];
                v[name] = (...a) => { window.__smoke[key] += 1; return fn(...a); };
            };
            wrap('buildSceneObject', 'created');
            wrap('updateEntityMesh', 'updated');
            wrap('removeEntityMesh', 'removed');
            _tanga = v;
            window.__smoke.ready = true;
        },
    });
});

await page.goto(base, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('#tanga-play-btn', { timeout: 30000 });
await page.waitForFunction(() => window.__smoke && window.__smoke.ready === true);

// Wait for the first frame to be on screen: the scrub bar is initialised to
// frame 0 with its max = frame_count - 1, and the bridge has been wrapped.
await page.waitForFunction(() => {
    const scrub = document.getElementById('tanga-scrub');
    return scrub && scrub.value === '0' && Number(scrub.max) > 0;
}, { timeout: 15000 });
await page.waitForTimeout(500);

const counters = () => page.evaluate(() => ({ ...window.__smoke }));
const before = await counters();
const labelsBefore = await page.evaluate(() =>
    document.querySelectorAll('div[style*="pointer-events: none"]').length);

await page.click('#tanga-play-btn');

// loop=False → playback stops at the last frame: the button flips back to ▶.
await page.waitForFunction(() => {
    const btn = document.getElementById('tanga-play-btn');
    const scrub = document.getElementById('tanga-scrub');
    return (btn && btn.textContent.includes('▶')) || (scrub && scrub.value === scrub.max);
}, { timeout: 30000 });

const after = await counters();
const applied = await page.evaluate(() => Number(document.getElementById('tanga-scrub').value));

// Scrub pass: jumping to [0, mid, last] must apply frames through the pump
// without adding rebuild churn beyond the playback budget.
const beforeScrub = await counters();
const scrubMax = await page.evaluate(() => Number(document.getElementById('tanga-scrub').max));
const scrubTargets = [0, Math.floor(scrubMax / 2), scrubMax];
for (const target of scrubTargets) {
    await page.evaluate((t) => {
        const scrub = document.getElementById('tanga-scrub');
        scrub.value = String(t);
        scrub.dispatchEvent(new Event('input', { bubbles: true }));
    }, target);
    await page.waitForFunction((t) => {
        const scrub = document.getElementById('tanga-scrub');
        return scrub && scrub.value === String(t);
    }, target, { timeout: 5000 });
}
const afterScrub = await counters();
// Let the CSS2DRenderer attach the refilled axis-label elements before counting
// them (clearGroupChildren detaches the old DOM, addAxis re-adds new elements on
// the next render tick).
await page.waitForTimeout(400);
const labelsAfter = await page.evaluate(() =>
    document.querySelectorAll('div[style*="pointer-events: none"]').length);

const report = { applied, before, after, beforeScrub, afterScrub, labelsBefore, labelsAfter };
console.log(JSON.stringify(report));

const removedDelta = after.removed - before.removed;
const createdDelta = after.created - before.created;
const removedBudget = Math.max(3, Math.round(applied * 0.05));
const createdBudget = Math.max(6, Math.round(applied * 0.1));

const failures = [];
if (removedDelta > removedBudget) {
    failures.push(`removed delta ${removedDelta} exceeds budget ${removedBudget}`);
}
if (createdDelta > createdBudget) {
    failures.push(`created delta ${createdDelta} exceeds budget ${createdBudget}`);
}
const scrubRemovedDelta = afterScrub.removed - beforeScrub.removed;
const scrubCreatedDelta = afterScrub.created - beforeScrub.created;
if (scrubRemovedDelta > removedBudget) {
    failures.push(`scrub removed delta ${scrubRemovedDelta} exceeds budget ${removedBudget}`);
}
if (scrubCreatedDelta > createdBudget) {
    failures.push(`scrub created delta ${scrubCreatedDelta} exceeds budget ${createdBudget}`);
}
if (afterScrub.updated <= beforeScrub.updated) {
    failures.push('scrub pass did not apply any frames');
}
if (labelsAfter !== labelsBefore) {
    failures.push(`label DOM drifted: ${labelsBefore} -> ${labelsAfter}`);
}
if (consoleErrors.length) {
    failures.push(`console errors: ${JSON.stringify(consoleErrors)}`);
}

await browser.close();

if (failures.length) {
    console.error('anim-export-smoke FAILED:', failures.join('; '));
    process.exit(1);
}
console.log('anim-export-smoke ok: unchanged entities are not rebuilt');
