#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# Copyright 2025 Christian Perwass
#
# Standalone script – can be run locally or inside CI.
# Reads Conventional Commit messages since the last tag and creates
# the next semantic-version tag (vMAJOR.MINOR.PATCH).
#
# Bump rules (highest wins):
#   feat! / scope! / BREAKING CHANGE  → major
#   feat:                             → minor
#   everything else                   → patch  (default)
#
# Usage:
#   ./tools/version-tag.sh [--dry-run] [--push]

set -euo pipefail

DRY_RUN=false
PUSH=false
NO_PUSH_MESSAGE=true

show_help() {
  cat <<EOF
Usage: $0 [--dry-run] [--push] [--help]

  --dry-run   Print the next tag but do not create it.
  --push      Create the tag AND push it to origin.
              Without --push the tag is only created locally.
EOF
  exit 0
}

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --push)    PUSH=true ;;
    --help)    show_help ;;
    *)         echo "Unknown option: $arg"; exit 1 ;;
  esac
done

# ---- inside a git repo? ----------------------------------------------------
if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Not inside a git repository – aborting."
  exit 1
fi

# ---- helper -----------------------------------------------------------------
read_semver() {
  local ver="${1#v}"
  IFS='.' read -r _maj _min _pat <<< "$ver"
  printf -v "$2" '%s' "${_maj:-0}"
  printf -v "$3" '%s' "${_min:-0}"
  printf -v "$4" '%s' "${_pat:-0}"
}

# ---- find last tag ----------------------------------------------------------
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"

if [[ -z "$LAST_TAG" ]]; then
  echo "No previous tag found – starting at v0.1.0"
  NEXT="v0.1.0"
else
  echo "Previous tag: $LAST_TAG"

  # commits since that tag
  if [[ "$LAST_TAG" == "$(git describe --tags --exact-match HEAD 2>/dev/null || true)" ]]; then
    COMMITS=""
  else
    COMMITS="$(git log "${LAST_TAG}..HEAD" --pretty=format:'%s')"
  fi

  if [[ -z "$COMMITS" ]]; then
    echo "No new commits since $LAST_TAG – nothing to bump"
    exit 0
  fi

  echo "Commits since last tag:"
  echo "$COMMITS"
  echo ""

  # ---- decide bump level ----------------------------------------------------
  BUMP="patch"
  while IFS= read -r msg; do
    # 1) breaking change
    if echo "$msg" | grep -qE '^[^:]+!:|BREAKING[ _]CHANGE'; then
      BUMP="major"
      break
    fi
    # 2) feature
    if echo "$msg" | grep -qE '^feat(\([^)]*\))?:'; then
      BUMP="minor"
    fi
    # everything else stays patch
  done <<< "$COMMITS"

  echo "Determined bump: $BUMP"

  read_semver "$LAST_TAG" MAJ MIN PAT
  case "$BUMP" in
    major) MAJ=$((MAJ + 1)); MIN=0; PAT=0 ;;
    minor) MIN=$((MIN + 1)); PAT=0 ;;
    patch) PAT=$((PAT + 1)) ;;
  esac
  NEXT="v${MAJ}.${MIN}.${PAT}"
fi

echo "Next version: $NEXT"

if $DRY_RUN; then
  exit 0
fi

# ---- create tag -------------------------------------------------------------
git tag -a "$NEXT" -m "Release $NEXT (auto)"

if $PUSH; then
  git push origin "$NEXT"
  echo "Pushed tag $NEXT to origin."
else
  echo "Tag $NEXT created locally."
  echo "Run 'git push origin $NEXT' to publish it."
fi