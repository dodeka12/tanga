# Phase 3 — `ImageData.version` (uuid) + `update()`

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/viz-architecture.md` — the image
> transport section and the `ImageData` value model).  This is an additive
> value-model change; no architecture change.

## Goal

Give `ImageData` a per-instance `version` (a uuid4 string assigned in
`__post_init__`) and an `update()` method that replaces its content in place and
bumps the version.  This is the identity the server diffs on in Phase 4.

## Files

- Edit: `py/pytanga/viz/image.py`
- Edit: `py/tests/viz/test_image.py`

## Steps

- [x] **3.1 — Add the uuid `version`.**
  - `import uuid` at the top of `image.py`.
  - At the start of `ImageData.__post_init__`, set
    `self.version = uuid.uuid4().hex` (a fresh 32-hex-char uuid4 string per
    instance) so every constructed instance has one regardless of the later
    validation/auto-tile path.
  - `version` is a plain instance attribute, **not** an `__init__` parameter and
    not part of dataclass `__eq__`/`repr`.

- [x] **3.2 — Add `update()` (mutate content + bump version).**
  - Add `def update(self, data=None, *, url=None, codec=None, jpeg_quality=None) -> "ImageData":`
  - Require exactly one of `data`/`url` (raise `ValueError` otherwise), mirroring
    the constructor's mutual exclusivity.
  - `data` given: clear `self.url`/`self.tiled`; reset `width/height/channels/
    dtype` to `None`; assign `self.data`; then re-run `_maybe_auto_tile()` +
    `_validate_array()` (so dims/dtype re-derive and large arrays re-tile).
  - `url` given: clear `self.data`/`self.tiled`; assign `self.url`; keep the
    existing `width/height/channels/dtype` (required for `url`).
  - Apply `codec`/`jpeg_quality` when provided.
  - End with `self.version = uuid.uuid4().hex`; `return self`.

- [x] **3.3 — Tests.**
  - `version` present and unique across two `ImageData("id", data=...)` instances.
  - `update(data=...)` on the same instance: `version` changes and
    `data`/`width`/`height`/`channels`/`dtype` reflect the new array.
  - `update(url=...)` sets the url path (and behaves as the constructor does when
    `width/height/channels/dtype` are absent).
  - `update` with both or neither of `data`/`url` raises `ValueError`.

## Validation

`uv run pytest py/tests/viz/test_image.py -q`

## Notes

- `ImageData` stays a plain (non-frozen) `@dataclass`; `version` is an instance
  attribute set in `__post_init__`, so identity is the uuid compared explicitly.
- `tiled` images are unchanged: their `version` is the existing `ImagePyramid`
  registration counter, not this uuid.
