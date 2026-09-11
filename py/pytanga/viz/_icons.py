# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

"""Icon identifiers for Tanga 3D viewer controls.

Icons are opaque ``family:name`` strings (e.g. ``material:settings``,
``uc:▶``).  The Python side only defines the collections for autocompletion
and a small grammar helper; the family → font / render mapping lives in the
frontend (``controls-panel.js``), so new families can be added without
changing the wire format or the control model.
"""

from __future__ import annotations

from enum import StrEnum

#: Separator between the icon family and the icon name in an icon id.
FAMILY_SEPARATOR = ":"


class EIconMaterial(StrEnum):
    """Google Material Symbols ligature names (rendered via the online font)."""

    ACCOUNT_CIRCLE = "material:account_circle"
    ADD = "material:add"
    ADD_CIRCLE = "material:add_circle"
    ADD_COLUMN_LEFT = "material:add_column_left"
    ADD_COLUMN_RIGHT = "material:add_column_right"
    ADD_ROW_ABOVE = "material:add_row_above"
    ADD_ROW_BELOW = "material:add_row_below"
    APPS = "material:apps"
    ARROW_BACK = "material:arrow_back"
    ARROW_DOWNWARD = "material:arrow_downward"
    ARROW_DROP_DOWN = "material:arrow_drop_down"
    ARROW_DROP_UP = "material:arrow_drop_up"
    ARROW_FORWARD = "material:arrow_forward"
    ARROW_LEFT = "material:arrow_left"
    ARROW_RIGHT = "material:arrow_right"
    ARROW_UPWARD = "material:arrow_upward"
    ATTACH_FILE = "material:attach_file"
    BOOKMARK = "material:bookmark"
    BUILD = "material:build"
    CAMERA = "material:camera"
    CHECK = "material:check"
    CHECK_CIRCLE = "material:check_circle"
    CHEVRON_LEFT = "material:chevron_left"
    CHEVRON_RIGHT = "material:chevron_right"
    CLOSE = "material:close"
    CLOUD_DOWNLOAD = "material:cloud_download"
    CLOUD_UPLOAD = "material:cloud_upload"
    CODE = "material:code"
    CONTENT_COPY = "material:content_copy"
    CREATE = "material:create"
    DELETE = "material:delete"
    DOWNLOAD = "material:download"
    EDIT = "material:edit"
    ERROR = "material:error"
    EXPAND_LESS = "material:expand_less"
    EXPAND_MORE = "material:expand_more"
    FAVORITE = "material:favorite"
    FILE_DOWNLOAD = "material:file_download"
    FILE_UPLOAD = "material:file_upload"
    FILTER_LIST = "material:filter_list"
    FIT_PAGE_HEIGHT = "material:fit_page_height"
    FIT_PAGE_WIDTH = "material:fit_page_width"
    FLAG = "material:flag"
    FOLDER = "material:folder"
    FOLDER_OPEN = "material:folder_open"
    FULLSCREEN = "material:fullscreen"
    FULLSCREEN_EXIT = "material:fullscreen_exit"
    GRID_VIEW = "material:grid_view"
    HELP = "material:help"
    HELP_OUTLINE = "material:help_outline"
    HISTORY = "material:history"
    HOME = "material:home"
    INFO = "material:info"
    KEYBOARD = "material:keyboard"
    LANGUAGE = "material:language"
    LAYERS = "material:layers"
    LIGHTBULB = "material:lightbulb"
    LINK = "material:link"
    LIST = "material:list"
    LOCK = "material:lock"
    LOCK_OPEN = "material:lock_open"
    MAP = "material:map"
    MENU = "material:menu"
    MORE_HORIZ = "material:more_horiz"
    MORE_VERT = "material:more_vert"
    MY_LOCATION = "material:my_location"
    NOTIFICATIONS = "material:notifications"
    OPEN_IN_NEW = "material:open_in_new"
    PALETTE = "material:palette"
    PAUSE = "material:pause"
    PERSON = "material:person"
    PHOTO = "material:photo"
    PLAY_ARROW = "material:play_arrow"
    POWER_SETTINGS_NEW = "material:power_settings_new"
    PRINT = "material:print"
    REDO = "material:redo"
    REFRESH = "material:refresh"
    REMOVE = "material:remove"
    REMOVE_CIRCLE = "material:remove_circle"
    RESTART_ALT = "material:restart_alt"
    SAVE = "material:save"
    SCHEDULE = "material:schedule"
    SEARCH = "material:search"
    SEND = "material:send"
    SETTINGS = "material:settings"
    SHARE = "material:share"
    SKIP_NEXT = "material:skip_next"
    SKIP_PREVIOUS = "material:skip_previous"
    SORT = "material:sort"
    SPLITSCREEN_BOTTOM = "material:splitscreen_bottom"
    SPLITSCREEN_LEFT = "material:splitscreen_left"
    SPLITSCREEN_RIGHT = "material:splitscreen_right"
    SPLITSCREEN_TOP = "material:splitscreen_top"
    STAR = "material:star"
    STAR_BORDER = "material:star_border"
    STOP = "material:stop"
    SWAP_HORIZ = "material:swap_horiz"
    SWAP_VERT = "material:swap_vert"
    SYNC = "material:sync"
    TERMINAL = "material:terminal"
    TIMER = "material:timer"
    TUNE = "material:tune"
    UNDO = "material:undo"
    UPDATE = "material:update"
    UPLOAD = "material:upload"
    VIDEOCAM = "material:videocam"
    VIEW_LIST = "material:view_list"
    VIEW_MODULE = "material:view_module"
    VISIBILITY = "material:visibility"
    VISIBILITY_OFF = "material:visibility_off"
    VOLUME_OFF = "material:volume_off"
    VOLUME_UP = "material:volume_up"
    WARNING = "material:warning"
    ZOOM_IN = "material:zoom_in"
    ZOOM_OUT = "material:zoom_out"


class EIconUC(StrEnum):
    """Unicode symbol icons (rendered as literal text, no font needed)."""

    ARROW_DOWN = "uc:↓"
    ARROW_LEFT = "uc:←"
    ARROW_RIGHT = "uc:→"
    ARROW_UP = "uc:↑"
    CHECK = "uc:✓"
    CIRCLE = "uc:○"
    CLOSE = "uc:✕"
    CROSS = "uc:✗"
    DIAMOND = "uc:◆"
    DOT = "uc:●"
    GEAR = "uc:⚙"
    HEART = "uc:♥"
    INFO = "uc:ℹ"
    LIGHTNING = "uc:⚡"
    PAUSE = "uc:⏸"
    PENCIL = "uc:✎"
    PLAY = "uc:▶"
    PLAY_REVERSE = "uc:◀"
    RESIZE = "uc:⤢"
    STAR = "uc:★"
    STOP = "uc:⏹"
    TRIANGLE_DOWN = "uc:▼"
    TRIANGLE_UP = "uc:▲"
    WARNING = "uc:⚠"


#: Any valid icon identifier: a curated enum member or a raw ``family:name``
#: (or bare name) string.
Icon = EIconMaterial | EIconUC | str


def icon_family(icon_id: str) -> str:
    """Return the icon family prefix, defaulting to ``"material"`` when unset."""
    if FAMILY_SEPARATOR not in icon_id:
        return "material"
    return icon_id.split(FAMILY_SEPARATOR, 1)[0] or "material"


def icon_name(icon_id: str) -> str:
    """Return the icon name (the part after the first ``:``, or the whole id)."""
    if FAMILY_SEPARATOR not in icon_id:
        return icon_id
    return icon_id.split(FAMILY_SEPARATOR, 1)[1]
