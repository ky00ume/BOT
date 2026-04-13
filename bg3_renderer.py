"""
bg3_renderer.py — 하위 호환 re-export 래퍼

실제 구현은 renderer/ 패키지에 있습니다:
  renderer/palette.py   — class C (색상 팔레트)
  renderer/fonts.py     — 폰트 탐색 및 LRU 캐시
  renderer/assets.py    — 에셋 로딩 + 경로 상수
  renderer/drawing.py   — 저수준 드로잉 유틸
  renderer/cards.py     — BG3Renderer 클래스
  renderer/singleton.py — get_renderer(), render_async()

기존 임포트 예시 (전부 동작):
    from bg3_renderer import get_renderer, render_async, C, BG3Renderer, PIL_AVAILABLE
"""
# ruff: noqa: F401, F403
from renderer import (
    PIL_AVAILABLE,
    C,
    BG3Renderer,
    get_renderer,
    render_async,
    _renderer_lock,
    _executor,
    # drawing utils
    _gv, _rr, _glow, _gold_frame, _orn,
    _is_emoji, _notxt, _wrap,
    _make_base, _to_buf, _MAX_IMG_DIM,
    _bar_A, _grade_badge, _ph_portrait, _paste_stat_icon,
    # font utils
    _f, _tw, _th,
    # asset utils
    _safe_id, _smart_crop,
    _load_portrait, _load_stat_icon, _load_banner,
    # path constants
    _BASE, _STATIC, _PORT_D, _ICON_D, _BAN_D,
)

# Keep legacy module-level logger for anything that imported _log from here
from utils.logger import setup_logger as _setup_logger
_log = _setup_logger('bg3_renderer')

