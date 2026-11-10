# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Tests for the animated-export "skip unchanged entities" contract.

The reconcile engine is a Python-emitted JS string, so these tests guard the
*emitted contract* (``node`` is not available in CI, which is Python-only; the
behavioural gate is ``js/dev/tests/anim-export-smoke.mjs``).  The contract:
``_reconcileFrame`` remembers the last applied source frame object on
``mesh.userData._src`` / ``entry.obj.userData._src`` and skips an entity
outright on an identity match — made possible because ``_expandFrames`` reuses
the same object instance for entities that did not change in a frame.
"""

from __future__ import annotations

from pytanga.viz.export._bootstrap._animation import (
    js_expand_frames,
    js_reconcile_frame,
)

_JS = js_reconcile_frame(scene_var="figScene")


def test_identity_skip_guard_precedes_update_and_image():  # noqa: ANN201
    """The skip guard must run before any update / image rebuild work."""
    assert "mesh.userData._src === ent" in _JS
    assert _JS.index("mesh.userData._src === ent") < _JS.index("updateEntityMesh(")
    assert _JS.index("mesh.userData._src === ent") < _JS.index("ent.kind === 'image'")


def test_src_assigned_on_all_four_scene_apply_paths():  # noqa: ANN201
    """``_src`` is stored on create, in-place, image-rebuild and generic rebuild."""
    assert _JS.count("mesh.userData._src = ent") == 4
    # The merged dict never appears in ``frames[]`` — storing it would make
    # every following frame look changed.
    assert "userData._src = merged" not in _JS


def test_overlay_identity_skip_and_single_assignment():  # noqa: ANN201
    """Overlays (labels) get the same rule with exactly one assignment site."""
    assert "entry.obj.userData._src === ent" in _JS
    assert _JS.count("obj.userData._src = ent") == 1


def test_expander_preserves_entity_identity():  # noqa: ANN201
    """``_expandFrames`` must keep storing the same object per unchanged id.

    This is the precondition the identity skip relies on — if the expander ever
    starts cloning entities, the skip silently stops working.
    """
    expand = js_expand_frames()
    assert "for (const ent of initial) state.set(ent.id, ent);" in expand
    assert "for (const ent of (d.set || [])) state.set(ent.id, ent);" in expand


def test_hide_loop_does_not_dispose():  # noqa: ANN201
    """An absent entity is hidden, not removed — so ``_src`` survives a gap."""
    assert "if (!targetIds.has(id)) mesh.visible = false;" in _JS
    # ``removeEntityMesh`` appears exactly twice: the image rebuild and the
    # generic rebuild branch — never in the hide loop.
    assert _JS.count("removeEntityMesh(") == 2
