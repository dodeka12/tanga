# Phase 5 — Docs + changelog

> **Architecture note — check the developer docs.** Before implementing, check
> `docs/dev/architecture/viz-architecture.md` and `docs/py/viz/styling/surface.md`
> — both currently state surface materials are opaque.  This phase updates them
> (the behavior change itself landed in Phases 1-4), and adds the changelog per
> `dev/workflows/changelog.md`.

## Goal

Update the user + developer docs to the new opacity semantics and add the branch
changelog.

## Files

- Edit `docs/py/viz/styling/surface.md`
- Edit `docs/dev/architecture/viz-architecture.md`
- New `docs/changelog/2026/10/20_fix-tex.md`

## Steps

- [x] **5.1 — User docs**
  - In `docs/py/viz/styling/surface.md`, replace the "opaque by default; do not
    inherit the shell opacity" bullet with:
    - solid-surface entities default to opacity `1.0`;
    - the standard texture map multiplies the entity opacity by the texture's
      alpha channel;
    - custom shaders receive the entity opacity as `u_opacity`.
  - Update the `u_opacity` mention in the "Custom shaders" section to "the
    entity's opacity".

- [x] **5.2 — Developer docs**
  - In `docs/dev/architecture/viz-architecture.md`, update the "Surface materials
    are **opaque** (they ignore the …)" sentence under "Surface material
    (extension recipe)" to describe the new contract (default `1.0`, opacity ×
    texture alpha, `u_opacity` = entity opacity).

- [x] **5.3 — Branch changelog**
  - Run `uv run python tools/last-release.py` and use the printed since-version
    for the title, then create `docs/changelog/2026/10/20_fix-tex.md`.
  - Use `## Bug Fixes` (and note the default-opacity change) with self-contained
    bullets: solid-surface default opacity → `1.0`; standard texture alpha =
    `u_opacity × texel.a`; shaders receive entity opacity as `u_opacity`.
  - The `docs/changelog/index.md` entry and the hash rename happen at PR time
    (`dev/workflows/pull-request.md`), not here.

## Validation

```bash
uv run mkdocs build --strict
uv run ruff check .
uv run ty check
```

## Notes

- Do not hand-edit `docs/changelog/index.md` yet — that is part of the PR
  workflow (squash → hash rename → index entry).
- Manual smoke (optional): `uv run python py/examples/viz/surface/texture_mapping.py`.
