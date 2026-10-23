# Background-image reconnect + texture reuse — Overview

**Created:** 2026-10-08 | **Status:** Done | **Branch:** `fix/background-image`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md` — the
> "Layout re-push", "One `_viewRegistry`", "Granular updates", and "Image
> background" sections) for the subsystem(s) this work touches, so the new code
> aligns with the documented architecture.  If this work introduces or changes
> architecture, update the developer docs.

## Goal

Fix the reconnect black-pane bug (`_input/pytanga-background-image-reconnect-bug.md`)
and make the per-pane background quad a consistent **scene-content** citizen:

- On `clear_all` (reconnect) it is disposed and rebuilt from the re-sent frame,
  exactly like entity meshes — instead of leaving a stale, disposed quad.
- On a granular / layout-only update it **keeps its previous texture** when the
  frame is unchanged, instead of re-decoding (or blanking when no frame arrives).
- On `set_layout` the server only re-sends background frames that actually
  changed, so a layout-only re-push (e.g. "Swap panes") stops paying the
  transfer + client decode cost for an unchanged image.

## Background / root cause

`ThreeJsView` reuses the pane shell (WebGL context/camera/controls) across both
layout re-pushes and reconnects (`_viewRegistry` reconciliation).  Its scene
*content* (entity meshes) is the opposite: `clearAll()` disposes every scene
child and `scene_update` rebuilds them from authoritative state.  The background
quad is scene content, but it is an exception to that rule — it lives in a
private `this._backgroundMesh` field, is not in `sceneObjects`, and `clearAll()`
never clears that field.  Consequences:

1. **Reconnect black pane** — `clear_all` disposes the quad but leaves
   `_backgroundMesh`/`_backgroundImage` set; the reused pane's
   `setBackgroundImage()` then calls `updateImageBackground()` on the detached,
   disposed mesh, so nothing re-renders.
2. **No-frame blank** — `image-background.js::_backgroundTexture()` falls back to
   `makeEncodedTexture(img, null)`, which returns a *blank* DataTexture rather
   than "keep the previous texture".  This is masked today only because
   `set_layout` re-sends the frame every time; once the server-side diffing (Phase 4) stops that, the
   reuse path would blank the background.

## Architecture (short)

- **Client, `py/pytanga/viz/templates/views/three-view.js`** — `clearAll()`
  resets `_backgroundMesh`/`_backgroundImage`; `setBackgroundImage()` only reuses
  a mesh still attached to `this.scene`.
- **Client, `py/pytanga/viz/templates/renderers/image-background.js`** —
  `_backgroundTexture()` returns `null` (not a blank texture) when no pixel frame
  is pending for a `source:"data"` image; `createImageBackground()` registers a
  one-shot `registerImageFrameConsumer` fallback (mirroring
  `renderers/image.js`), while `updateImageBackground()`'s existing `if (tex)`
  guard then keeps the previous texture.
- **Model, `py/pytanga/viz/image.py`** — `ImageData` gains a per-instance
  `version` (a fresh `uuid.uuid4().hex` in `__post_init__`) and an `update()`
  method that replaces the content in place and bumps `version`.
- **Server, `py/pytanga/viz/_layout.py` + `py/pytanga/viz/views/_helpers.py`** —
  `_image_meta` emits `"version"` for `data`/`url`; `set_layout()` diffs each
  background by `image.version` against a cached `_background_versions[id]` and
  only re-encodes/re-sends when the version changed (pruning stale ids).

## Decisions (confirmed)

- The background quad is **scene content**, not a view leaf: dispose + rebuild on
  `clear_all`, keep-previous on unchanged updates.  We do **not** retain it across
  a hard reconnect (entities are rebuilt too, the server re-sends the frame
  regardless, and retaining risks staleness).
- **A per-instance uuid is the image `version`.**  `ImageData.__post_init__`
  assigns `version = uuid.uuid4().hex`; `update()` bumps it.  `_image_meta`
  serialises `version` for `data`/`url` (tiled already carries its own counter).
  Change is detected by uuid identity, so the caller must **reuse the instance**
  (or not call `update()`) for an unchanged image — recreating the instance
  yields a new uuid and re-sends (same as today's always-re-send, never worse).
- Reusing the quad *mesh* alone is not a goal (a 2×2 plane + shader is cheap);
  the resource worth avoiding is the texture decode/upload, which the keep-previous
  path (Phase 2) and server-side diffing (Phase 4) address.

## Contract (fixed)

```js
// three-view.js — clearAll() gains two resets (after sceneObjects.clear()):
this._backgroundMesh = null;
this._backgroundImage = null;

