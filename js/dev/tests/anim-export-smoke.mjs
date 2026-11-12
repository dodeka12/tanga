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
    window.__smoke = {
        created: 0,
        updated: 0,
        removed: 0,
        pointPathGrew: false,
        pointPathMeshes: new Map(),
    };
    let _tanga;
    Object.defineProperty(window, '__tanga', {
        configurable: true,
        get: () => _tanga,
        set: (v) => {
            const build = v.buildSceneObject;
            v.buildSceneObject = (...a) => {
                window.__smoke.created += 1;
                return build(...a).then((entry) => {
                    if (a[0]?.kind === 'PointPath' && entry?.mesh) {
                        window.__smoke.pointPathMeshes.set(a[0].id, entry.mesh);
                    }
                    return entry;
                });
            };
            const update = v.updateEntityMesh;
            v.updateEntityMesh = (...a) => {
                window.__smoke.updated += 1;
                const [mesh, ent] = a;
                const before = mesh?.geometry?.attributes?.instanceStart?.count ?? 0;
                const result = update(...a);
                if (result && ent?.kind === 'PointPath' && mesh?.geometry) {
                    const after = mesh.geometry.attributes?.instanceStart?.count ?? 0;
                    window.__smoke.pointPathMeshes.set(ent.id, mesh);
                    if (after > before) window.__smoke.pointPathGrew = true;
                }
                return result;
            };
            const remove = v.removeEntityMesh;
            v.removeEntityMesh = (...a) => {
                window.__smoke.removed += 1;
                return remove(...a);
            };
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

const counters = () => page.evaluate(() => ({
    created: window.__smoke.created,
    updated: window.__smoke.updated,
    removed: window.__smoke.removed,
}));
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

// Give the animation loop a render tick so three.js records the final cached
// instance bound, then confirm every PointPath can draw all of its segments.
await page.waitForTimeout(400);
const pointPath = await page.evaluate(() => {
    const state = window.__smoke;
    const samples = [];
    for (const [id, mesh] of state.pointPathMeshes) {
        const count = mesh.geometry?.attributes?.instanceStart?.count ?? 0;
        const max = mesh.geometry?._maxInstanceCount ?? null;
        samples.push({ id, count, max });
    }
    return { grew: state.pointPathGrew, samples };
});

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

const report = { applied, before, after, pointPath, beforeScrub, afterScrub, labelsBefore, labelsAfter };
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
if (!pointPath.grew) {
    failures.push('growing PointPath never received a larger segment list');
}
if (pointPath.samples.length === 0) {
    failures.push('no PointPath meshes were instrumented');
}
for (const sample of pointPath.samples) {
    if (sample.max === null || sample.count > sample.max) {
        failures.push(
            `PointPath ${sample.id}: segment count ${sample.count} exceeds cached draw bound ${sample.max}`,
        );
    }
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
