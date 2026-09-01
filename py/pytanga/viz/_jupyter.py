# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Jupyter display mixin providing ``_repr_html_`` for the Tanga 3D viewer.

Used by both :class:`Visualizer` and :class:`VizSceneHandle` so that each
renders an inline iframe when displayed in a Jupyter notebook cell.
"""

from __future__ import annotations


class _JupyterDisplayMixin:
    """Mixin providing Jupyter notebook inline display via ``_repr_html_``.

    The host class must supply these attributes (by duck-typing, no
    abstract properties so the host can freely assign them):

    * ``_server`` — the current :class:`VizServer` or ``None``
    * ``_name: str`` — scene name used in the iframe title (``""`` for main)
    * ``_viewer_name: str | None`` — optional viewer label
    * ``url: str`` — the HTTP URL of the scene
    """

    _viewer_name: str | None = None
    _name: str = ""

    # ── Jupyter support ──────────────────────────────────────

    def _repr_html_(self) -> str:
        """Return an HTML iframe embedding this scene."""
        if self._server is None:  # type: ignore[has-type]
            return (
                "<p style='color:#888'>Visualizer not started. "
                "Call <code>.start()</code> first.</p>"
            )
        height = 500
        src = self.url  # type: ignore[has-type]
        if self._viewer_name:
            src += f"?viewer={self._viewer_name}"
        title = "Tanga 3D Viewer"
        if self._name:
            title += f" — {self._name}"
        return (
            f'<iframe src="{src}" width="100%" height="{height}px" '
            f'style="border: 1px solid #444; border-radius: 4px;" '
            f'title="{title}"></iframe>'
        )
