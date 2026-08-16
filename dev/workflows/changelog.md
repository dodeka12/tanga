# Workflow: Changelog

How to create and maintain changelog entries for this repository.

## Location & naming

- New changelogs live in `docs/changelog/`.
- Filename: `YYYY-MM-DD_<short-commit-hash>.md`, e.g. `2026-08-16_7cb2db1.md`.
  The hash is the commit that introduces the file (use the full commit's short hash).

## Title

- Do **not** predict the next release version number — it is assigned later by
  the GitHub deploy workflow (semantic versioning). Hard-coding a version here
  is fragile.
- Use the current-tag-relative form:

  ```
  # Changes since version <last-public-release>
  ```

  e.g. `# Changes since version 0.9.2`.

## Structure

Use these sections in this order (only include the sections that apply):

```
# Changes since version <last-public-release>

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
When adding a new changelog:

1. Add a new entry at the top, directly below `# Changelog`.
2. Head the entry with the same since-relative label as the title:

   ```
   ## [Since 0.9.2] — 2026-08-16
   ```

   (use `## [Since <version>] — <YYYY-MM-DD>`; do **not** use an `[Unreleased]`
   tag, since the version is not yet known).
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