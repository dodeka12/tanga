#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Christian Perwass
#
# Installs git hooks into .git/hooks/ that automate version tagging.
# Run once per clone:  ./tools/install-hooks.sh
#
# Hooks installed:
#   post-merge  → runs version-tag.sh --push when merging into main

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOOKS_DIR="$REPO_ROOT/.git/hooks"

echo "Installing git hooks into $HOOKS_DIR"

# ---- post-merge hook --------------------------------------------------------
cat > "$HOOKS_DIR/post-merge" <<'HOOK'
#!/usr/bin/env bash
# post-merge: called after git pull / git merge.
# Only acts when we are on the 'main' branch.

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

if [[ "$CURRENT_BRANCH" != "main" ]]; then
  exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
SCRIPT="$REPO_ROOT/tools/version-tag.sh"

if [[ -x "$SCRIPT" ]]; then
  echo "[post-merge] Running version-tag.sh on branch main …"
  "$SCRIPT" --push
else
  echo "[post-merge] WARNING: $SCRIPT not found or not executable"
fi
HOOK

chmod +x "$HOOKS_DIR/post-merge"

echo "✓ post-merge hook installed"
echo ""
echo "Now every time you pull/merge into 'main',"
echo "  tools/version-tag.sh --push  will run automatically."
echo ""
echo "You can also still run the script manually:"
echo "  ./tools/version-tag.sh --dry-run"
echo "  ./tools/version-tag.sh --push"