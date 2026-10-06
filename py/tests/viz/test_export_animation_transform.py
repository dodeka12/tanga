# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Animated HTML export must re-apply node transforms for in-place updates.

Regression test for exported animations never moving entities placed via the
transform wrapper when their updater performs an in-place update (returns
``true``) instead of a rebuild — e.g. ``Point``/``Circle``, whose per-frame
change is a position/rotation/scale only.
"""

from pytanga.geometry.entities import Point
from pytanga.viz.export._animated_figure import render_export_animated_html
from pytanga.viz.export._animation_recording import AnimationRecording
from pytanga.viz.scene import Scene


def _moving_point_recording() -> AnimationRecording:
    scene = Scene()
    entity_id = scene.add(Point(0, 0, 0))

    rec = AnimationRecording(scene)
    rec.capture_frame()

    scene.update_entity(entity_id, Point(5, -3, 2))
    rec.capture_frame()

    return rec


def test_recorded_frames_differ_in_transform():  # noqa: ANN201
    rec = _moving_point_recording()
    frame0 = next(d for d in rec.frames[0] if d["kind"] == "Point")
    frame1 = next(d for d in rec.frames[1] if d["kind"] == "Point")
    assert frame0["transform"]["position"] != frame1["transform"]["position"]


def test_animated_export_reapplies_transform_for_in_place_update():  # noqa: ANN201
    rec = _moving_point_recording()
    html = render_export_animated_html(rec.to_dict())

    # The transform-reapplication must appear on the in-place-update branch of
    # the generated `_reconcileFrame`, mirroring the live viewer's `transform`
    # aspect handling.
    assert "applyTransformToObject(entry.obj, ent.transform)" in html

    # The helper must be exposed on the `window.__tanga` bridge (and hence
    # destructured into the adapter scope) for the generated call to resolve.
    assert "applyTransformToObject" in html
