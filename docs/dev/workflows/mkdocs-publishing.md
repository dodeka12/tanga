# MkDocs Publishing with Mike

TanGA uses [mike](https://github.com/jimporter/mike) to manage versioned
documentation on the `gh-pages` branch. Mike builds the site with MkDocs and
organises each version into its own subdirectory, enabling:

- Clean versioned URLs: `https://dodeka12.github.io/tanga/v0.2.3-rc1/`
- A version selector dropdown in the page header
- Aliases like `latest` that point to the current stable release
- Branch-based preview deploys for testing before merging

## What Mike Does

| Command | Result |
|---|---|
| `mike deploy v0.2.3` | Builds docs and pushes them to `gh-pages` under `v0.2.3/` |
| `mike deploy --update-aliases v0.2.3 latest` | Builds **and** moves the `latest` alias to this version |
| `mike set-default --push latest` | Makes `latest` the default (root URL redirects to it) |
| `mike list` | Lists all published versions and their aliases |
| `mike delete dev-old-branch --push` | Removes a preview version from `gh-pages` |

Mike stores metadata in `versions.json` on the `gh-pages` branch. Each
deployed version lives in its own directory — they never overwrite each other.

## Local Preview

Start a live-reload development server (unchanged from standard MkDocs):

```bash
uv sync --group dev
mkdocs serve
```

Open http://localhost:8000. Press `Ctrl+C` to stop.

## Local Deploy with Mike

To publish docs from your local machine to `gh-pages`:

```bash
# Ensure dev deps are installed
uv sync --group dev

# Deploy a test version (your current branch)
export ALIAS="dev-$(git branch --show-current | tr '/' '-')"
mike deploy --push --alias "$ALIAS" "$ALIAS"
```

To publish an official version tag:

```bash
# Deploy a tagged version (e.g. v0.2.3-rc1)
mike deploy --push v0.2.3-rc1
```

To promote a version to `latest`:

```bash
mike deploy --push --update-aliases v0.2.3 latest
```

## Managing Versions

```bash
# List all published versions
mike list

# Set the default version (which the root URL redirects to)
mike set-default --push latest

# Delete an old preview version
mike delete dev-old-feature --push

# Rebuild an existing version locally (for testing)
mike serve          # serves the currently-checked-out version via mike
mike serve -a       # serves all versions
```

## CI/CD Automation

Docs are also deployed automatically via GitHub Actions:

| Workflow | Trigger | What it does |
|---|---|---|
| `cd.yml` → `docs-deploy` | Push to `main` | Builds and deploys docs for the RC tag (e.g. `v0.2.3-rc1`) |
| `promote.yml` → `docs-stable` | Manual (`workflow_dispatch`) | Deploys stable version and moves `latest` alias |
| `docs-preview.yml` | Manual (`workflow_dispatch`) | Deploys docs from any branch under `dev-<branch>/` |

See [Docs Publishing Workflows](docs-publishing-workflows.md) for a detailed
walkthrough of each workflow and manual branch publishing instructions.

## gh-pages Branch Structure

Mike organises the `gh-pages` branch as follows:

```
gh-pages/
├── versions.json          # Mike metadata: version list, aliases, default
├── v0.2.2/                # Version subdirectory
│   └── index.html
├── v0.2.3-rc1/            # RC version subdirectory
│   └── index.html
├── v0.2.3/                # Stable version subdirectory
│   └── index.html
├── dev-my-feature/        # Branch preview subdirectory
│   └── index.html
└── index.html             # Redirect page to the default version
```

## Troubleshooting

### 404 on the root URL

- Run `mike set-default --push latest` to ensure the root redirect exists.
- Check GitHub Pages settings: **Source** must be "Deploy from a branch",
  **Branch** = `gh-pages`, **Folder** = `/ (root)`.

### Version selector missing

- Mike injects the version selector via the `versions.json` file. Ensure
  `mike` is used for deployment (not raw `mkdocs gh-deploy`).

### mike: command not found

```bash
uv sync --group dev    # installs mike via the dev dependency group
```

### Broken links in the built site

Run `mkdocs build --strict` locally before deploying. Mike also uses the
same MkDocs build pipeline, so any errors caught locally will also fail in CI.

## Files Involved

| File | Role |
|---|---|
| `mkdocs.yml` | Site configuration, theme, navigation, extensions |
| `docs/` | User-facing documentation (C++ and Python) |
| `docs/_hooks/inject_version.py` | Reads `TANGA_VERSION` env var to set the site banner version |
| `gh-pages` branch | Deployment target managed by mike (`versions.json` + subdirectories) |
| `pyproject.toml` | Dev dependency group includes `mike>=2.0` |

## Reference

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [mike on GitHub](https://github.com/jimporter/mike)
- [GitHub Pages Docs](https://docs.github.com/en/pages)