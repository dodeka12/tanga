// Tanga — headless Playwright smoke for the background layer-texture race.
// Run `uv run python js/dev/tests/serve-layer-race-smoke.py` first, then:
//   node js/dev/tests/layer-race-smoke.mjs <base-url>
//
// Optional: SMOKE_ITERS=N overrides the number of full replace cycles (default
// 20; the issue's acceptance suggests 50).  Not run in CI.
import { chromium } from 'playwright';

const base = process.argv[2] || process.env.SMOKE_URL;
if (!base) {
    console.error('usage: node layer-race-smoke.mjs <base-url>');
    process.exit(2);
}

const ITERS = Number(process.env.SMOKE_ITERS || 20);
// Layer index → the opaque colour the server fills that layer with.  The server
// cycles which single layer it enables on each button click (1→2→3→4→5→1…).
const COLORS = {
    1: [255, 0, 0],
    2: [0, 255, 0],
    3: [0, 0, 255],
    4: [255, 255, 0],
    5: [255, 0, 255],
};
const TOLERANCE = 12;

const browser = await chromium.launch({
    headless: true,
    args: ['--enable-unsafe-swiftshader', '--use-angle=swiftshader'],
});

const consoleErrors = [];
const page = await browser.newPage({ viewport: { width: 1200, height: 800 } });
page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
page.on('pageerror', (e) => consoleErrors.push(String(e)));

// Slow the CPU so the zlib decompressions overlap more (wider race window),
// matching the reported "several MB take longer to decode" trigger.
try {
    const cdp = await page.context().newCDPSession(page);
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
} catch {
    // CPU throttling is best-effort; the smoke still runs without it.
}

await page.goto(`${base}/?view=demo`, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('.tanga-three-view canvas', { timeout: 15000 });

const centerPixel = () => page.evaluate(() => {
    const canvas = document.querySelector('.tanga-three-view canvas');
    const c = document.createElement('canvas');
    c.width = canvas.width;
    c.height = canvas.height;
    const ctx = c.getContext('2d');
    ctx.drawImage(canvas, 0, 0);
    const x = Math.floor(c.width / 2);
    const y = Math.floor(c.height / 2);
    const d = ctx.getImageData(x, y, 1, 1).data;
    return [d[0], d[1], d[2]];
});

const close = (r, g, b, expected) =>
    Math.abs(r - expected[0]) <= TOLERANCE
    && Math.abs(g - expected[1]) <= TOLERANCE
    && Math.abs(b - expected[2]) <= TOLERANCE;

async function waitForCenterColor(expected) {
    const deadline = Date.now() + 10000;
    let last = null;
    while (Date.now() < deadline) {
        last = await centerPixel();
        if (close(last[0], last[1], last[2], expected)) return;
        await page.waitForTimeout(50);
    }
    throw new Error(
        `expected centre ${JSON.stringify(expected)}, got ${JSON.stringify(last)}`
    );
}

for (let iter = 1; iter <= ITERS; iter++) {
    for (let layer = 1; layer <= 5; layer++) {
        await page.click('button:has-text("Replace layers")');
        await waitForCenterColor(COLORS[layer]);
    }
    process.stdout.write(`iter ${iter}/${ITERS} ok\n`);
}

await browser.close();

if (consoleErrors.length) {
    console.error('console errors:', consoleErrors);
    process.exit(1);
}
console.log(`layer-race-smoke ok: every layer rendered its colour across ${ITERS} replace cycles`);
