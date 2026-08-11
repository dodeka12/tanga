# Phase 3 — Frontend `createTextureLabel()` Utility

**Prerequisites:** Phase 1 (TextureLabelStyle on Python side), Phase 2 (entity styles include texture_label)

**Goal:** Add a `createTextureLabel(text, style)` function to `utils.js` that renders
a label (plain text, KaTeX formula, or mixed text+formula) onto an offscreen canvas
and returns a `THREE.CanvasTexture`. Also add helper functions for SVG rendering and
mixed-content layout.

---

## 1. Three Content Modes

| Mode | Detection | Rendering |
|------|-----------|-----------|
| **Math** | `style.math_mode === true` | `katex.renderToString(text)` → SVG → Image → Canvas |
| **Mixed** | `style.math_mode === false` AND text contains `$...$` or `$$...$$` | Split text at delimiters; plain segments via `ctx.fillText()`, math segments via KaTeX SVG composited inline |
| **Plain** | `style.math_mode === false` AND no `$` delimiters | `ctx.fillText(text, cx, cy)` with `style.font_size` + `style.color` |

---

## 2. New Functions in `utils.js`

### 2.1 `hasMathDelimiters(text)` → `boolean`

```js
/**
 * Check whether a string contains $...$ (inline) or $$...$$ (display) delimiters.
 * Used to decide between plain-text and mixed rendering modes.
 *
 * A single unpaired $ is treated as plain text (no mixed mode).
 *
 * @param {string} text
 * @returns {boolean}
 */
export function hasMathDelimiters(text) {
    // Must have at least one pair of $$ or $
    return /\$\$/.test(text) || /\$[^$]+\$/.test(text);
}
```

### 2.2 `svgToImage(svgString)` → `Promise<HTMLImageElement>`

```js
/**
 * Convert an SVG string to an HTMLImageElement via a blob URL.
 *
 * @param {string} svgString - Raw SVG markup (e.g. from katex.renderToString).
 * @returns {Promise<HTMLImageElement>}
 */
function svgToImage(svgString) {
    return new Promise((resolve, reject) => {
        const blob = new Blob([svgString], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const img = new Image();
        img.onload = () => {
            URL.revokeObjectURL(url);
            resolve(img);
        };
        img.onerror = (err) => {
            URL.revokeObjectURL(url);
            reject(err);
        };
        img.src = url;
    });
}
```

### 2.3 `drawSVGToCanvas(ctx, svgString, width, height)` → `Promise<void>`

```js
/**
 * Render a KaTeX SVG string onto a canvas, centered and fit to the
 * available area.
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {string} svgString - SVG from katex.renderToString().
 * @param {number} width - Canvas width.
 * @param {number} height - Canvas height.
 * @returns {Promise<void>}
 */
async function drawSVGToCanvas(ctx, svgString, width, height) {
    const img = await svgToImage(svgString);
    // Fit the image within the canvas while preserving aspect ratio
    const scale = Math.min(width / img.naturalWidth, height / img.naturalHeight) * 0.9;
    const iw = img.naturalWidth * scale;
    const ih = img.naturalHeight * scale;
    const x = (width - iw) / 2;
    const y = (height - ih) / 2;
    ctx.drawImage(img, x, y, iw, ih);
}
```

### 2.4 `drawPlainText(ctx, text, width, height, fontSize, color)` → `void`

```js
/**
 * Render plain text centered on the canvas.
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {string} text
 * @param {number} width
 * @param {number} height
 * @param {number} fontSize
 * @param {string} color
 */
function drawPlainText(ctx, text, width, height, fontSize, color) {
    ctx.fillStyle = color;
    ctx.font = `${fontSize}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, width / 2, height / 2);
}
```

### 2.5 `drawMixedToCanvas(ctx, text, width, height, fontSize, color)` → `Promise<void>`

```js
/**
 * Render text with embedded $...$ (inline) and $$...$$ (display) math.
 *
 * Inline formulas ($...$) are rendered at the current text position on the
 * same line as surrounding text.  Display formulas ($$...$$) occupy their
 * own line, centered.
 *
 * Implementation strategy:
 * 1. Split the text into segments: plain text blocks and formula blocks
 * 2. Measure and layout each segment line-by-line
 * 3. For formula segments, render KaTeX → SVG → drawImage at the
 *    appropriate position
 * 4. For text segments, use ctx.fillText()
 *
 * @param {CanvasRenderingContext2D} ctx
 * @param {string} text
 * @param {number} width
 * @param {number} height
 * @param {number} fontSize
 * @param {string} color
 * @returns {Promise<void>}
 */
