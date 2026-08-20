# Workflow: Changelog

How to create and maintain changelog entries for this repository.

## Location & naming

- New changelogs live in `docs/changelog/`.
- **On a feature/fix branch (any branch other than `main`)** name the file
  `YYYY-MM-DD_<branch-name>.md`, e.g. `2026-08-19_fix-join-meet.md`.
  - Replace `/` in the branch name with `-` (branch names commonly contain
    `/`, which would be read as a path separator in a filename).
  - Integrate **all** changes made on the branch into this single branch
    changelog — append to it as the branch evolves; do **not** create a new
    file per commit.
- **When opening a PR**, the file is renamed to its final
  `YYYY-MM-DD_<short-commit-hash>.md` form (the hash of the branch's last
  commit). See `dev/workflows/pull-request.md`.

## Title

- Do **not** predict the next release version number — it is assigned later by
  the GitHub deploy workflow (semantic versioning). Hard-coding a version here
  is fragile.
- Use the current-tag-relative form:

  ```
  # Changes since version <last-stable-release>
  ```

  Determine `<last-stable-release>` by running (prints the newest non-prerelease
  tag reachable from the commit the branch is based on, without the leading
  `v`):

  ```
  uv run python tools/last-release.py
  ```

  e.g. if it prints `0.10.0`, use `# Changes since version 0.10.0`.
  Do **not** copy a version from this document or from another changelog — it
  must reflect the tag your branch actually forked from, and it changes
  frequently.

## Structure

Use these sections in this order (only include the sections that apply):

```
# Changes since version <last-stable-release>

## New Features
- **<Headline>** — one-sentence explanation.

## Breaking Changes
- **<Headline>** — one-sentence explanation.

## Bug Fixes
- **<Headline>** — one-sentence explanation.

## Refactor
- **<Headline>** — one-sentence explanation.
```

Bullet style: `- **Headline** —` followed by a concise sentence. Wrap body text
at ~80 columns. Keep each bullet self-contained (no context from other bullets).

## Index update (`docs/changelog/index.md`)

`docs/changelog/index.md` keeps a top-level, newest-first list of releases.
The entry is added when the changelog is finalized at PR time (after the rename
to the hash-based filename). When adding a changelog:

1. Add a new entry at the top, directly below `# Changelog`.
2. Head the entry with the same since-relative label as the title:

   ```
   ## [Since <version>] — <YYYY-MM-DD>
   ```

   where `<version>` is the same value printed by `tools/last-release.py`
   (e.g. `## [Since 0.10.0] — 2026-08-18`). Do **not** use an `[Unreleased]`
   tag, since the version is not yet known.
3. Add a one-line summary of the main features (dot-separated, `·`), a second
   line for breaking/bug highlights if needed, and a details link:

   ```
   - OPNS/IPNS flag on `Algebra.opns` · typed analyzers · ...
   - Breaking: per-call `opns` removed · ...
   → [Details](2026-08-16_7cb2db1.md)
   ```

4. Leave existing (older) entries untouched.

## Release flow (for later)

- When the deploy workflow actually cuts a version/tag, the "since <version>"
  labels may optionally be retrofitted to the concrete released version number,
  but this is a separate step and not done when authoring the changelog.