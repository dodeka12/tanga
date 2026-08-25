# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass
"""Shared JS code generator for Tanga HTML export bootstraps.

Re-exports all public functions and constants from the submodules.
Import from here instead of the old ``_bootstrap_core.py``.
"""

from pytanga.viz.export._bootstrap._animation import (  # noqa: F401
    embed_animation_data,
    get_anim_data_js,
    get_anim_decompress_js,
    js_animated_render_loop,
    js_animation_data_init,
    js_animation_state,
    js_controls_html,
    js_controls_ui,
    js_reconcile_frame,
)
from pytanga.viz.export._bootstrap._entities import (  # noqa: F401
    js_scene_build,
)
from pytanga.viz.export._bootstrap._errors import js_cdn_check_script  # noqa: F401
from pytanga.viz.export._bootstrap._html import (  # noqa: F401
    _RENDERER_FILES,
    _strip_imports,
    generate_bootstrap_js,
    html_fullpage_template,
    html_snippet_template,
    katex_css_if_needed,
)
from pytanga.viz.export._bootstrap._overlays import (  # noqa: F401
    js_annotation_panel,
    js_footer,
    js_title_overlay,
)
from pytanga.viz.export._bootstrap._scene import (  # noqa: F401
    js_apply_camera,
    js_autofit_camera,
    js_imports,
    js_render_loop,
    js_resize_handler,
    js_scene_setup,
)
from pytanga.viz.export._bootstrap._utils import (  # noqa: F401
    _escape_html,
    _escape_js,
    _format_js_bool,
    contains_math,
)
