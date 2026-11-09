// Tanga — headless Playwright smoke for `ValueEditView` focus behaviour (manual).
// Run `uv run python js/dev/tests/serve-value-edit-smoke.py` first, then:
//   node js/dev/tests/value-edit-focus-smoke.mjs <base-url>
//
// The stepper must only take keyboard focus on an explicit click: hovering it
// used to call `input.focus()`, which silently stole arrow-key/space shortcuts
// from the scene.  The scroll wheel keeps stepping the value on hover.
import { chromium } from 'playwright';

const base = process.argv[2] || process.env.SMOKE_URL;
if (!base) {
    console.error('usage: node value-edit-focus-smoke.mjs <base-url>');
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

await page.goto(base, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('.tanga-value-input', { timeout: 15000 });

const focused = () => page.evaluate(() => {
    const input = document.querySelector('.tanga-value-input');
    return input !== null && document.activeElement === input;
});
const value = () => page.inputValue('.tanga-value-input');
const blur = () => page.evaluate(() => {
    if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
});

const startValue = await value();
if (await focused()) throw new Error('the field started out focused');

// Hovering the field or its label must not move the keyboard focus.
await page.hover('.tanga-value-input');
await page.waitForTimeout(200);
if (await focused()) throw new Error('hovering the input focused it');

await page.hover('.tanga-value-edit label');
await page.waitForTimeout(200);
if (await focused()) throw new Error('hovering the label focused it');

// Arrow keys must be inert while the pointer merely hovers over the control.
await page.keyboard.press('ArrowUp');
await page.waitForTimeout(200);
if ((await value()) !== startValue) {
    throw new Error(`ArrowUp stepped the value without focus: ${await value()}`);
}

// Clicking the label focuses the field, after which arrow keys step the value.
await page.click('.tanga-value-edit label');
await page.waitForTimeout(150);
if (!(await focused())) throw new Error('clicking the label did not focus the field');
await page.keyboard.press('ArrowUp');
await page.waitForTimeout(300);
if ((await value()) === startValue) throw new Error('ArrowUp did not step the focused field');

// Clicking into the input focuses it too (native caret placement).
await blur();
await page.click('.tanga-value-input');
if (!(await focused())) throw new Error('clicking the input did not focus it');

// Typed text still commits on Enter.
await page.fill('.tanga-value-input', '2.5');
await page.keyboard.press('Enter');
await page.waitForTimeout(300);
if ((await value()) !== '2.50') {
    throw new Error(`typed value did not commit, got ${JSON.stringify(await value())}`);
}

// The scroll wheel still steps the value while hovering.
await blur();
const box = await page.locator('.tanga-value-edit').boundingBox();
await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
const beforeWheel = await value();
await page.mouse.wheel(0, -120);
await page.waitForTimeout(300);
if ((await value()) === beforeWheel) {
    throw new Error('the scroll wheel no longer steps the value');
}

await browser.close();

if (consoleErrors.length) {
    console.error('console errors:', consoleErrors);
    process.exit(1);
}
console.log('value-edit-focus-smoke ok: focus follows clicks only, wheel still steps');
