# Automatic Version Tagging

This project uses **`hatch-vcs`** for dynamic versions: the package version
is derived from the latest git tag (see `[tool.hatch.version]` in `pyproject.toml`).

To keep tags in sync with conventional commits, we use a **git post-merge hook**
that runs locally after every merge into `main`.

---

## How it works

1. You write [Conventional Commit][1] messages:
   - `feat: add …` → **minor** bump
   - `feat!: change …` or `BREAKING CHANGE` → **major** bump
   - `fix:` / `docs:` / `chore:` … → **patch** bump (default)

2. When you merge a PR (or `git pull`) into `main`, the **`post-merge` hook**
   fires automatically.

3. The hook calls `tools/version-tag.sh --push`, which:
   - reads commit messages since the last tag,
   - determines the highest bump level,
   - computes the next semver (`vMAJOR.MINOR.PATCH`),
   - creates an annotated tag,
   - pushes it to `origin`.

4. `hatch-vcs` picks up the new tag on the next build.

---

## One-time setup (per clone)

```bash
./tools/install-hooks.sh
```

This creates `.git/hooks/post-merge` (a regular file, not tracked by git).
Every collaborator should run this once after cloning.

---

## Manual usage

You can also run the version-tag script directly:

```bash
# Preview what the next tag would be (does not create anything):
./tools/version-tag.sh --dry-run

# Create tag locally only:
./tools/version-tag.sh

# Create tag and immediately push:
./tools/version-tag.sh --push
```

---

## No external dependencies

The whole system is just two small Bash scripts (`tools/version-tag.sh` and
`tools/install-hooks.sh`).  There is **no** need for CI, GitHub Actions, or
any third-party tool.  It works equally well on private and public repos.

[1]: https://www.conventionalcommits.org/