async function drawMixedToCanvas(ctx, text, width, height, fontSize, color) {
    // Split text into segments: {type: 'text'|'inline'|'display', content: string}[]
    const segments = parseMathSegments(text);

    const lineHeight = fontSize * 1.5;
    const padding = 20;
    const maxWidth = width - padding * 2;
    let cursorY = padding;

    ctx.fillStyle = color;
    ctx.font = `${fontSize}px sans-serif`;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'alphabetic';

    for (const seg of segments) {
        if (seg.type === 'text') {
            // Word-wrap the plain text
            const words = seg.content.split(' ');
            let line = '';
            for (const word of words) {
                const testLine = line ? line + ' ' + word : word;
                const metrics = ctx.measureText(testLine);
                if (metrics.width > maxWidth && line !== '') {
                    ctx.fillText(line, padding, cursorY + fontSize);
                    cursorY += lineHeight;
                    line = word;
                } else {
                    line = testLine;
                }
            }
            if (line) {
                ctx.fillText(line, padding, cursorY + fontSize);
                // Stay on same line for inline math that follows
            }
        } else if (seg.type === 'inline') {
            // Render KaTeX inline at current cursor position
            const svg = katex.renderToString(seg.content, { throwOnError: false });
            const img = await svgToImage(svg);
            // Scale to match font size
            const scale = (fontSize * 0.8) / img.naturalHeight;
            const iw = img.naturalWidth * scale;
            const ih = img.naturalHeight * scale;
            const x = ctx.measureText(
                // approximate cursor x by measuring text before this segment
                // For simplicity: measure cumulative text width up to this point
                ''
            ).width + padding;
            // Center inline math vertically on the text baseline
            ctx.drawImage(img, padding + (ctx.measureText(' ').width), cursorY + fontSize - ih, iw, ih);
            // Advance cursor (approximate)
            cursorY += 0; // inline doesn't break line
        } else if (seg.type === 'display') {
            // Display formula on its own line, centered
            const svg = katex.renderToString(seg.content, { throwOnError: false, displayMode: true });
            const img = await svgToImage(svg);
            const scale = Math.min(maxWidth / img.naturalWidth, (fontSize * 2.5) / img.naturalHeight) * 0.9;
            const iw = img.naturalWidth * scale;
            const ih = img.naturalHeight * scale;
            const x = (width - iw) / 2;
            cursorY += lineHeight * 0.5; // extra space before display formula
            ctx.drawImage(img, x, cursorY, iw, ih);
            cursorY += ih + lineHeight * 0.5; // extra space after
        }
    }
}

/**
 * Parse a string into an array of text/math segments.
 *
 * @param {string} text
 * @returns {Array<{type: 'text'|'inline'|'display', content: string}>}
 */
