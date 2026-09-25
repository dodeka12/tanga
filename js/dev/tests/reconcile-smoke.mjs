// Tanga — headless Playwright smoke for layout reconciliation (manual, not CI).
// Run `uv run python js/dev/tests/serve-smoke.py` first, then:
//   node js/dev/tests/reconcile-smoke.mjs <base-url>
import { chromium } from 'playwright';

const base = process.argv[2] || process.env.SMOKE_URL;
if (!base) {
    console.error('usage: node reconcile-smoke.mjs <base-url>');
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

await page.goto(`${base}/?view=demo`, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('.tanga-split', { timeout: 15000 });
await page.waitForSelector('.tanga-three-view', { timeout: 15000 });

// Tag the two scene-pane canvases so we can detect reuse vs. recreate.
await page.evaluate(() => {
    [...document.querySelectorAll('.tanga-three-view canvas')]
        .forEach((c, i) => { c.dataset.smokeId = `canvas-${i}`; });
});

const order = () => page.evaluate(() =>
    [...document.querySelectorAll('.tanga-three-view canvas')]
        .map((c) => c.dataset.smokeId || null));

const before = await order();
if (before.length !== 2 || before.some((x) => x == null)) {
    throw new Error(`expected 2 tagged panes, got ${JSON.stringify(before)}`);
}

// Swap panes → the same canvases must survive (reordered, not recreated).
await page.click('button:has-text("Swap panes")');
await page.waitForTimeout(500);
const afterSwap = await order();
if (JSON.stringify([...afterSwap].sort()) !== JSON.stringify([...before].sort())) {
    throw new Error(`panes were recreated on swap: ${JSON.stringify(before)} -> ${JSON.stringify(afterSwap)}`);
}
if (JSON.stringify(afterSwap) === JSON.stringify(before)) {
    throw new Error('panes did not reorder on swap');
}

// New noise → background updates in place; the canvases are untouched.
await page.click('button:has-text("New noise")');
await page.waitForTimeout(500);
const afterNoise = await order();
if (JSON.stringify(afterNoise) !== JSON.stringify(afterSwap)) {
    throw new Error(`panes changed on background-image swap: ${JSON.stringify(afterNoise)}`);
}

await browser.close();

if (consoleErrors.length) {
    console.error('console errors:', consoleErrors);
    process.exit(1);
}
console.log('reconcile-smoke ok: panes reused on swap, background swap left canvases intact');
