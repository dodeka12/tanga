# Phase 4 — Tests, docs, changelog

## Goal

Lock in correctness (C++ path ≡ numpy path), document the fast path, and record
the change.

## Files

- Edit: `py/tests/viz/test_image_io.py`
- Edit: `docs/dev/workflows/precompiled-wheels.md`
- Edit: `docs/dev/architecture/viz-architecture.md`
- Edit: `docs/py/viz/image/hdr-images.md`
- Edit: `docs/changelog/2026/09/25_fix-image-display.md`

## Steps

- [x] **4.1 — Tests**
  - Add a round-trip test that runs the C++ `binding_piz.piz_decode` (when
    importable, else `pytest.skip`) and the numpy fallback on the committed
    `piz_rgb.exr` / raw-fallback fixtures and asserts **identical** bytes.
  - Add a fallback test that monkeypatches the loader to raise and asserts
    `read_exr` still decodes via numpy; and that
    `PYTANGA_FORCE_PURE_PYTHON=1` takes the numpy path.

- [x] **4.2 — Developer docs**
  - `docs/dev/workflows/precompiled-wheels.md`: add `binding_piz` to the
    precompiled-set list + manifest format (a `"piz"` key).
  - `docs/dev/architecture/viz-architecture.md`: note the `_image_io.py` PIZ
    fast path (C++ `binding_piz` → numpy fallback) in the file-map row.
  - `docs/py/viz/image/hdr-images.md`: one line that large PIZ EXRs use the
    compiled `binding_piz` when available, falling back to numpy.

- [x] **4.3 — Changelog**
  - Per `dev/workflows/changelog.md`, add a `## New Features` (or `## Bug
    Fixes`) bullet: PIZ decode now vectorized (numpy) and accelerated via a
    compiled `binding_piz` extension with a pure-Python fallback; large EXRs
    load in seconds.  Regenerate example docs if any example docstring changed
    (`uv run python tools/generate-example-docs.py --check`).

## Notes

- `tools/generate-example-docs.py --check` reports pre-existing drift in
  `viz/image/load_image_from_disk.md` (from an earlier commit on this branch,
  unrelated to PIZ); no example docstring changed here, so it was not
  regenerated.
- `pytest` (27 tests, both C++ and `PYTANGA_FORCE_PURE_PYTHON=1` paths),
  `ruff check py/`, `ty check`, and `mkdocs build --strict` all pass.

## Validation

```
uv run pytest py/tests/viz/test_image_io.py -q
uv run ruff check py/ && uv run ty check
uv run python tools/generate-example-docs.py --check
uv run mkdocs build --strict
```

## Notes

- Keep the changelog title `# Changes since version 2.11.0` (rename to the hash
  form only at PR time, per `dev/workflows/changelog.md`).
- No change to the public `read_exr`/`read_hdr` API or return shape — only
  performance and the optional compiled fast path.

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/` (especially `docs/dev/architecture/`) for the subsystem(s) this
> work touches, so the new code aligns with the documented architecture.  If
> this work introduces or changes architecture, update the developer docs.
