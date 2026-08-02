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
#   ./tools/version-tag.sh [--dry-run] [--push] [--rc]

set -euo pipefail

DRY_RUN=false
PUSH=false
RC_MODE=false

show_help() {
  cat <<EOF
Usage: $0 [--dry-run] [--push] [--rc] [--help]

  --dry-run   Print the next tag but do not create it.
  --push      Create the tag AND push it to origin.
              Without --push the tag is only created locally.
  --rc        Create a release-candidate tag (vX.Y.Z-rcN).
              Auto-increments the RC number for the current base version.
EOF
  exit 0
}

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --push)    PUSH=true ;;
    --rc)      RC_MODE=true ;;
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

# ---- find last non-RC tag (for version bump) --------------------------------
# When in RC mode, we need to find the latest non-RC tag to determine the base
# version to bump from. Otherwise we find the latest tag of any kind.
if $RC_MODE; then
  LAST_TAG="$(git tag -l 'v*' --sort=-v:refname | grep -v '\-rc' | head -1 || true)"
  echo "Looking up latest non-RC tag for version bump..."
else
  LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
fi

if [[ -z "$LAST_TAG" ]]; then
  echo "No previous tag found – starting at v0.1.0"
  BASE="v0.1.0"
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
  BASE="v${MAJ}.${MIN}.${PAT}"
fi

# ---- RC mode: auto-increment RC number --------------------------------------
if $RC_MODE; then
  # Find existing RC tags for this base version
  RC_NEXT=1
  EXISTING_RC=$(git tag -l "${BASE}-rc*" --sort=-v:refname | head -1 || true)
  if [[ -n "$EXISTING_RC" ]]; then
    # Extract RC number and increment
    RC_CURRENT="${EXISTING_RC##*-rc}"
    if [[ "$RC_CURRENT" =~ ^[0-9]+$ ]]; then
      RC_NEXT=$((RC_CURRENT + 1))
    fi
    echo "Existing RC tag: $EXISTING_RC"
  fi
  NEXT="${BASE}-rc${RC_NEXT}"
  echo "Next RC version: $NEXT (base: $BASE)"
else
  NEXT="$BASE"
  echo "Next version: $NEXT"
fi

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