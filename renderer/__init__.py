"""
renderer/__init__.py — renderer 패키지 공개 API

기존 bg3_renderer import 호환:
    from bg3_renderer import get_renderer, render_async, C, BG3Renderer, PIL_AVAILABLE
"""
try:
    from PIL import Image  # noqa: F401
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from renderer.palette import C
from renderer.fonts import _f, _tw, _th
from renderer.assets import (
    _safe_id, _smart_crop,
    _load_portrait, _load_stat_icon, _load_banner,
    _BASE, _STATIC, _PORT_D, _ICON_D, _BAN_D,
)
from renderer.drawing import (
    _gv, _rr, _glow, _gold_frame, _orn,
    _is_emoji, _notxt, _wrap,
    _make_base, _to_buf, _MAX_IMG_DIM,
    _bar_A, _grade_badge, _ph_portrait, _paste_stat_icon,
)
from renderer.cards import BG3Renderer
from renderer.singleton import get_renderer, render_async, _renderer_lock, _executor

__all__ = [
    "PIL_AVAILABLE",
    "C",
    "BG3Renderer",
    "get_renderer",
    "render_async",
    # drawing utils
    "_gv", "_rr", "_glow", "_gold_frame", "_orn",
    "_is_emoji", "_notxt", "_wrap",
    "_make_base", "_to_buf", "_MAX_IMG_DIM",
    "_bar_A", "_grade_badge", "_ph_portrait", "_paste_stat_icon",
    # font utils
    "_f", "_tw", "_th",
    # asset utils
    "_safe_id", "_smart_crop",
    "_load_portrait", "_load_stat_icon", "_load_banner",
    # path constants
    "_BASE", "_STATIC", "_PORT_D", "_ICON_D", "_BAN_D",
    # singleton internals
    "_renderer_lock", "_executor",
]
