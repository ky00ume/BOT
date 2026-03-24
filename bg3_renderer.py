"""
bg3_renderer.py — 발더스게이트3 스타일 PIL 렌더링 엔진 (최종)
비전 타운 봇 전용 디자인 시스템

에셋 경로 규칙:
  초상화:  static/portraits/{npc|animal|monster}/{id}.png
  스탯 아이콘: static/icons/stat/{str|dex|int|will|luck}.png
  배너:    static/banners/{town|hunting|gathering|fishing}/{zone_id}.png|.webp
  → 파일이 없으면 플레이스홀더 자동 표시, 레이아웃 미붕괴 보장
"""
import io, os, math, re, logging, threading
from typing import Optional
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

_log = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════
# 경로
# ══════════════════════════════════════════════════════════════════
_BASE    = os.path.dirname(os.path.abspath(__file__))
_STATIC  = os.path.join(_BASE, "static")
_PORT_D  = os.path.join(_STATIC, "portraits")
_ICON_D  = os.path.join(_STATIC, "icons", "stat")
_BAN_D   = os.path.join(_STATIC, "banners")
_FONT_D  = os.path.join(_STATIC, "fonts")

# ── 폰트 탐색 (프로젝트 번들 → 시스템 경로 자동 탐색) ──────────
def _find_fonts():
    """크로스 플랫폼 폰트 경로 탐색. 프로젝트 번들 우선."""
    candidates_regular = []
    candidates_bold = []
    candidates_serif = []

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
                pass
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
                pass
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
        return bb[2] - bb[0]
    except (AttributeError, TypeError):
        return len(t) * max(7, getattr(f, "size", 12) // 2)

def _th(d, t, f) -> int:
    try:
        bb = d.textbbox((0, 0), t, font=f)
        return bb[3] - bb[1]
    except (AttributeError, TypeError):
        return getattr(f, "size", 12)


# ══════════════════════════════════════════════════════════════════
# 에셋 로더
# ══════════════════════════════════════════════════════════════════

_SAFE_ID = re.compile(r'^[가-힣a-zA-Z0-9_\-. ]+$')

def _safe_id(value: str) -> bool:
    """에셋 ID 유효성 검사 — path traversal 방지"""
    return bool(value) and _SAFE_ID.match(value) and ".." not in value

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
    없으면 None 반환 → 호출부에서 플레이스홀더 처리
    """
    if not _safe_id(portrait_id) or not _safe_id(portrait_type):
        return None
    folder = os.path.join(_PORT_D, portrait_type)
    for ext in (".png", ".webp", ".jpg", ".jpeg"):
        p = os.path.join(folder, portrait_id + ext)
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
    없으면 None → 호출부에서 플레이스홀더 처리
    """
    if not _safe_id(zone_id) or not _safe_id(zone_type):
        return None
    folder = os.path.join(_BAN_D, zone_type)
    for ext in (".png", ".webp", ".jpg", ".jpeg"):
        p = os.path.join(folder, zone_id + ext)
        if os.path.isfile(p):
            try:
                img = Image.open(p).convert("RGBA")
                return _smart_crop(img, w, h, face_center=0.5)
            except (OSError, IOError, ValueError) as e:
                _log.warning("Banner load failed: %s (%s)", p, e)
    return None


# ══════════════════════════════════════════════════════════════════
# 색상 팔레트
# ══════════════════════════════════════════════════════════════════
class C:
    BG0 = (8,7,18);   BG1 = (14,12,28); BG2 = (20,18,38); BG3 = (28,24,50)
    GOLD_HI  = (235,200,110); GOLD_MID = (195,158,78); GOLD_LO = (130,100,42)
    GOLD_GL  = (255,225,130,55)
    TXT_HI   = (245,238,222); TXT_MID  = (195,186,168); TXT_LO  = (128,118,102)
    TXT_LBL  = (148,138,122)
    TEAL_HI  = (88,220,210);  TEAL_MID = (52,168,160);  TEAL_LO = (28,100,96)
    SEP      = (52,48,68)
    RARITY = {
        "Normal":   (155,155,155), "Rare":      (80,155,230),
        "Epic":     (160,90,255),  "Legendary": (245,200,45),
        "Fail":     (220,65,55),
    }
    RARITY_GL = {
        "Normal":   (50,50,50,35),   "Rare":      (25,70,150,45),
        "Epic":     (70,25,130,50),  "Legendary": (155,105,0,55),
        "Fail":     (115,15,8,45),
    }
    SYS = {
        "battle":  (155,25,42),  "npc":    (48,125,78),
        "shop":    (180,150,28), "status": (78,122,190),
        "quest":   (180,115,32), "rest":   (82,82,185),
        "system":  (60,52,80),   "fishing":(30,115,150),
        "cooking": (160,90,30),  "craft":  (80,110,150),
    }
    # 바 색상: (기본, 하이라이트)
    HP  = ((195,52,52),  (255,95,75))
    MP  = ((50,88,195),  (95,145,255))
    EN  = ((42,162,70),  (85,215,95))
    EXP = ((48,162,155), (82,215,205))
    BAR_BG = (8,7,18); BAR_FR = (140,110,45)


# ══════════════════════════════════════════════════════════════════
# 저수준 드로잉 유틸
# ══════════════════════════════════════════════════════════════════

def _gv(img, x0,y0,x1,y1, ct, cb, at=255, ab=255):
    """수직 그라디언트"""
    d = ImageDraw.Draw(img); h = y1-y0
    if h <= 0: return
    r0,g0,b0=ct[:3]; r1,g1,b1=cb[:3]
    for dy in range(h):
        t = dy/max(h-1,1)
        r=round(r0+(r1-r0)*t); g=round(g0+(g1-g0)*t); b=round(b0+(b1-b0)*t)
        a=round(at+(ab-at)*t)
        d.line([(x0,y0+dy),(x1,y0+dy)], fill=(r,g,b,a))

def _rr(img, x0,y0,x1,y1, rad, fill=None, outline=None, lw=1):
    """RGBA 둥근 사각형"""
    ov = Image.new("RGBA", img.size, (0,0,0,0))
    d  = ImageDraw.Draw(ov)
    if fill:   d.rounded_rectangle([x0,y0,x1,y1], radius=rad, fill=fill)
    if outline: d.rounded_rectangle([x0,y0,x1,y1], radius=rad, outline=outline, width=lw)
    img.alpha_composite(ov)

def _glow(img, x0,y0,x1,y1, color, rad=0, blur=8):
    """글로우"""
    g = Image.new("RGBA", img.size, (0,0,0,0))
    r,gc,b = color[:3]; a = color[3] if len(color)>3 else 70
    if rad == 0:
        ImageDraw.Draw(g).rectangle([x0,y0,x1,y1], fill=(r,gc,b,a))
    else:
        ImageDraw.Draw(g).rounded_rectangle([x0,y0,x1,y1], radius=rad, fill=(r,gc,b,a))
    g = g.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(g)

def _gold_frame(img, radius=16):
    """BG3 금장 3중 테두리 + 코너 다이아몬드"""
    w,h = img.size; d = ImageDraw.Draw(img)
    _glow(img, 2,2,w-3,h-3, C.GOLD_GL, rad=radius+2, blur=6)
    d.rounded_rectangle([1,1,w-2,h-2], radius=radius, outline=C.GOLD_HI, width=2)
    d.rounded_rectangle([5,5,w-6,h-6], radius=max(radius-4,4), outline=C.GOLD_LO, width=1)
    S = 9
    for cx,cy in [(2,2),(w-3,2),(2,h-3),(w-3,h-3)]:
        d.polygon([(cx,cy-S),(cx+S,cy),(cx,cy+S),(cx-S,cy)], fill=C.GOLD_HI)
        s2 = S//2
        d.polygon([(cx,cy-s2),(cx+s2,cy),(cx,cy+s2),(cx-s2,cy)], fill=C.BG0)

def _orn(img, d, x0,y,x1, color=None, thick=1):
    """장식 구분선"""
    col = color or C.GOLD_MID
    d.line([(x0+12,y),(x1-12,y)], fill=col, width=thick)
    for cx in [x0+7, x1-7]:
        d.polygon([(cx,y-4),(cx+4,y),(cx,y+4),(cx-4,y)], fill=col)

def _is_emoji(cp: int) -> bool:
    """이모지 유니코드 범위 판정"""
    return (0x1F000 <= cp <= 0x1FFFF or 0x2600 <= cp <= 0x27BF
            or 0x2300 <= cp <= 0x23FF or 0xFE00 <= cp <= 0xFE0F
            or 0x200D == cp or 0x20E3 == cp)

def _notxt(d, pos, text, font, fill):
    """이모지 제외 텍스트 (깨짐 방지) — 폭 보정 포함"""
    clean = ""
    for ch in text:
        if _is_emoji(ord(ch)):
            clean += " "
        else:
            clean += ch
    d.text(pos, clean, font=font, fill=fill)

def _wrap(d, text, font, x,y, maxw, fill, lh=21) -> int:
    """자동 줄바꿈, 마지막 y 반환"""
    line = ""; cy = y
    for ch in text:
        test = line+ch
        if _tw(d,test,font) > maxw and line:
            _notxt(d,(x,cy), line, font, fill); cy+=lh; line=ch
        else: line = test
    if line: _notxt(d,(x,cy), line, font, fill); cy+=lh
    return cy

def _make_base(w,h, sys_key="system", grade="Normal") -> "Image.Image":
    """카드 베이스 배경 생성"""
    img = Image.new("RGBA",(w,h),(0,0,0,0))
    _gv(img,0,0,w,h, C.BG1,C.BG0)
    sc = C.SYS.get(sys_key, C.SYS["system"])
    _glow(img,0,h//2,w,h, sc, rad=0, blur=45)
    rc = C.RARITY.get(grade,(60,60,60))
    _glow(img,0,0,w,h//3, rc, rad=0, blur=30)
    # 미묘한 대각선 광택
    ov = Image.new("RGBA",(w,h),(0,0,0,0)); dp = ImageDraw.Draw(ov)
    for i in range(0,w+h,60):
        dp.line([(i,0),(0,i)], fill=(255,255,255,4), width=1)
    img.alpha_composite(ov)
    # 둥근 마스크
    mk = Image.new("L",(w,h),0)
    ImageDraw.Draw(mk).rounded_rectangle([0,0,w-1,h-1], radius=16, fill=255)
    r = Image.new("RGBA",(w,h),(0,0,0,0)); r.paste(img, mask=mk)
    return r

_MAX_IMG_DIM = 4096

def _to_buf(img) -> io.BytesIO:
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    buf.seek(0); return buf


# ══════════════════════════════════════════════════════════════════
# ★ 게이지 바 — 시안 A (세그먼트 노치, 최종 확정)
# ══════════════════════════════════════════════════════════════════

def _bar_A(img, d, x,y, w,h, cur,mx, colors, label="", show_val=True):
    """
    BG3 스타일 세그먼트 바 (시안 A 확정)
    - 좌→우 밝아지는 그라디언트
    - 10% 간격 수직 노치
    - 상단 하이라이트 + 하단 그림자
    - 이중 금색 외부 프레임
    """
    ratio = max(0.0, min(1.0, cur/max(mx,1)))
    bc, hc = colors
    r,g,b  = bc
    fw     = int(w*ratio)

    # ① 이중 외부 프레임
    d.rectangle([x-2,y-2,x+w+2,y+h+2], outline=(140,110,45), width=1)
    d.rectangle([x-1,y-1,x+w+1,y+h+1], outline=(80,60,20),   width=1)

    # ② 배경 홈
    d.rectangle([x,y,x+w,y+h], fill=C.BAR_BG)

    # ③ 채움 그라디언트 (좌→우)
    if fw > 0:
        for px in range(fw):
            t  = px/max(fw-1,1)
            cr = round(r*0.65 + r*0.35*t)
            cg = round(g*0.65 + g*0.35*t)
            cb2= round(b*0.65 + b*0.35*t)
            d.line([(x+px,y+1),(x+px,y+h-1)], fill=(cr,cg,cb2))

        # ④ 상단 하이라이트 (밝은 수평 선)
        hr,hg,hb = hc
        for px in range(fw):
            t2 = px/max(fw-1,1)
            a2 = round(190*(1-t2*0.4))
            d.point((x+px, y+1),  fill=(hr,hg,hb))
            d.point((x+px, y+2),  fill=(hr,hg,hb,a2//2))

        # ⑤ 하단 그림자 선
        for px in range(fw):
            d.point((x+px, y+h-1), fill=(r//3, g//3, b//3))

        # ⑥ 세그먼트 노치 (10% 간격)
        seg = max(1, w//10)
        for i in range(1,10):
            nx = x + seg*i
            if nx < x+fw:
                d.line([(nx,y+1),(nx,y+h-1)], fill=(0,0,0,130), width=1)

    # ⑦ 내부 테두리 마무리
    d.rectangle([x,y,x+w,y+h], outline=(55,48,72), width=1)

    # ⑧ 라벨 (좌측)
    if label:
        fl = _f(max(10, h-4), bold=True)
        lw = _tw(d, label, fl)
        d.text((x-lw-10, y+h//2-_th(d,"0",fl)//2), label,
               font=fl, fill=C.TXT_LBL)

    # ⑨ 수치 (우측)
    if show_val:
        fv  = _f(max(9, h-5))
        txt = f"{cur}/{mx}"
        d.text((x+w+8, y+h//2-_th(d,"0",fv)//2), txt,
               font=fv, fill=C.TXT_MID)


# ══════════════════════════════════════════════════════════════════
# 등급 배지 — 자간 균일 고정폭
# ══════════════════════════════════════════════════════════════════

def _grade_badge(img, d, x,y, grade) -> int:
    labels = {
        "Normal":"NORMAL","Rare":"RARE","Epic":"EPIC",
        "Legendary":"LEGENDARY","Fail":"FAIL"
    }
    txt = labels.get(grade, grade.upper())
    col = C.RARITY.get(grade,(155,155,155))
    gl  = C.RARITY_GL.get(grade,(50,50,50,35))
    f   = _f(15, bold=True)
    CW=12; PAD=10
    bx0=x; by0=y; bx1=x+len(txt)*CW+PAD*2; by1=y+26
    _glow(img,bx0-3,by0-3,bx1+3,by1+3, (*gl[:3],gl[3]), rad=6, blur=5)
    _rr(img,bx0,by0,bx1,by1, 4, fill=(*C.BG2,210), outline=col, lw=1)
    d  = ImageDraw.Draw(img)
    cx = bx0+PAD
    for ch in txt:
        cw  = _tw(d,ch,f); off=(CW-cw)//2
        d.text((cx+off,by0+5), ch, font=f, fill=col)
        cx += CW
    return bx1


# ══════════════════════════════════════════════════════════════════
# 초상화 플레이스홀더
# ══════════════════════════════════════════════════════════════════

def _ph_portrait(img, d, x0,y0,x1,y1):
    _rr(img,x0,y0,x1,y1, 8, fill=(*C.BG3,200))
    d  = ImageDraw.Draw(img)
    cx = (x0+x1)//2; cy=(y0+y1)//2
    r  = min((x1-x0),(y1-y0))//5
    d.ellipse([cx-r,cy-r*2,cx+r,cy-r//3],   fill=C.BG2, outline=C.GOLD_LO, width=1)
    d.ellipse([cx-r,cy-r//4,cx+r,cy+r+r//2], fill=C.BG2, outline=C.GOLD_LO, width=1)
    fp = _f(10)
    d.text((cx-_tw(d,"초상화 없음",fp)//2, cy+r+8), "초상화 없음", font=fp, fill=C.TXT_LO)


# ══════════════════════════════════════════════════════════════════
# 스탯 아이콘 플레이스홀더
# ══════════════════════════════════════════════════════════════════

def _paste_stat_icon(img, d, stat_key, x,y, size=24):
    """스탯 아이콘 붙여넣기. 없으면 다이아몬드 플레이스홀더"""
    ico = _load_stat_icon(stat_key, size)
    if ico:
        img.paste(ico,(x,y), ico)
        return True
    # 다이아몬드 플레이스홀더
    cx,cy = x+size//2, y+size//2; s=size//3
    d = ImageDraw.Draw(img)
    d.polygon([(cx,cy-s),(cx+s,cy),(cx,cy+s),(cx-s,cy)], fill=C.GOLD_MID)
    return False


# ══════════════════════════════════════════════════════════════════
# 렌더러 클래스
# ══════════════════════════════════════════════════════════════════

class BG3Renderer:

    # ─── 범용 카드 ───────────────────────────────────────────────
    def render_card(self, title, rows,
                    grade="Normal", subtitle=None,
                    system_key="system",
                    footer="✦ 비전 타운 ✦",
                    w=520, h=380) -> io.BytesIO:
        w = min(w, _MAX_IMG_DIM); h = min(h, _MAX_IMG_DIM)
        title = str(title)[:200]; subtitle = str(subtitle)[:200] if subtitle else None
        PAD = 24; HH = 66 if not subtitle else 88; FH = 46
        _lh_val = 22  # 값 텍스트 줄 높이
        fV = _f(19, True)
        mx_col = PAD + (w - PAD * 2) * 2 // 5 + 26
        val_maxw = w - PAD - mx_col - 8

        # 행별 실제 높이 계산 (텍스트 줄바꿈 고려)
        _tmp = Image.new("RGBA", (w, 1))
        _tmp_d = ImageDraw.Draw(_tmp)
        row_heights = []
        for row in rows:
            val = str(row.get("value", ""))
            line = ""; n = 0
            for ch in val:
                test = line + ch
                if _tw(_tmp_d, test, fV) > val_maxw and line:
                    n += 1; line = ch
                else:
                    line = test
            if line:
                n += 1
            row_heights.append(max(36, n * _lh_val + 14))

        min_h = HH + FH + 30 + sum(row_heights) + 10
        h = max(h, min_h)
        h = min(h, _MAX_IMG_DIM)

        img = _make_base(w,h, system_key, grade)
        d   = ImageDraw.Draw(img)
        rc  = C.RARITY.get(grade,(155,155,155))
        fT  = _f(28,True); fS=_f(16); fL=_f(17); fF=_f(14)

        # 헤더 패널
        hdr = Image.new("RGBA",(w,h),(0,0,0,0))
        _gv(hdr,0,0,w,HH, (*C.BG3,225),(0,0,0,0))
        img.alpha_composite(hdr); d=ImageDraw.Draw(img)

        _notxt(d,(PAD,13), title, fT, C.TXT_HI)
        if subtitle: _notxt(d,(PAD+1,50), subtitle, fS, C.TXT_LO)
        _grade_badge(img,d, w-165,12, grade)
        _orn(img,d, PAD,HH, w-PAD, color=rc)

        # 콘텐츠 패널
        CT=HH+12; CB=h-FH-6
        _rr(img,PAD,CT,w-PAD,CB, 8, fill=(*C.BG2,115))
        d=ImageDraw.Draw(img)
        cy=CT+12

        for i, (row, rh) in enumerate(zip(rows, row_heights)):
            lbl = row.get("label",""); val=str(row.get("value",""))
            col = row.get("color", C.TXT_HI)
            if i>0: d.line([(PAD+18,cy-5),(w-PAD-18,cy-5)], fill=C.SEP, width=1)
            _notxt(d,(PAD+18,cy), lbl+":", fL, C.TXT_LBL)
            _wrap(d, val, fV, mx_col, cy, val_maxw, col, lh=_lh_val)
            cy+=rh

        sy=h-FH; _orn(img,d,PAD,sy,w-PAD, color=C.GOLD_LO)
        fw=_tw(d,footer,fF); fh=_th(d,footer,fF)
        _notxt(d,(w//2-fw//2, sy+(FH-fh)//2), footer, fF, C.TXT_LO)
        _gold_frame(img); return _to_buf(img)

    # ─── 상태창 ──────────────────────────────────────────────────
    def render_status_card(self,
                           name, level, title_str,
                           hp, max_hp, mp, max_mp, en, max_en,
                           gold, exp, exp_needed,
                           stats: dict,
                           inv_used, inv_max) -> io.BytesIO:
        W = 520
        PAD = 22; HH = 78

        # ── 폰트 (모바일 가독성 우선 — 큰 사이즈) ────────────
        fN  = _f(34, True)   # 이름
        fT  = _f(20)         # 칭호
        fLb = _f(18, True)   # HP/MP/EN 라벨
        fBv = _f(18)         # 바 수치
        fSec= _f(18, True)   # 섹션 헤더
        fSt = _f(20)         # 스탯 이름
        fV  = _f(22, True)   # 스탯 값
        fFt = _f(20, True)   # 하단

        # ── 높이 계산 (세로 배치) ─────────────────────────────
        # 헤더(78) + 바간격(18) + 바3줄(126) + 구분(16) + EXP(42)
        # + 구분+헤더(42) + 스탯5줄(180) + 하단(66)
        H = HH + 18 + 126 + 16 + 42 + 42 + 180 + 66
        img = _make_base(W, H, "status")
        d   = ImageDraw.Draw(img)

        # ── 헤더 ──────────────────────────────────────────────
        hdr = Image.new("RGBA", (W, H), (0,0,0,0))
        _gv(hdr, 0, 0, W, HH, (*C.BG3, 230), (0,0,0,0))
        img.alpha_composite(hdr); d = ImageDraw.Draw(img)
        _notxt(d, (PAD, 10), f"Lv.{level}  {name}", fN, C.TXT_HI)
        if title_str and str(title_str) != "None":
            _notxt(d, (PAD+2, 42), f"✦ {title_str}", fT, C.GOLD_MID)
        _orn(img, d, PAD, HH, W-PAD)

        # ── 게이지 바 (전체 폭 사용) ─────────────────────────
        BW = W - PAD*2 - 62; BH = 24; BX = PAD + 56; LX = PAD + 4
        bars = [("HP", hp, max_hp, C.HP), ("MP", mp, max_mp, C.MP), ("EN", en, max_en, C.EN)]
        by = HH + 18
        for lbl, cur, mx2, cols in bars:
            _notxt(d, (LX, by+3), lbl, fLb, C.TXT_LBL)
            _bar_A(img, d, BX, by, BW, BH, cur, mx2, cols, show_val=False)
            d = ImageDraw.Draw(img)
            # 수치를 바 안쪽 오른편에 표시
            vtxt = f"{cur}/{mx2}"
            vw = _tw(d, vtxt, fBv)
            _notxt(d, (BX + BW - vw - 6, by+3), vtxt, fBv, C.TXT_HI)
            by += 42

        # EXP 바
        _orn(img, d, PAD, by+2, W-PAD, color=C.GOLD_LO); by += 16
        _notxt(d, (LX, by+3), "EXP", fLb, C.TXT_LBL)
        _bar_A(img, d, BX, by, BW, BH, int(exp), exp_needed, C.EXP, show_val=False)
        d = ImageDraw.Draw(img)
        vtxt = f"{int(exp)}/{exp_needed}"
        vw = _tw(d, vtxt, fBv)
        _notxt(d, (BX + BW - vw - 6, by+3), vtxt, fBv, C.TXT_HI)
        by += 42

        # ── 구분선 + 스탯 (바 아래에 배치) ────────────────────
        _orn(img, d, PAD, by, W-PAD)
        by += 12
        _notxt(d, (PAD+8, by), "[ 기본 스탯 ]", fSec, C.GOLD_MID)
        by += 30

        STAT_DATA = [
            ("str",  "힘",   stats.get("str", 0)),
            ("dex",  "민첩", stats.get("dex", 0)),
            ("int",  "지력", stats.get("int", 0)),
            ("will", "의지", stats.get("will", 0)),
            ("luck", "운",   stats.get("luck", 0)),
        ]
        IS = 26  # 아이콘 크기
        for sk, sname, val in STAT_DATA:
            _paste_stat_icon(img, d, sk, PAD+8, by, IS)
            d = ImageDraw.Draw(img)
            text_y = by + (IS - _th(d, "가", fSt)) // 2
            _notxt(d, (PAD+8+IS+12, text_y), sname, fSt, C.TXT_LBL)
            vt = str(val); vw = _tw(d, vt, fV)
            _notxt(d, (W-PAD-vw-8, text_y), vt, fV, C.TXT_HI)
            # 점선 리더
            leader_y = text_y + _th(d, "가", fSt) // 2
            lx2 = PAD+8+IS+12+_tw(d, sname, fSt)+8
            rx2 = W-PAD-vw-16
            if rx2 > lx2:
                for dx in range(lx2, rx2, 7):
                    d.point((dx, leader_y), fill=C.SEP)
            by += 36

        # ── 하단 골드/인벤 ────────────────────────────────────
        _orn(img, d, PAD, H-60, W-PAD)
        _notxt(d, (PAD+12, H-46), f"◆ {gold:,} G", fFt, C.GOLD_HI)
        it = f"{inv_used} / {inv_max} 슬롯"
        iw = _tw(d, it, fFt)
        _notxt(d, (W-PAD-iw-12, H-46), it, fFt, C.TXT_MID)
        _orn(img, d, PAD, H-16, W-PAD, color=C.GOLD_LO)

        _gold_frame(img); return _to_buf(img)

    # ─── 장비창 ────────────────────────────────────────────────
    def render_equipment_card(self, name, slots, attack, defense,
                               magic_attack=0) -> io.BytesIO:
        """
        장비창 카드 렌더링.
        slots: [{"slot_name": str, "item_name": str|None, "grade": str, "stats_text": str}, ...]
        """
        W, H = 600, 480
        img = _make_base(W, H, "equipment")
        d   = ImageDraw.Draw(img)
        fN  = _f(28, True); fSec = _f(17, True)
        fL  = _f(17); fV = _f(19, True); fF = _f(14)
        PAD = 24; HH = 68

        # 헤더
        hdr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        _gv(hdr, 0, 0, W, HH, (*C.BG3, 225), (0, 0, 0, 0))
        img.alpha_composite(hdr); d = ImageDraw.Draw(img)
        _notxt(d, (PAD, 15), f"⚔ {name}의 장비창", fN, C.TXT_HI)
        _orn(img, d, PAD, HH, W - PAD)

        # 콘텐츠 영역
        FH = 46; CT = HH + 12; CB = H - FH - 6
        _rr(img, PAD, CT, W - PAD, CB, 8, fill=(*C.BG2, 115))
        d = ImageDraw.Draw(img)

        cy = CT + 14
        mx_col = PAD + 120

        for slot in slots:
            sname = slot.get("slot_name", "")
            iname = slot.get("item_name")
            grade = slot.get("grade", "Normal")
            stats = slot.get("stats_text", "")

            if cy > CT + 14:
                d.line([(PAD + 18, cy - 5), (W - PAD - 18, cy - 5)],
                       fill=C.SEP, width=1)

            _notxt(d, (PAD + 18, cy), f"[{sname}]", fL, C.GOLD_MID)

            if iname:
                col = C.RARITY.get(grade, (155, 155, 155))
                display = iname
                if stats:
                    display += f"  {stats}"
                _notxt(d, (mx_col, cy), display, fV, col)
            else:
                _notxt(d, (mx_col, cy), "— 비어있음 —", fV, C.TXT_LO)
            cy += 38

        # 전투 스탯 구분선
        cy += 10
        _orn(img, d, PAD + 18, cy, W - PAD - 18, color=C.GOLD_LO)
        cy += 16
        _notxt(d, (PAD + 18, cy), "[ 전투 스탯 ]", fSec, C.GOLD_MID)
        cy += 30
        _notxt(d, (PAD + 18, cy), "공격력:", fL, C.TXT_LBL)
        _notxt(d, (mx_col, cy), str(attack), fV, C.TXT_HI)
        cy += 30
        _notxt(d, (PAD + 18, cy), "방어력:", fL, C.TXT_LBL)
        _notxt(d, (mx_col, cy), str(defense), fV, C.TXT_HI)
        if magic_attack:
            cy += 30
            _notxt(d, (PAD + 18, cy), "마공력:", fL, C.TXT_LBL)
            _notxt(d, (mx_col, cy), str(magic_attack), fV, C.TXT_HI)

        # 푸터
        footer = "✦ 장비 정보 ✦"
        sy = H - FH
        _orn(img, d, PAD, sy, W - PAD, color=C.GOLD_LO)
        fw = _tw(d, footer, fF); fh = _th(d, footer, fF)
        _notxt(d, (W // 2 - fw // 2, sy + (FH - fh) // 2), footer, fF, C.TXT_LO)

        _gold_frame(img); return _to_buf(img)

    # ─── NPC 대화 ────────────────────────────────────────────────
    def render_npc_dialogue(self,
                            npc_name, npc_role, greeting,
                            affinity_pts, affinity_level,
                            portrait_type="npc",
                            portrait_id=None) -> io.BytesIO:
        """
        portrait_type: 'npc' | 'animal' | 'monster'
        portrait_id:   파일명 (확장자 제외). None이면 플레이스홀더
        """
        W=560; MIN_H=290
        PW=200; fN=_f(24,True); fR=_f(16); fD=_f(17); fA=_f(16); fP=_f(14)
        TX=PW+14; ty=18; LH=26

        # ── 동적 높이 계산 ──────────────────────────────────────
        _tmp_img = Image.new("RGBA", (W, 1), (0,0,0,0))
        _tmp_d   = ImageDraw.Draw(_tmp_img)
        name_h   = _th(_tmp_d, npc_name, fN)
        role_h   = _th(_tmp_d, f"[ {npc_role} ]", fR)
        orn_y    = ty + name_h + role_h + 14
        greeting_text = f'"{greeting}"'
        maxw = W - TX - 24
        text_start_y = orn_y + 12
        text_end_y   = _wrap(_tmp_d, greeting_text, fD, TX, text_start_y, maxw, (0,0,0,0), lh=LH)
        # 헤더 + 대사 줄들 + 여백(14) + 호감도 바 영역(58)
        H = max(MIN_H, text_end_y + 14 + 58)

        img = _make_base(W,H,"npc")
        d   = ImageDraw.Draw(img)
        PX0,PY0=14,14; PX1,PY1=PW-4,H-14
        pw2=PX1-PX0-2; ph2=PY1-PY0-2

        # 초상화
        _rr(img,PX0,PY0,PX1,PY1,8, fill=(*C.BG3,200))
        port = (_load_portrait(portrait_type, portrait_id, pw2, ph2)
                if portrait_id else None)
        if port:
            mk = Image.new("L",(pw2,ph2),0)
            ImageDraw.Draw(mk).rounded_rectangle([0,0,pw2-1,ph2-1],radius=6,fill=255)
            img.paste(port,(PX0+1,PY0+1), mk)
        else:
            _ph_portrait(img,d, PX0,PY0,PX1,PY1)

        d=ImageDraw.Draw(img)
        d.rounded_rectangle([PX0,PY0,PX1,PY1], radius=8, outline=C.GOLD_MID, width=2)

        # 대화창
        _notxt(d,(TX,ty), npc_name, fN, C.GOLD_HI)
        _notxt(d,(TX, ty+name_h+6), f"[ {npc_role} ]", fR, C.TXT_LO)
        _orn(img,d,TX, orn_y, W-18, color=C.GOLD_LO)
        _wrap(d, greeting_text, fD, TX, orn_y+12, maxw, C.TXT_HI, lh=LH)

        # 호감도 바 (시안 A)
        AY=H-58; _orn(img,d,TX,AY,W-18, color=(*C.TEAL_LO,180))
        d=ImageDraw.Draw(img)
        aff_y = AY+10
        _notxt(d,(TX,aff_y), affinity_level, fA, C.TEAL_HI)
        aw=_tw(d,affinity_level,fA)
        _bar_A(img,d, TX+aw+12, aff_y, W-TX-aw-72, 18,
               min(affinity_pts,100), 100,
               (C.TEAL_LO, C.TEAL_HI), show_val=False)
        d=ImageDraw.Draw(img)
        pt2=f"{affinity_pts}pt"; pw3=_tw(d,pt2,fP)
        _notxt(d,(W-pw3-18, aff_y+2), pt2, fP, C.TXT_LO)

        _gold_frame(img); return _to_buf(img)

    # ─── 전투 카드 ───────────────────────────────────────────────
    def render_battle_card(self,
                           monster_name, monster_level,
                           monster_hp, monster_max_hp,
                           danger, turn,
                           player_hp, player_max_hp,
                           player_mp, player_max_mp,
                           last_action="", last_dmg=0,
                           is_crit=False, size_label="") -> io.BytesIO:
        W,H=540,360
        img=_make_base(W,H,"battle"); d=ImageDraw.Draw(img)
        fB=_f(26,True); fM=_f(18,True); fS=_f(16); fL=_f(14); PAD=22

        _notxt(d,(PAD,14), monster_name, fB, C.TXT_HI)
        _notxt(d,(PAD+2,50), f"Lv.{monster_level}   {size_label}", fS, C.TXT_LO)

        DCOL={"위험당함":(220,55,45),"보통":(230,180,30),"안전":(50,195,100)}
        dc=DCOL.get(danger,(155,155,155)); dt=f"  {danger}  "
        dw=_tw(d,dt,fS)
        _rr(img,W-dw-PAD-6,12,W-PAD+2,40,5, fill=(*dc,38),outline=dc,lw=1)
        d=ImageDraw.Draw(img); d.text((W-dw-PAD,16),dt, font=fS, fill=dc)

        rc=C.SYS["battle"]; _orn(img,d,PAD,68,W-PAD,color=rc)

        # 몬스터 HP (시안 A, 크게)
        _notxt(d,(PAD,80),"몬스터 HP",fL,C.TXT_LBL)
        _bar_A(img,d, PAD+98,78, W-PAD*2-98,28, monster_hp,monster_max_hp, C.HP)
        d=ImageDraw.Draw(img); _orn(img,d,PAD,122,W-PAD,color=(68,22,28))

        # 플레이어 HP/MP
        _notxt(d,(PAD,134),"내 HP",fL,C.TXT_LBL)
        _bar_A(img,d,PAD+76,132, 240,22, player_hp,player_max_hp, C.HP)
        d=ImageDraw.Draw(img)
        _notxt(d,(PAD,164),"내 MP",fL,C.TXT_LBL)
        _bar_A(img,d,PAD+76,162, 240,22, player_mp,player_max_mp, C.MP)
        d=ImageDraw.Draw(img); _orn(img,d,PAD,200,W-PAD,color=(68,22,28))

        # 마지막 액션
        if last_action:
            col=C.GOLD_HI if is_crit else C.TXT_HI
            pre="[크리티컬]  " if is_crit else ""
            _notxt(d,(PAD,212),f"{pre}{last_action}  /  {last_dmg} 피해",fM,col)
        tt=f"턴  {turn}"; tw2=_tw(d,tt,fS)
        _notxt(d,(W-tw2-PAD,212),tt, fS, C.TXT_LO)

        _orn(img,d,PAD,H-56,W-PAD,color=rc)
        g="/공격 [스킬명]   /도주"; gw=_tw(d,g,fL)
        d.text((W//2-gw//2,H-42),g, font=fL, fill=C.TXT_LO)

        _gold_frame(img); return _to_buf(img)

    # ─── 장소 배너 ───────────────────────────────────────────────
    def render_location_banner(self,
                                location_name: str,
                                description: str,
                                zone_type: str = "town",
                                zone_id: str = None) -> io.BytesIO:
        """
        zone_type: 'town' | 'hunting' | 'gathering' | 'fishing'
        zone_id:   파일명 (확장자 제외, 예: '비전타운', '고블린동굴')
                   None이면 플레이스홀더 표시
        """
        W=540; SH=180
        fLoc=_f(34,True); fDesc=_f(17); fSub=_f(14)
        LH=24  # 설명 텍스트 줄 간격

        # ── 텍스트 패널 높이 동적 계산 ──────────────────────────
        # 임시 이미지에서 줄바꿈 결과를 미리 계산하여 TH 결정
        _tmp_img = Image.new("RGBA", (W, 1), (0,0,0,0))
        _tmp_d   = ImageDraw.Draw(_tmp_img)
        desc_text = description or ""
        # 줄 수 계산
        line_count = 0
        line = ""
        for ch in desc_text:
            test = line + ch
            if _tw(_tmp_d, test, fDesc) > W - 56 and line:
                line_count += 1
                line = ch
            else:
                line = test
        if line:
            line_count += 1
        # 장소명(44) + 밑줄(6) + 설명 줄들 + 하단 여백(44)
        TH = max(130, 44 + 6 + line_count * LH + 44)
        H = SH + TH

        img=Image.new("RGBA",(W,H),(0,0,0,0))

        # ── 상단 씬 이미지 슬롯 ─────────────────────────────
        scene = (_load_banner(zone_type, zone_id, W, SH)
                 if zone_id else None)

        if scene:
            # 하단 페이드 아웃
            fd=Image.new("RGBA",(W,SH),(0,0,0,0))
            _gv(fd,0,SH*3//5,W,SH, (0,0,0,0),(0,0,0,210))
            scene.alpha_composite(fd)
            img.paste(scene,(0,0))
        else:
            # 플레이스홀더 (그라디언트 + 안내 텍스트)
            _gv(img,0,0,W,SH, C.BG2,C.BG0)
            d2=ImageDraw.Draw(img)
            d2.rounded_rectangle([16,16,W-17,SH-16], radius=8,
                                  outline=(*C.GOLD_LO,100), width=1)
            fph=_f(17)
            ph_type = {"town":"마을","hunting":"사냥터",
                       "gathering":"채집터","fishing":"낚시터"}.get(zone_type,"")
            ph=f"[ {ph_type} 씬 이미지 슬롯 ]"
            pw=_tw(d2,ph,fph)
            d2.text((W//2-pw//2,SH//2-11),ph, font=fph, fill=C.TXT_LO)

        # 씬 슬롯 테두리 표시
        d=ImageDraw.Draw(img)
        d.rounded_rectangle([14,14,W-15,SH-14], radius=8,
                             outline=(*C.GOLD_LO,80), width=1)

        # ── 하단 텍스트 패널 ────────────────────────────────
        tp=Image.new("RGBA",(W,H),(0,0,0,0))
        _gv(tp,0,SH,W,H, (*C.BG1,245),(*C.BG0,255))
        img.alpha_composite(tp); d=ImageDraw.Draw(img)

        TY=SH+16
        # 금장 세로선
        d.line([(24,TY+2),(24,H-18)], fill=C.GOLD_MID,  width=3)
        d.line([(25,TY+2),(25,H-18)], fill=(*C.GOLD_HI,65), width=1)

        _notxt(d,(42,TY), location_name, fLoc, C.GOLD_HI)
        lw=_tw(d,location_name,fLoc)
        d.line([(42,TY+48),(42+lw,TY+48)], fill=C.GOLD_MID, width=1)
        _wrap(d, desc_text, fDesc, 42, TY+58, W-60, C.TXT_MID, lh=LH)

        sub="✦ 비전 타운   언더다크"; sw=_tw(d,sub,fSub)
        d.text((W-sw-20,H-26),sub, font=fSub, fill=C.TXT_LO)

        # 전체 마스크
        mk=Image.new("L",(W,H),0)
        ImageDraw.Draw(mk).rounded_rectangle([0,0,W-1,H-1],radius=16,fill=255)
        r=Image.new("RGBA",(W,H),(0,0,0,0)); r.paste(img,mask=mk); img=r

        _gold_frame(img); return _to_buf(img)

    # ─── 범용 결과 카드 ────────────────────────────────────────────
    def render_result_card(self, title, subtitle=None, rows=None,
                           system_key="system", grade="Normal",
                           footer="✦ 비전 타운 ✦") -> io.BytesIO:
        """낚시/요리/제련/채집/전투결과 등 범용 결과 카드"""
        rows = rows or []
        return self.render_card(title, rows, grade=grade, subtitle=subtitle,
                                system_key=system_key, footer=footer)

    # ─── 전투 결과 카드 ────────────────────────────────────────────
    def render_battle_result(self, title, is_victory=True,
                             rewards_rows=None, level_up_info=None) -> io.BytesIO:
        """전투 승리/패배 결과"""
        rows = rewards_rows or []
        if level_up_info:
            rows.append({"label": "레벨 업!", "value": level_up_info, "color": C.GOLD_HI})
        grade = "Legendary" if is_victory else "Fail"
        sys_key = "battle"
        footer = "전투 승리!" if is_victory else "전투 패배..."
        return self.render_card(title, rows, grade=grade, subtitle=None,
                                system_key=sys_key, footer=footer)

    # ─── 퀘스트 카드 ──────────────────────────────────────────────
    def render_quest_card(self, quest_name, npc_name="", quest_type="",
                          difficulty="", description="",
                          progress_cur=0, progress_max=0,
                          rewards=None) -> io.BytesIO:
        """퀘스트 정보 카드"""
        rows = []
        if npc_name:
            rows.append({"label": "NPC", "value": npc_name})
        if quest_type:
            rows.append({"label": "유형", "value": quest_type})
        if difficulty:
            rows.append({"label": "난이도", "value": difficulty})
        if description:
            rows.append({"label": "내용", "value": description[:60]})
        if progress_max > 0:
            rows.append({"label": "진행", "value": f"{progress_cur}/{progress_max}"})
        if rewards:
            rw_parts = []
            if rewards.get("gold"): rw_parts.append(f"{rewards['gold']}G")
            if rewards.get("exp"):  rw_parts.append(f"{rewards['exp']}EXP")
            if rewards.get("item"): rw_parts.append(rewards["item"])
            if rw_parts:
                rows.append({"label": "보상", "value": " / ".join(rw_parts)})
        return self.render_card(quest_name, rows, grade="Normal",
                                system_key="quest", footer="퀘스트")

    # ─── 상점 카드 ────────────────────────────────────────────────
    def render_shop_card(self, shop_name, npc_name="",
                         items=None) -> io.BytesIO:
        """상점 목록 카드"""
        rows = []
        if npc_name:
            rows.append({"label": "상인", "value": npc_name})
        for it in (items or [])[:8]:
            name = it.get("name", "?")
            price = it.get("price", 0)
            rows.append({"label": name, "value": f"{price:,}G"})
        return self.render_card(shop_name, rows, grade="Normal",
                                system_key="shop", footer="상점")

    # ─── 제작 결과 카드 ──────────────────────────────────────────
    def render_craft_result(self, recipe_name, result_item_name,
                            result_grade="Normal", ingredients=None,
                            exp_gained=0, rank_up_msg="",
                            system_key="craft",
                            footer="제작 완료") -> io.BytesIO:
        """제작/제련/요리/연금 결과 카드"""
        rows = [
            {"label": "결과물", "value": result_item_name,
             "color": C.RARITY.get(result_grade, C.TXT_HI)},
        ]
        if ingredients:
            for ing_name, cnt in ingredients:
                rows.append({"label": "소모", "value": f"{ing_name} x{cnt}",
                             "color": C.TXT_MID})
        if exp_gained:
            rows.append({"label": "숙련도", "value": f"+{exp_gained}",
                         "color": C.GOLD_HI})
        if rank_up_msg:
            rows.append({"label": "랭크 업!", "value": rank_up_msg,
                         "color": C.GOLD_HI})
        return self.render_card(recipe_name, rows, grade=result_grade,
                                system_key=system_key, footer=footer)

    # ─── 제작 실패 카드 ──────────────────────────────────────────
    def render_craft_fail(self, recipe_name, reason,
                          exp_gained=0, rank_up_msg="",
                          system_key="craft",
                          footer="제작 실패") -> io.BytesIO:
        """제작/제련/요리/연금 실패 카드"""
        rows = [
            {"label": "실패 사유", "value": reason, "color": C.RARITY["Fail"]},
        ]
        if exp_gained:
            rows.append({"label": "숙련도", "value": f"+{exp_gained}",
                         "color": C.GOLD_HI})
        if rank_up_msg:
            rows.append({"label": "랭크 업!", "value": rank_up_msg,
                         "color": C.GOLD_HI})
        return self.render_card(recipe_name, rows, grade="Fail",
                                system_key=system_key, footer=footer)

    # ─── 제작 레시피 목록 카드 ───────────────────────────────────
    def render_recipe_list(self, skill_name, rank, recipes_info,
                           system_key="craft") -> io.BytesIO:
        """레시피 목록 카드 (skill_name: 스킬명, recipes_info: [(name, rank_req, unlocked), ...])"""
        rows = []
        for name, rank_req, unlocked in recipes_info[:12]:
            status = "O" if unlocked else "X"
            col = C.TXT_HI if unlocked else C.TXT_LO
            rows.append({"label": f"[{status}] [{rank_req}]",
                         "value": name, "color": col})
        return self.render_card(
            f"{skill_name} 레시피", rows, grade="Normal",
            subtitle=f"현재 랭크: {rank}",
            system_key=system_key,
            footer=f"{skill_name} 레시피 목록")


# ══════════════════════════════════════════════════════════════════
# 싱글톤 (스레드 안전)
# ══════════════════════════════════════════════════════════════════
_renderer: Optional[BG3Renderer] = None
_renderer_lock = threading.Lock()

def get_renderer() -> BG3Renderer:
    global _renderer
    if _renderer is None:
        with _renderer_lock:
            if _renderer is None:
                _renderer = BG3Renderer()
    return _renderer


# ══════════════════════════════════════════════════════════════════
# 비동기 래퍼 (이벤트 루프 블로킹 방지)
# ══════════════════════════════════════════════════════════════════
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="bg3_render")

async def render_async(func, *args, **kwargs) -> io.BytesIO:
    """
    PIL 렌더링을 ThreadPoolExecutor에서 실행하여
    Discord 봇의 asyncio 이벤트 루프를 블로킹하지 않는다.

    사용 예:
        from bg3_renderer import get_renderer, render_async
        r = get_renderer()
        buf = await render_async(r.render_card, title="...", rows=[...])
        await ctx.send(file=discord.File(fp=buf, filename="card.png"))
    """
    import asyncio
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, lambda: func(*args, **kwargs))
