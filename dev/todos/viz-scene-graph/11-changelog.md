# Phase 11 — Changelog

**Status:** Planned

## Goal

Add a changelog entry for the scene-graph work following
`dev/workflows/changelog.md`.

## Files

- New: `docs/changelog/YYYY-MM-DD_<short-hash>.md` (date + short hash of the
  introducing commit)
- Modify: `docs/changelog/index.md`

## Steps

### Determine the "since" label

- [ ] Check the current latest public release version; use the form
      `# Changes since version <last-public-release>` in the title and the
      `## [Since <version>] — <date>` heading in the index.

### Create the changelog file

- [ ] Create `docs/changelog/YYYY-MM-DD_<short-hash>.md`.
- [ ] Use only the sections that apply, in the required order
      (`New Features`, `Breaking Changes`, `Bug Fixes`, `Refactor`).
- [ ] Add entries covering at least:
  - [ ] **New Features** — `VizGroup` container nodes and scene-graph parenting.
  - [ ] **New Features** — `VizObjectRef` (entity/style/color/opacity/
        texture-label/label access, transform mutators, group `add`/`new`).
  - [ ] **New Features** — per-object transforms
        (`translate`/`rotate`/`scale_by`/`set_transform`/`transform`) and
        aspect-scoped updates (`full`/`style`/`transform`) for fast,
        in-place group animation.
  - [ ] **New Features** — overlay objects (`VizOverlayObject`) and
        `attach_to` for labels that live-follow scene nodes.
  - [ ] **New Features** — `_transforms.py` operator/entity → matrix/TRS
        conversion helpers.
  - [ ] **Breaking Changes** (if any) — e.g. any removed serializer
        entry points or `SceneObject` changes surfaced to users.
  - [ ] **Refactor** — object-node hierarchy (`VizSceneObject` /
        `VizOverlayObject` / `VizGroup`) replacing the flat `SceneObject`
        registry, with serialization moving into node `serialize()` and
        updates emitted as aspect patches.
- [ ] Wrap body text at ~80 columns; use `- **Headline** — …` bullet style.

### Update the index

- [ ] Add a new entry at the top of `docs/changelog/index.md`, directly below
      `# Changelog`.
- [ ] Head it `## [Since <version>] — <YYYY-MM-DD>`.
- [ ] Add a dot-separated summary line (main features `·` optional
      breaking/bug highlights) and a `→ [Details](...md)` link.
- [ ] Leave older entries untouched.

## Verification

- [ ] Filename matches `YYYY-MM-DD_<short-hash>.md` per the workflow.
- [ ] Title uses the `# Changes since version <last-public-release>` form.
- [ ] Section order matches the workflow.
- [ ] Index entry is newest-first and links to the new file.
- [ ] No hard-coded future version number is introduced.