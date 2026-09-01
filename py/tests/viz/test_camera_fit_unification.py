# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Regression tests for the unified camera-fit module.

The ortho/aspect math used to be duplicated in three places that drifted apart,
which made 2D ``fit_camera`` fit against the window size instead of the pane.
These tests pin the unified ``camera-fit.js`` contract (one source of truth) and
guard the 3D fit path against a future aspect regression.
"""

from __future__ import annotations

from pathlib import Path

import pytanga.viz
from pytanga.viz.export._bootstrap._html import generate_bootstrap_js
from pytanga.viz.export._bootstrap._scene import js_autofit_camera
from pytanga.viz.export._figure_html import render_figure
from pytanga.viz.export._html import render_snapshot


def test_bootstrap_bundles_single_camera_fit_module():
    b = generate_bootstrap_js("")
    assert "function finiteAspect(" in b
    assert "function orthoFrustum(" in b
    assert "function applyOrthoFrustum(" in b
    # The old hand-maintained copies must be gone.
    assert "_finiteAspectExport" not in b
    assert "_orthoFrustum2d" not in b
    assert "_finiteAspect(" not in b


def test_bundled_fit_camera_accepts_size():
    b = generate_bootstrap_js("")
    assert (
        "function fitCamera(sceneObjects, camera, controls, spaceDim, width, height)"
        in b
    )


def test_bundled_fit_camera_delegates_to_shared_ortho_frustum():
    b = generate_bootstrap_js("")
    # The 2D branch calls the shared helper rather than computing aspect inline.
    assert "orthoFrustum(xmin, xmax, ymin, ymax, true, 0" in b


def test_fit_camera_3d_branch_is_aspect_independent():
    src = Path(pytanga.viz.__file__).parent / "templates" / "fit_camera.js"
    fit3d = src.read_text(encoding="utf-8").split("// ── 3D perspective fit ──", 1)[1]
    assert "const distance = (radius / Math.sin(fov / 2)) * 1.1;" in fit3d
    assert "innerWidth" not in fit3d
    assert "innerHeight" not in fit3d


def test_js_autofit_camera_emits_size_args():
    js = js_autofit_camera(
        registry_var="reg",
        camera_var="cam",
        controls_var="ctl",
        cam_explicit=False,
        space_dim=2,
        width_expr="W",
        height_expr="H",
    )
    assert "fitCamera(reg, cam, ctl, 2, W, H);" in js


def test_js_autofit_camera_empty_when_explicit():
    assert (
        js_autofit_camera(
            registry_var="reg",
            camera_var="cam",
            controls_var="ctl",
            cam_explicit=True,
            space_dim=2,
            width_expr="W",
            height_expr="H",
        )
        == ""
    )


def test_snapshot_full_page_uses_window_size():
    html = render_snapshot([], {"space_dim": 2})
    assert (
        "fitCamera(sceneRegistry, adapterCamera, adapterControls, 2, "
        "window.innerWidth, window.innerHeight)" in html
    )


def test_responsive_figure_uses_container_size():
    html = render_figure(
        [],
        {"space_dim": 2},
        {"width": 400, "height": 300, "responsive": True},
        {"title": "T"},
    )
    assert (
        "fitCamera(figRegistry, figCamera, figControls, 2, "
        "(figContainer.clientWidth || window.innerWidth), "
        "(figContainer.clientHeight || window.innerHeight))" in html
    )


def test_snapshot_resize_recomputes_2d_ortho_frustum():
    html = render_snapshot([], {"space_dim": 2})
    assert "applyOrthoFrustum(adapterCamera, rw, rh)" in html


def test_responsive_figure_resize_recomputes_2d_ortho_frustum():
    html = render_figure([], {"space_dim": 2}, {"responsive": True}, {})
    assert "applyOrthoFrustum(figCamera, rw, rh)" in html
