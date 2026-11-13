// Tanga — headless Playwright smoke for view visibility (`visible: false`).
// Run `uv run python js/dev/tests/serve-visibility-smoke.py` first, then:
//   node js/dev/tests/visibility-smoke.mjs <base-url>
//
// Asserts that visibility is a *view* property:
//   * a group serialized with `visible: false` starts hidden and takes no
//     layout space, while a visible probe group still does;
//   * a Parameters row whose control is hidden hides its title too;
//   * `control_state {visible}` shows/hides a group and a row at runtime,
//     shrinking/growing the surrounding layout;
//   * a hidden group survives a layout re-push, and shows again afterwards
//     (the inline `display:flex` shell is restored).
import { chromium } from 'playwright';

const base = process.argv[2] || process.env.SMOKE_URL;
if (!base) {
    console.error('usage: node visibility-smoke.mjs <base-url>');
    process.exit(2);
}

const browser = await chromium.launch({
    headless: true,
    args: ['--enable-unsafe-swiftshader', '--use-angle=swiftshader'],
});

const consoleErrors = [];
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
page.on('pageerror', (e) => consoleErrors.push(String(e)));

await page.goto(`${base}/?view=demo`, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('.tanga-toolbar', { timeout: 15000 });
await page.waitForTimeout(400);

const groupState = (title) => page.evaluate((wanted) => {
    const label = [...document.querySelectorAll('.tanga-group-title')]
        .find((el) => el.textContent === wanted);
    const group = label ? label.closest('.tanga-group') : null;
    if (!group) return null;
    return {
        display: getComputedStyle(group).display,
        height: Math.round(group.getBoundingClientRect().height),
    };
}, title);

const rowState = (title) => page.evaluate((wanted) => {
    const key = [...document.querySelectorAll('.tanga-params-key')]
        .find((el) => el.textContent === wanted);
    if (!key) return null;
    const row = key.closest('.tanga-params-row');
    return {
        display: row ? getComputedStyle(row).display : 'missing',
        height: row ? Math.round(row.getBoundingClientRect().height) : 0,
    };
}, title);

const paramsHeight = () => page.evaluate(() => {
    const view = document.querySelector('.tanga-params-view');
    if (!view) return null;
    // The pane itself is sized by the enclosing split; what shrinks is the
    // rendered content, so measure the rows' bounding box instead.
    const rows = [...view.querySelectorAll('.tanga-params-row')];
    return rows.reduce((sum, row) => sum + row.getBoundingClientRect().height, 0);
});

const expect = (condition, message) => {
    if (!condition) throw new Error(message);
};


// ── initial state ───────────────────────────────────────────
const hiddenInitial = await groupState('Hidden group');
expect(hiddenInitial, 'expected the "Hidden group" group to exist');
expect(hiddenInitial.display === 'none', `expected the hidden group to be display:none, got ${hiddenInitial.display}`);
expect(hiddenInitial.height === 0, `expected the hidden group to take no space, got ${hiddenInitial.height}px`);

const probeInitial = await groupState('Probe group');
expect(probeInitial, 'expected the "Probe group" group to exist');
expect(probeInitial.display === 'flex', `expected the probe group to use display:flex, got ${probeInitial.display}`);
expect(probeInitial.height > 0, `expected the probe group to take space, got ${probeInitial.height}px`);

const alphaInitial = await rowState('Alpha');
expect(alphaInitial, 'expected the hidden "Alpha" row to keep its key label element');
expect(alphaInitial.display === 'none', `expected the hidden Alpha row to be display:none, got ${alphaInitial.display}`);
const betaInitial = await rowState('Beta');
expect(betaInitial && betaInitial.display !== 'none', 'expected the Beta row to be visible');

// ── show the group ──────────────────────────────────────────
await page.click('button:has-text("Show group")');
await page.waitForTimeout(400);
const hiddenShown = await groupState('Hidden group');
expect(hiddenShown.display === 'flex', `expected the shown group to restore display:flex, got ${hiddenShown.display}`);
expect(hiddenShown.height > 0, `expected the shown group to take space, got ${hiddenShown.height}px`);

// ── hide / show a Parameters row ────────────────────────────
const beforeHide = await paramsHeight();
await page.click('button:has-text("Hide row")');
await page.waitForTimeout(400);
const betaHidden = await rowState('Beta');
expect(betaHidden.display === 'none', `expected the hidden Beta row to be display:none, got ${betaHidden.display}`);
const afterHide = await paramsHeight();
expect(afterHide < beforeHide, `expected the params view to shrink (${beforeHide} -> ${afterHide})`);

await page.click('button:has-text("Show row")');
await page.waitForTimeout(400);
const alphaShown = await rowState('Alpha');
expect(alphaShown.display !== 'none', `expected the shown Alpha row to be visible, got ${alphaShown.display}`);


// ── hide the group, re-push, then show it again ─────────────
await page.click('button:has-text("Hide group")');
await page.waitForTimeout(300);
await page.click('button:has-text("Re-push")');
await page.waitForTimeout(600);
const hiddenAfterRepush = await groupState('Hidden group');
expect(hiddenAfterRepush, 'expected the hidden group to exist after the re-push');
expect(hiddenAfterRepush.display === 'none', `expected the group to stay hidden across a re-push, got ${hiddenAfterRepush.display}`);
const probeAfterRepush = await groupState('Probe group');
expect(probeAfterRepush.display === 'flex', `expected the probe group to keep display:flex after the re-push, got ${probeAfterRepush.display}`);

await page.click('button:has-text("Show group")');
await page.waitForTimeout(400);
const shownAfterRepush = await groupState('Hidden group');
expect(shownAfterRepush.display === 'flex', `expected the group to show again after a re-push, got ${shownAfterRepush.display}`);
expect(shownAfterRepush.height > 0, `expected the shown group to take space after a re-push, got ${shownAfterRepush.height}px`);

await browser.close();

if (consoleErrors.length) {
    console.error('console errors:', consoleErrors);
    process.exit(1);
}
console.log(
    'visibility-smoke ok: hidden group takes no space, params rows hide with their control, '
    + 'runtime toggles work, and visibility survives a layout re-push'
);
