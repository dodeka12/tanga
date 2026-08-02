# Phase 2 — JS Frontend: Control Panel

DOM-based control panel rendered as an overlay in the Three.js viewer. Handles
control rendering, drag-to-move, hide/restore toggle, group expand/collapse,
and WebSocket event dispatch back to Python.

References: [Overview](./README.md) | [Phase 1](./phase1-protocol-and-data-model.md)

---

## 2.1 Architecture

```
viewer.html
    └── <script type="module" src="controls-panel.js">
               │
               ├── handleControlsDefine(msg)    ← called from viewer.js
               ├── renderControlPanel(controls, groups)
               ├── createSlider(ctrl) → <input type="range">
               ├── createDropdown(ctrl) → <select>
               ├── createButton(ctrl) → <button>
               ├── createGroupPanel(group, controls) → <div>
               └── sendControlEvent(type, control_id, value) → ws.send(...)
```

A single new file: `py/pytanga/viz/templates/controls-panel.js`.

## 2.2 Control Panel Container

The control panel is a DOM `<div>` appended to the viewer container
(`#viewer-container` or `document.body`). It is **positioned absolutely**
within the viewport and can be dragged by the user.

### CSS Structure

```css
.tanga-control-panel {
    position: absolute;
    z-index: 20;
    background: rgba(20, 20, 40, 0.92);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 6px;
    padding: 8px 12px;
    min-width: 220px;
    max-width: 320px;
    font-family: sans-serif;
    font-size: 13px;
    color: #ccc;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
    user-select: none;
    transition: opacity 0.2s;
}
.tanga-control-panel.dragging { cursor: grabbing; opacity: 0.95; }
.tanga-control-panel.hidden { display: none; }
```

### Drag Handle

The top bar of each group (or the orphan panel) serves as a drag handle
(`cursor: grab`). On `mousedown`, capture the offset and add `mousemove` /
`mouseup` listeners to update `style.left` / `style.top`. Pointer events on
the handle are consumed to prevent interfering with orbit controls.

### Hide/Restore Toggle

A small floating button is always visible (e.g., `position: fixed;
bottom: 10px; right: 10px;` with a gear or eye icon `⚙`). Clicking it toggles
`display: none` on all control panels. Clicking again restores them. The
button itself remains visible regardless.

## 2.3 Control Rendering

### Slider (`<input type="range">`)

```html
<div class="tanga-control tanga-slider">
    <label>X Position <span class="tanga-value">2.0</span></label>
    <input type="range" min="0" max="5" step="0.1" value="2.0">
</div>
```

- The `<span class="tanga-value">` updates in real-time on `input`.
- WebSocket send is **debounced at ~40ms** to avoid flooding. The `input`
  event updates the DOM display immediately; a debounced handler sends the
  WebSocket message.
- CSS for the range input is themed dark (custom `appearance` with
  `-webkit-slider-runnable-track` etc.).

### Dropdown (`<select>`)

```html
<div class="tanga-control tanga-dropdown">
    <label>Mode</label>
    <select>
        <option value="Wireframe">Wireframe</option>
        <option value="Solid" selected>Solid</option>
        <option value="Translucent">Translucent</option>
    </select>
</div>
```

- `change` event on `<select>` fires an immediate WebSocket send (no
  debouncing needed).

### Button (`<button>`)

```html
<div class="tanga-control tanga-button">
    <button>Reset</button>
</div>
```

- `click` event fires `control:click` immediately.

## 2.4 Group Panel

Each group renders as a collapsible section within the control panel:

```html
<div class="tanga-group" data-group-id="sphere_b_group">
    <div class="tanga-group-header">
        <span class="tanga-group-title">Sphere B</span>
        <button class="tanga-group-toggle">▾</button>
    </div>
    <div class="tanga-group-controls">
        <!-- controls go here -->
    </div>
</div>
```

- Clicking the header toggles `collapsed` by adding/removing a CSS class that
  sets `.tanga-group-controls { display: none; }` and rotates the toggle
  arrow.
- If the group has an `on_toggle` handler registered (tracked via a lookup
  from Phase 4), a `control:group_toggle` message is sent.

## 2.5 Orphan Panel

Controls not belonging to any group are rendered in a default panel with no
title. This panel uses the same drag/hide infrastructure as groups but has no
collapse toggle.

## 2.6 Integration with `viewer.js`

### New Message Handling

In `handleMessage()` in `viewer.js`, add:

```js
if (msg.type === 'controls_define') {
    handleControlsDefine(msg);
} else if (msg.type === 'controls_clear') {
    handleControlsClear();
}
```

### Module Import

In `viewer.html`, add the module import after `viewer.js`:

```html
<script type="module" src="controls-panel.js"></script>
```

Or import as a side-effect module from `viewer.js`:

```js
import './controls-panel.js';
```

The `controls-panel.js` module exports functions that `viewer.js` calls, or
alternatively registers itself on the `window` object so `handleMessage` can
delegate to it.

### API Surface of `controls-panel.js`

```js
// Called from viewer.js handleMessage():
export function handleControlsDefine(msg) { ... }
export function handleControlsClear() { ... }

// Called internally:
function sendControlEvent(type, controlId, value) { ... }
function renderControlPanel(controls, groups) { ... }
function createSlider(ctrl) { ... }
function createDropdown(ctrl) { ... }
function createButton(ctrl) { ... }
function createGroupPanel(group, controls) { ... }
function setupDrag(panelEl, handleEl) { ... }
```

The WebSocket instance (`ws`) is accessed via a module-level variable set by
`viewer.js` after connection, or via a callback:

```js
let _ws = null;
export function setWebSocket(ws) { _ws = ws; }
```

## 2.7 Style Theme

All controls follow the existing dark theme from `viewer.html`:

- Background: `rgba(20, 20, 40, 0.92)` (dark blue-tinted)
- Border: `rgba(255, 255, 255, 0.12)`
- Text: `#ccc` / `#fff` for labels
- Accent: `#4488ff` for sliders, focus outlines
- Button background: `rgba(255, 255, 255, 0.1)`, hover `rgba(255, 255, 255, 0.18)`

CSS is injected via a `<style>` element created by the module to keep styling
self-contained and avoid modifying `viewer.html`.

---

## 2.8 Implementation Checklist

- [ ] 2.1 Create `py/pytanga/viz/templates/controls-panel.js`
- [ ] 2.2 Implement `handleControlsDefine(msg)` — parse controls/groups, destroy old panel, build new DOM
- [ ] 2.3 Implement `handleControlsClear()` — remove all control DOM elements
- [ ] 2.4 Implement `createSlider(ctrl)` — `<input type="range">` with debounced `control:change` send
- [ ] 2.5 Implement `createDropdown(ctrl)` — `<select>` with immediate `control:change` send
- [ ] 2.6 Implement `createButton(ctrl)` — `<button>` with `control:click` send
- [ ] 2.7 Implement `createGroupPanel(group, controls)` — collapsible section with title bar
- [ ] 2.8 Implement orphan panel for controls outside groups
- [ ] 2.9 Implement drag-to-move via drag handle on group/orphan headers
- [ ] 2.10 Implement hide/restore toggle button (always-visible gear/eye icon)
- [ ] 2.11 Inject dark-themed CSS via `<style>` element
- [ ] 2.12 Integrate with `viewer.js` — add message routing, `setWebSocket()` call
- [ ] 2.13 Update `viewer.html` to load the new module
- [ ] 2.14 Manual test: render a slider, dropdown, button in a group; verify drag, hide/restore, expand/collapse
- [ ] 2.15 Manual test: verify WebSocket messages are sent with correct `control_id` and `value`