// three-view.js — setBackgroundImage() reuse branch becomes:
if (this._backgroundMesh && this._backgroundMesh.parent === this.scene) {
    updateImageBackground(this._backgroundMesh, this._backgroundImage);
} else {
    this._backgroundMesh = createImageBackground(this._backgroundImage);
    this.scene.add(this._backgroundMesh);
}

// image-background.js — _backgroundTexture() data branch:
const frame = hasImageFrame(img.id) ? takeImageFrame(img.id) : null;
if (!frame) return Promise.resolve(null);   // caller keeps previous / fills in later
return makeEncodedTexture(img, frame);
```

```python
# image.py — ImageData identity + in-place update
# __post_init__:
self.version = uuid.uuid4().hex          # fresh per-instance identity

def update(self, data=None, *, url=None, codec=None, jpeg_quality=None):
    # exactly one of data/url; re-validate/re-tile; then:
    self.version = uuid.uuid4().hex      # bump on every content change
    return self

# views/_helpers.py — _image_meta() data/url branch gains:
"version": image.version

# _layout.py — set_layout() diffs by version (skip encode+send when unchanged):
if self._background_versions.get(image.id) != image.version:
    self._transport.send_bytes(encode_image_frame(...))
    self._background_frames[image.id] = frame
    self._background_versions[image.id] = image.version
# prune ids no longer present (both _background_frames and _background_versions)
```

## Phases

| Phase | File | Summary |
|-------|------|---------|
| 1 | [01-reconnect-clearall-reset.md](./01-reconnect-clearall-reset.md) | Reset background state on `clearAll` + guard `setBackgroundImage` (the reported bug) |
| 2 | [02-keep-previous-and-consumer.md](./02-keep-previous-and-consumer.md) | `_backgroundTexture` keep-previous + `registerImageFrameConsumer` fallback |
| 3 | [03-imagedata-uuid-version.md](./03-imagedata-uuid-version.md) | `ImageData.version` (uuid) + `update()` method |
| 4 | [04-server-version-diffing.md](./04-server-version-diffing.md) | `_image_meta` `version` + `set_layout` uuid-diffing |
| 5 | [05-docs-changelog.md](./05-docs-changelog.md) | Developer-doc clarification + branch changelog |

## Testing as you go

- `node js/dev/tests/check-syntax.mjs` (frontend syntax gate, every client phase)
- `node --test 'js/dev/tests/*.test.mjs'` (JS unit tests — unaffected but run to be safe)
- `uv run pytest py/tests/viz/test_image.py -q` (phase 3)
- `uv run pytest py/tests/viz/test_image_background.py -q` (phase 4)
- `uv run mkdocs build --strict` (phase 5)
- Manual browser smoke (frontend behaviour): `uv run python js/dev/tests/serve-smoke.py`
  then `node js/dev/tests/reconcile-smoke.mjs` (see `js/dev/README.md`)

## Non-goals

- No retention of the background quad (or its texture) across a hard reconnect —
  reconnect rebuilds it from authoritative state, like entities.
- No change to the binary frame wire format or `view_layout` shape (`_image_meta`
  gains only the additive `version` field for `data`/`url`).
- No content hashing — the version is a per-instance uuid, so callers reuse the
  instance (or use `update()`) to avoid a re-send on an unchanged image.
- Not fixing the separate `_input/pytanga-background-image-blank-pane.md`
  initial-load race end-to-end — Phase 2's consumer fallback removes the same
  asymmetry for the background, but the blank-pane report is tracked on its own.
- No change to entity-image (`renderers/image.js`) or tiled/URL/stream paths.
