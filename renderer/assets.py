"""renderer/assets.py — 에셋 로딩 및 경로 상수"""
import os
import re
from typing import Optional

from utils.logger import setup_logger

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

_log = setup_logger('bg3_renderer')

# ══════════════════════════════════════════════════════════════════
# 경로
# ══════════════════════════════════════════════════════════════════
_BASE    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STATIC  = os.path.join(_BASE, "static")
_PORT_D  = os.path.join(_STATIC, "portraits")
_ICON_D  = os.path.join(_STATIC, "icons", "stat")
_BAN_D   = os.path.join(_STATIC, "banners")

# ══════════════════════════════════════════════════════════════════
# 유효성 검사
# ══════════════════════════════════════════════════════════════════
_SAFE_ID = re.compile(r'^[가-힣a-zA-Z0-9_\-. ]+$')


def _safe_id(value: str) -> bool:
    """에셋 ID 유효성 검사 — path traversal 방지"""
    return bool(value) and bool(_SAFE_ID.match(value)) and ".." not in value


def _smart_crop(img: "Image.Image", w: int, h: int,
                face_center: float = 0.33) -> "Image.Image":
    """적응형 크롭. face_center: 세로 기준 얼굴 위치 비율 (0=상단, 1=하단)"""
    ir, br = img.width / img.height, w / h
    if ir > br:
        nh = h; nw = int(h * ir)
        img = img.resize((nw, nh), Image.LANCZOS)
        cx = (nw - w) // 2
        img = img.crop((cx, 0, cx + w, nh))
    else:
        nw = w; nh = int(w / ir)
        img = img.resize((nw, nh), Image.LANCZOS)
        # 적응형 오프셋: 세로 비율에 따라 얼굴 중심 위치 조정
        max_offset = max(0, nh - h)
        cy = min(max_offset, int(nh * face_center - h * 0.4))
        cy = max(0, cy)
        img = img.crop((0, cy, nw, cy + h))
    return img


def _load_portrait(portrait_type: str, portrait_id: str,
                   w: int, h: int) -> Optional["Image.Image"]:
    """
    초상화 로드 및 크롭.
    portrait_type: 'npc' | 'animal' | 'monster'
    portrait_id:   파일명 (확장자 제외)
    없으면 _default 폴백 → 그래도 없으면 None → 호출부에서 플레이스홀더 처리
    """
    if not _safe_id(portrait_id) or not _safe_id(portrait_type):
        return None
    folder = os.path.join(_PORT_D, portrait_type)
    # E-1 fix: portrait_id 우선, 없으면 _default 폴백
    for name in (portrait_id, "_default"):
        for ext in (".png", ".webp", ".jpg", ".jpeg"):
            p = os.path.join(folder, name + ext)
            if os.path.isfile(p):
                try:
                    img = Image.open(p).convert("RGBA")
                    return _smart_crop(img, w, h, face_center=0.30)
                except (OSError, IOError, ValueError) as e:
                    _log.warning("Portrait load failed: %s (%s)", p, e)
    return None


def _load_stat_icon(stat_key: str, size: int) -> Optional["Image.Image"]:
    """
    스탯 아이콘 로드.
    static/icons/stat/{stat_key}.png
    없으면 None → 호출부에서 다이아몬드 플레이스홀더
    """
    if not _safe_id(stat_key):
        return None
    for ext in (".png", ".webp"):
        p = os.path.join(_ICON_D, stat_key + ext)
        if os.path.isfile(p):
            try:
                img = Image.open(p).convert("RGBA")
                return img.resize((size, size), Image.LANCZOS)
            except (OSError, IOError, ValueError) as e:
                _log.warning("Stat icon load failed: %s (%s)", p, e)
    return None


def _load_banner(zone_type: str, zone_id: str,
                 w: int, h: int) -> Optional["Image.Image"]:
    """
    배너 씬 이미지 로드 및 크롭.
    zone_type: 'town' | 'hunting' | 'gathering' | 'fishing'
    zone_id:   파일명 (확장자 제외, 예: '비전타운', '고블린동굴')
    없으면 _default 폴백 → 그래도 없으면 None → 호출부에서 플레이스홀더 처리
    """
    if not _safe_id(zone_id) or not _safe_id(zone_type):
        return None
    folder = os.path.join(_BAN_D, zone_type)
    # zone_id 우선, 없으면 _default 폴백
    for name in (zone_id, "_default"):
        for ext in (".png", ".webp", ".jpg", ".jpeg"):
            p = os.path.join(folder, name + ext)
            if os.path.isfile(p):
                try:
                    img = Image.open(p).convert("RGBA")
                    return _smart_crop(img, w, h, face_center=0.5)
                except (OSError, IOError, ValueError) as e:
                    _log.warning("Banner load failed: %s (%s)", p, e)
    return None