function parseMathSegments(text) {
    const segments = [];
    // Split by $$...$$ first (display math), then by $...$ (inline math)
    // Format: text $$display$$ text $inline$ text
    const displayRegex = /\$\$(.+?)\$\$/gs;
    let lastIndex = 0;
    let match;

    // First pass: split by display math
    const parts = [];
    while ((match = displayRegex.exec(text)) !== null) {
        if (match.index > lastIndex) {
            parts.push({ type: 'text', content: text.slice(lastIndex, match.index) });
        }
        parts.push({ type: 'display', content: match[1] });
        lastIndex = match.index + match[0].length;
    }
    if (lastIndex < text.length) {
        parts.push({ type: 'text', content: text.slice(lastIndex) });
    }

    // Second pass: split each text part by inline math ($...$)
    for (const part of parts) {
        if (part.type !== 'text') {
            segments.push(part);
            continue;
        }
        const inlineRegex = /\$(.+?)\$/g;
        let ilast = 0;
        let imatch;
        while ((imatch = inlineRegex.exec(part.content)) !== null) {
            if (imatch.index > ilast) {
                segments.push({ type: 'text', content: part.content.slice(ilast, imatch.index) });
            }
            segments.push({ type: 'inline', content: imatch[1] });
            ilast = imatch.index + imatch[0].length;
        }
        if (ilast < part.content.length) {
            segments.push({ type: 'text', content: part.content.slice(ilast) });
        }
    }

    return segments;
}
```

### 2.6 `createTextureLabel(text, style)` → `THREE.CanvasTexture | null`

```js
/**
 * Create a THREE.CanvasTexture from a label string and texture label style.
 *
 * Supports three modes:
 * - math_mode=true: entire text is a KaTeX formula
 * - math_mode=false + $ delimiters: mixed text with embedded math
 * - math_mode=false + no $: plain text
 *
 * Returns null if text is falsy, katex is unavailable (and math is needed),
 * or rendering fails.
 *
 * @param {string|null|undefined} text - The label content.
 * @param {object} style - TextureLabelStyle dict from the entity's style.
 *        Expected keys: math_mode, repeat_u, repeat_v, offset_u, offset_v,
 *        background, resolution, color, font_size.
 * @returns {THREE.CanvasTexture|null}
 */
export async function createTextureLabel(text, style) {
    if (!text) return null;

    const resolution = style.resolution || 512;
    const width = resolution;
    const height = Math.floor(resolution / 2);
    const bg = style.background;
    const color = style.color || '#000000';
    const fontSize = style.font_size || 48;
    const mathMode = style.math_mode === true;

    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');

    // 1. Background fill
    if (bg && bg !== 'transparent') {
        ctx.fillStyle = bg;
        ctx.fillRect(0, 0, width, height);
    }

    try {
        if (mathMode) {
            // Full math mode
            if (typeof katex === 'undefined') {
                console.warn('createTextureLabel: KaTeX not available, cannot render math formula');
                return null;
            }
            const svg = katex.renderToString(text, { throwOnError: false });
            await drawSVGToCanvas(ctx, svg, width, height);
        } else if (hasMathDelimiters(text)) {
            // Mixed mode
            if (typeof katex === 'undefined') {
                console.warn('createTextureLabel: KaTeX not available, rendering as plain text');
                drawPlainText(ctx, text, width, height, fontSize, color);
            } else {
                await drawMixedToCanvas(ctx, text, width, height, fontSize, color);
            }
        } else {
            // Plain text mode
            drawPlainText(ctx, text, width, height, fontSize, color);
        }
    } catch (err) {
        console.warn('createTextureLabel: rendering failed', err);
        return null;
    }

    // 2. Create texture
    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;

    // 3. Apply wrapping
    const repeatU = style.repeat_u;
    const repeatV = style.repeat_v;
    if ((repeatU && repeatU > 1) || (repeatV && repeatV > 1)) {
        texture.wrapS = THREE.RepeatWrapping;
        texture.wrapT = THREE.RepeatWrapping;
        texture.repeat.set(repeatU || 1, repeatV || 1);
    }

    // 4. Apply offset
    const offsetU = style.offset_u;
    const offsetV = style.offset_v;
    if (offsetU || offsetV) {
        texture.offset.set(offsetU || 0, offsetV || 0);
    }

    return texture;
}
```

**Note:** `createTextureLabel` is `async` because SVG-to-Image conversion is
asynchronous (the `Image.onload` callback). Renderers that call it need to
`await` the result.

---

## 3. Backward Compatibility: Wrapping an `async` Function

Since `createTextureLabel` is `async`, renderers cannot call it in a synchronous
`createSphere(ent)` function and immediately use the result. Two approaches:

### Option A: Make renderers async (recommended)

```js
// sphere.js
export async function createSphere(ent) {
    // ... existing geometry/material setup ...

    const texLabel = ent.style?.texture_label;
    if (texLabel && texLabel.text) {
        const texture = await createTextureLabel(texLabel.text, texLabel);
        if (texture) {
            material.map = texture;
            material.needsUpdate = true;
        }
    }

    tagEntity(mesh, ent);
    return mesh;
}
```

This requires `createEntityMesh()` in `factory.js` to `await` the renderer result:

```js
export async function createEntityMesh(ent) {
    let mesh;
    switch (ent.kind) {
        case 'Sphere':
            mesh = await createSphere(ent);
            break;
        // ...
    }
    if (mesh) tagEntity(mesh, ent);
    return mesh;
}
```

And the caller in `viewer.js` must `await createEntityMesh(ent)`.

### Option B: Fire-and-forget with callback

Synchronous `createSphere` returns the mesh immediately without texture,
then starts an async task that sets the texture when ready:

```js
export function createSphere(ent) {
    // ... create mesh, material ...

    const texLabel = ent.style?.texture_label;
    if (texLabel && texLabel.text) {
        createTextureLabel(texLabel.text, texLabel).then(texture => {
            if (texture) {
                material.map = texture;
                material.needsUpdate = true;
            }
        });
    }

    return mesh;
}
```

**Choose Option A** for Phase 4 — it's cleaner and the viewer's scene loading
already handles async operations (WebSocket messages are processed sequentially,
and the scene is not displayed until loading completes). The `viewer.js`
`upsertObject` function already uses `await` for overlay elements.

---

## 4. No Changes to `viewer.html`

KaTeX is already loaded as a global via `<script>` tags:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
```

