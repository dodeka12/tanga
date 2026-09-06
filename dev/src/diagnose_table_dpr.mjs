// Sweep deviceScaleFactor (HiDPI / browser-zoom rounding) on a single page via
// CDP, to find where the last column/row of an embedded Tabulator table stops
// being editable.

import { spawn } from 'node:child_process';
import { chromium } from 'playwright';

const example = process.argv[2] || 'py/examples/viz/ui/controls/table_editing.py';

const child = spawn('uv', ['run', 'python', example], { stdio: ['ignore', 'pipe', 'pipe'] });
let url = null;
child.stdout.on('data', (d) => {
  const m = d.toString().match(/https?:\/\/[^\s"'<>]+/);
  if (m && !url) url = m[0];
});
child.stderr.on('data', (d) => process.stderr.write(d));
const t0 = Date.now();
while (!url && Date.now() - t0 < 60000) await new Promise((r) => setTimeout(r, 200));
if (!url) { console.error('No URL found'); child.kill('SIGKILL'); process.exit(1); }

let browser;
try { browser = await chromium.launch({ channel: 'chrome', headless: true }); }
catch { browser = await chromium.launch({ headless: true }); }

const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
const page = await ctx.newPage();
await page.goto(url);
await page.waitForSelector('.tabulator-cell', { timeout: 30000 });

const cdp = await ctx.newCDPSession(page);

async function measure() {
  await page.waitForTimeout(400);
  return page.evaluate(() => {
    const grid = document.querySelector('.tabulator');
    if (!grid) return { ready: false };
    const holder = grid.querySelector('.tabulator-tableholder');
    const cells = [...grid.querySelectorAll('.tabulator-cell')];
    const last = cells[cells.length - 1];
    const r = last.getBoundingClientRect();
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    const hit = document.elementFromPoint(cx, cy);
    return {
      ready: true,
      dpr: window.devicePixelRatio,
      hO: holder.scrollWidth - holder.clientWidth,
      vO: holder.scrollHeight - holder.clientHeight,
      cw: holder.clientWidth, sw: holder.scrollWidth,
      ch: holder.clientHeight, sh: holder.scrollHeight,
      lastW: r.width, lastH: r.height,
      lastRect: { l: r.left, t: r.top, rt: r.right, b: r.bottom },
      holderRect: (() => { const h = holder.getBoundingClientRect(); return { l: h.left, t: h.top, rt: h.right, b: h.bottom }; })(),
      hitLast: last === hit || last.contains(hit),
      hitEl: hit ? (hit.className || hit.tagName) : null,
    };
  });
}

async function dblLast() {
  return page.evaluate(async () => {
    const cells = [...document.querySelectorAll('.tabulator-cell')];
    const last = cells[cells.length - 1];
    const r = last.getBoundingClientRect();
    const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
    if (!hit) return 'HIT-NULL';
    hit.dispatchEvent(new MouseEvent('dblclick', { bubbles: true, cancelable: true, view: window }));
    await new Promise((res) => setTimeout(res, 60));
    const e = document.querySelector('.tabulator-cell.tabulator-editing');
    return e ? 'OPEN' : 'CLOSED';
  });
}

console.log('dpr\thO\tvO\tcw/sw\tch/sh\tlastWxH\tlastRect\tlastHit\tdbl');
for (const dpr of [1, 1.1, 1.2, 1.25, 1.5, 1.75, 2]) {
  await cdp.send('Emulation.setDeviceMetricsOverride', {
    width: 1280, height: 800, deviceScaleFactor: dpr, mobile: false,
  });
  const m = await measure();
  if (!m.ready) { console.log(dpr, 'NOT-READY', JSON.stringify(m)); continue; }
  const d = await dblLast();
  const lr = `${m.lastRect.l.toFixed(1)}..${m.lastRect.rt.toFixed(1)} x ${m.lastRect.t.toFixed(1)}..${m.lastRect.b.toFixed(1)}`;
  console.log(`${dpr}\t${m.hO}\t${m.vO}\t${m.cw}/${m.sw}\t${m.ch}/${m.sh}\t${m.lastW.toFixed(3)}x${m.lastH.toFixed(3)}\t${lr}\t${m.hitLast}\t${d}`);
}

await browser.close();
child.kill('SIGINT');
