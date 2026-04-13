"""renderer/fonts.py — 폰트 탐색 및 LRU 캐시"""
import os
import threading
from collections import OrderedDict

from utils.logger import setup_logger

try:
    from PIL import ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

_log = setup_logger('bg3_renderer')

# 프로젝트 루트 기준 폰트 경로 (renderer/ 한 단계 위)
_BASE   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FONT_D = os.path.join(_BASE, "static", "fonts")


def _find_fonts():
    """크로스 플랫폼 폰트 경로 탐색. 프로젝트 번들 우선."""
    candidates_regular: list = []
    candidates_bold: list = []
    candidates_serif: list = []

    # 1순위: 프로젝트 번들 폰트 (static/fonts/)
    if os.path.isdir(_FONT_D):
        for f in os.listdir(_FONT_D):
            fl = f.lower()
            fp = os.path.join(_FONT_D, f)
            if "noto" in fl and "cjk" in fl:
                if "bold" in fl:
                    candidates_bold.insert(0, fp)
                else:
                    candidates_regular.insert(0, fp)
            elif "lora" in fl or "liberation" in fl:
                candidates_serif.insert(0, fp)

    # 2순위: 시스템 폰트 경로 (OS별)
    if os.name == "nt":  # Windows
        winfonts = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
        localfonts = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")
        for d in [winfonts, localfonts]:
            if not os.path.isdir(d):
                continue
            try:
                for f in os.listdir(d):
                    fl = f.lower(); fp = os.path.join(d, f)
                    if "noto" in fl and "cjk" in fl and "serif" in fl:
                        if "bold" in fl: candidates_bold.append(fp)
                        else: candidates_regular.append(fp)
                    elif "malgun" in fl:  # 맑은 고딕 fallback
                        if "bold" in fl: candidates_bold.append(fp)
                        else: candidates_regular.append(fp)
                    elif "lora" in fl:
                        candidates_serif.append(fp)
            except OSError:
                _log.debug('bg3_renderer: Windows 폰트 디렉터리 읽기 실패 (%s)', d, exc_info=True)
    else:  # Linux / macOS
        linux_paths = [
            # Serif (우선)
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
            "/usr/share/fonts/noto-cjk/NotoSerifCJK-Regular.ttc",
            "/usr/share/fonts/noto-cjk/NotoSerifCJK-Bold.ttc",
            # Sans (fallback — 한글 지원이면 충분)
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
            # 기타
            "/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        ]
        # 추가: /usr/share/fonts 하위 재귀 탐색 (위 고정 경로에 없을 때)
        _extra_dirs = [
            "/usr/share/fonts/truetype",
            "/usr/share/fonts/opentype",
            "/usr/local/share/fonts",
            os.path.expanduser("~/.local/share/fonts"),
        ]
        for _ed in _extra_dirs:
            if not os.path.isdir(_ed):
                continue
            try:
                for _root, _dirs, _files in os.walk(_ed):
                    for _fn in _files:
                        _fl = _fn.lower()
                        if "noto" in _fl and "cjk" in _fl and _fl.endswith((".ttc", ".ttf", ".otf")):
                            _fp = os.path.join(_root, _fn)
                            if _fp not in linux_paths:
                                linux_paths.append(_fp)
            except OSError:
                _log.debug('bg3_renderer: 폰트 디렉터리 탐색 실패 (%s)', _ed, exc_info=True)
        for p in linux_paths:
            if os.path.isfile(p):
                fl = os.path.basename(p).lower()
                if "bold" in fl:
                    candidates_bold.append(p)
                elif "noto" in fl and "cjk" in fl:
                    candidates_regular.append(p)
                else:
                    candidates_serif.append(p)

    return candidates_regular, candidates_bold, candidates_serif


_FONTS_REG, _FONTS_BOLD, _FONTS_SERIF = _find_fonts()

# ── LRU 폰트 캐시 (최대 64개) ──────────────────────────────────
_FC_MAX = 64
_FC: OrderedDict = OrderedDict()
_fc_lock = threading.Lock()


def _f(size: int, bold: bool = False):
    k = (size, bold)
    with _fc_lock:
        if k in _FC:
            _FC.move_to_end(k)
            return _FC[k]
    search = (_FONTS_BOLD + _FONTS_SERIF) if bold else (_FONTS_REG + _FONTS_SERIF + _FONTS_BOLD)
    for p in search:
        try:
            font = ImageFont.truetype(p, size)
            with _fc_lock:
                _FC[k] = font
                if len(_FC) > _FC_MAX:
                    _FC.popitem(last=False)
            return font
        except (OSError, IOError) as e:
            _log.debug("Font load failed: %s (%s)", p, e)
    font = ImageFont.load_default()
    with _fc_lock:
        _FC[k] = font
        if len(_FC) > _FC_MAX:
            _FC.popitem(last=False)
    return font


def _tw(d, t, f) -> int:
    try:
        bb = d.textbbox((0, 0), t, font=f)
        return bb[2] - bb[0]  # type: ignore[no-any-return]
    except (AttributeError, TypeError):
        return len(t) * max(7, getattr(f, "size", 12) // 2)


def _th(d, t, f) -> int:
    try:
        bb = d.textbbox((0, 0), t, font=f)
        return bb[3] - bb[1]  # type: ignore[no-any-return]
    except (AttributeError, TypeError):
        return getattr(f, "size", 12)  # type: ignore[no-any-return]
