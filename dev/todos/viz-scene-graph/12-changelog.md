# Phase 12 — Changelog

**Status:** Done

## Goal

Add a changelog entry for the scene-graph work following
`dev/workflows/changelog.md`.

## Files

- New: `docs/changelog/YYYY-MM-DD_<short-hash>.md` (date + short hash of the
  introducing commit)
- Modify: `docs/changelog/index.md`

## Steps

### Determine the "since" label

- [x] Check the current latest public release version; use the form
      `# Changes since version <last-public-release>` in the title and the
      `## [Since <version>] — <date>` heading in the index.

### Create the changelog file

- [x] Create `docs/changelog/YYYY-MM-DD_<short-hash>.md`.
- [x] Use only the sections that apply, in the required order
      (`New Features`, `Breaking Changes`, `Bug Fixes`, `Refactor`).
- [x] Add entries covering at least:
  - [x] **New Features** — `VizGroup` container nodes and scene-graph parenting.
  - [x] **New Features** — `VizObjectRef` (entity/style/color/opacity/
        texture-label/label access, transform mutators, group `add`/`new`).
  - [x] **New Features** — per-object transforms
        (`translate`/`rotate`/`scale_by`/`set_transform`/`transform`) and
        aspect-scoped updates (`full`/`style`/`transform`) for fast,
        in-place group animation.
  - [x] **New Features** — overlay objects (`VizOverlayObject`) and
        `attach_to` for labels that live-follow scene nodes.
  - [x] **New Features** — `_transforms.py` operator/entity → matrix/TRS
        conversion helpers.
  - [x] **Breaking Changes** (if any) — e.g. any removed serializer
        entry points or `SceneObject` changes surfaced to users.
  - [x] **Refactor** — object-node hierarchy (`VizSceneObject` /
        `VizOverlayObject` / `VizGroup`) replacing the flat `SceneObject`
        registry, with serialization moving into node `serialize()` and
        updates emitted as aspect patches.
  - [x] **Refactor** — default styles moved into a per-scene
        `VizStyleDefaults` holder (snapshotted at scene creation).
- [x] Wrap body text at ~80 columns; use `- **Headline** — …` bullet style.

### Update the index

- [x] Add a new entry at the top of `docs/changelog/index.md`, directly below
      `# Changelog`.
- [x] Head it `## [Since <version>] — <YYYY-MM-DD>`.
- [x] Add a dot-separated summary line (main features `·` optional
      breaking/bug highlights) and a `→ [Details](...md)` link.
- [x] Leave older entries untouched.

## Verification

- [x] Filename matches `YYYY-MM-DD_<short-hash>.md` per the workflow.
- [x] Title uses the `# Changes since version <last-public-release>` form.
- [x] Section order matches the workflow.
- [x] Index entry is newest-first and links to the new file.
- [x] No hard-coded future version number is introduced.