The `katex` global is available without any ES module import. `viewer.html`
already handles KaTeX load failures gracefully (shows a warning banner for
optional library failures).

No changes to `viewer.html`.

---

## 5. Implementation Checklist

- [ ] Add `hasMathDelimiters(text)` to `utils.js`
- [ ] Add `svgToImage(svgString)` to `utils.js`
- [ ] Add `drawSVGToCanvas(ctx, svgString, width, height)` to `utils.js`
- [ ] Add `drawPlainText(ctx, text, width, height, fontSize, color)` to `utils.js`
- [ ] Add `parseMathSegments(text)` to `utils.js`
- [ ] Add `drawMixedToCanvas(ctx, text, width, height, fontSize, color)` to `utils.js`
- [ ] Add `createTextureLabel(text, style)` (async) to `utils.js`
- [ ] Export `createTextureLabel` and `hasMathDelimiters` from `utils.js`
- [ ] Update `createEntityMesh()` in `factory.js` to be async and `await` renderers
- [ ] Update all renderers (`point.js`, `line.js`, `sphere.js`, `plane.js`, ...) to be async or handle the async transition (only `sphere.js` and `plane.js` need to actually call `createTextureLabel`)

---

## 6. Verification

- [ ] `hasMathDelimiters("Hello")` → `false`
- [ ] `hasMathDelimiters("$x=1$")` → `true`
- [ ] `hasMathDelimiters("$$E=mc^2$$")` → `true`
- [ ] `hasMathDelimiters("Radius $$r=2$$ cm")` → `true`
- [ ] `createTextureLabel("Hello", {})` returns a `CanvasTexture` with plain text centered
- [ ] `createTextureLabel("E=mc^2", {math_mode: true})` returns a `CanvasTexture` with KaTeX formula (requires `katex` global)
- [ ] `createTextureLabel("Radius $$r=2$$ cm", {math_mode: false})` returns a `CanvasTexture` with mixed content
- [ ] `createTextureLabel(null, {})` → `null`
- [ ] `createTextureLabel("$$x$$", {math_mode: false})` without `katex` global → `console.warn` + returns plain-text texture
- [ ] Texture wrapping/repeat/offset are applied correctly when `repeat_u`/`offset_v` are set
- [ ] No browser console errors during normal operation