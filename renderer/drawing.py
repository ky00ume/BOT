"""renderer/drawing.py — 저수준 드로잉 유틸"""
import io

try:
    from PIL import Image, ImageDraw, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from renderer.palette import C
from renderer.fonts import _f, _tw, _th
from renderer.assets import _load_stat_icon

_MAX_IMG_DIM = 4096


def _gv(img, x0, y0, x1, y1, ct, cb, at=255, ab=255):
    """수직 그라디언트"""
    d = ImageDraw.Draw(img); h = y1 - y0
    if h <= 0: return
    r0, g0, b0 = ct[:3]; r1, g1, b1 = cb[:3]
    for dy in range(h):
        t = dy / max(h - 1, 1)
        r = round(r0 + (r1 - r0) * t); g = round(g0 + (g1 - g0) * t); b = round(b0 + (b1 - b0) * t)
        a = round(at + (ab - at) * t)
        d.line([(x0, y0 + dy), (x1, y0 + dy)], fill=(r, g, b, a))


def _rr(img, x0, y0, x1, y1, rad, fill=None, outline=None, lw=1):
    """RGBA 둥근 사각형"""
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d  = ImageDraw.Draw(ov)
    if fill:    d.rounded_rectangle([x0, y0, x1, y1], radius=rad, fill=fill)
    if outline: d.rounded_rectangle([x0, y0, x1, y1], radius=rad, outline=outline, width=lw)
    img.alpha_composite(ov)


def _glow(img, x0, y0, x1, y1, color, rad=0, blur=8):
    """글로우"""
    g = Image.new("RGBA", img.size, (0, 0, 0, 0))
    r, gc, b = color[:3]; a = color[3] if len(color) > 3 else 70
    if rad == 0:
        ImageDraw.Draw(g).rectangle([x0, y0, x1, y1], fill=(r, gc, b, a))
    else:
        ImageDraw.Draw(g).rounded_rectangle([x0, y0, x1, y1], radius=rad, fill=(r, gc, b, a))
    g = g.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(g)


def _gold_frame(img, radius=16):
    """BG3 금장 3중 테두리 + 코너 다이아몬드"""
    w, h = img.size; d = ImageDraw.Draw(img)
    _glow(img, 2, 2, w - 3, h - 3, C.GOLD_GL, rad=radius + 2, blur=6)
    d.rounded_rectangle([1, 1, w - 2, h - 2], radius=radius, outline=C.GOLD_HI, width=2)
    d.rounded_rectangle([5, 5, w - 6, h - 6], radius=max(radius - 4, 4), outline=C.GOLD_LO, width=1)
    S = 9
    for cx, cy in [(2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)]:
        d.polygon([(cx, cy - S), (cx + S, cy), (cx, cy + S), (cx - S, cy)], fill=C.GOLD_HI)
        s2 = S // 2
        d.polygon([(cx, cy - s2), (cx + s2, cy), (cx, cy + s2), (cx - s2, cy)], fill=C.BG0)


def _orn(img, d, x0, y, x1, color=None, thick=1):
    """장식 구분선"""
    col = color or C.GOLD_MID
    d.line([(x0 + 12, y), (x1 - 12, y)], fill=col, width=thick)
    for cx in [x0 + 7, x1 - 7]:
        d.polygon([(cx, y - 4), (cx + 4, y), (cx, y + 4), (cx - 4, y)], fill=col)


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


def _wrap(d, text, font, x: int, y: int, maxw, fill, lh=21) -> int:
    """자동 줄바꿈, 마지막 y 반환"""
    line = ""; cy: int = y
    for ch in text:
        test = line + ch
        if _tw(d, test, font) > maxw and line:
            _notxt(d, (x, cy), line, font, fill); cy += lh; line = ch
        else:
            line = test
    if line: _notxt(d, (x, cy), line, font, fill); cy += lh
    return cy


def _make_base(w, h, sys_key="system", grade="Normal") -> "Image.Image":
    """카드 베이스 배경 생성"""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    _gv(img, 0, 0, w, h, C.BG1, C.BG0)
    sc = C.SYS.get(sys_key, C.SYS["system"])
    _glow(img, 0, h // 2, w, h, sc, rad=0, blur=45)
    rc = C.RARITY.get(grade, (60, 60, 60))
    _glow(img, 0, 0, w, h // 3, rc, rad=0, blur=30)
    # 미묘한 대각선 광택
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0)); dp = ImageDraw.Draw(ov)
    for i in range(0, w + h, 60):
        dp.line([(i, 0), (0, i)], fill=(255, 255, 255, 4), width=1)
    img.alpha_composite(ov)
    # 둥근 마스크
    mk = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mk).rounded_rectangle([0, 0, w - 1, h - 1], radius=16, fill=255)
    r = Image.new("RGBA", (w, h), (0, 0, 0, 0)); r.paste(img, mask=mk)
    return r


def _to_buf(img) -> io.BytesIO:
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    buf.seek(0); return buf


# ══════════════════════════════════════════════════════════════════
# ★ 게이지 바 — 시안 A (세그먼트 노치, 최종 확정)
# ══════════════════════════════════════════════════════════════════

def _bar_A(img, d, x, y, w, h, cur, mx, colors, label="", show_val=True):
    """
    BG3 스타일 세그먼트 바 (시안 A 확정)
    - 좌→우 밝아지는 그라디언트
    - 10% 간격 수직 노치
    - 상단 하이라이트 + 하단 그림자
    - 이중 금색 외부 프레임
    """
    ratio = max(0.0, min(1.0, cur / max(mx, 1)))
    bc, hc = colors
    r, g, b  = bc
    fw       = int(w * ratio)

    # ① 이중 외부 프레임
    d.rectangle([x - 2, y - 2, x + w + 2, y + h + 2], outline=(140, 110, 45), width=1)
    d.rectangle([x - 1, y - 1, x + w + 1, y + h + 1], outline=(80, 60, 20),   width=1)

    # ② 배경 홈
    d.rectangle([x, y, x + w, y + h], fill=C.BAR_BG)

    # ③ 채움 그라디언트 (좌→우)
    if fw > 0:
        for px in range(fw):
            t  = px / max(fw - 1, 1)
            cr = round(r * 0.65 + r * 0.35 * t)
            cg = round(g * 0.65 + g * 0.35 * t)
            cb2 = round(b * 0.65 + b * 0.35 * t)
            d.line([(x + px, y + 1), (x + px, y + h - 1)], fill=(cr, cg, cb2))

        # ④ 상단 하이라이트 (밝은 수평 선)
        hr, hg, hb = hc
        for px in range(fw):
            t2 = px / max(fw - 1, 1)
            a2 = round(190 * (1 - t2 * 0.4))
            d.point((x + px, y + 1),  fill=(hr, hg, hb))
            d.point((x + px, y + 2),  fill=(hr, hg, hb, a2 // 2))

        # ⑤ 하단 그림자 선
        for px in range(fw):
            d.point((x + px, y + h - 1), fill=(r // 3, g // 3, b // 3))

        # ⑥ 세그먼트 노치 (10% 간격)
        seg = max(1, w // 10)
        for i in range(1, 10):
            nx = x + seg * i
            if nx < x + fw:
                d.line([(nx, y + 1), (nx, y + h - 1)], fill=(0, 0, 0, 130), width=1)

    # ⑦ 내부 테두리 마무리
    d.rectangle([x, y, x + w, y + h], outline=(55, 48, 72), width=1)

    # ⑧ 라벨 (좌측)
    if label:
        fl = _f(max(10, h - 4), bold=True)
        lw = _tw(d, label, fl)
        d.text((x - lw - 10, y + h // 2 - _th(d, "0", fl) // 2), label,
               font=fl, fill=C.TXT_LBL)

    # ⑨ 수치 (우측)
    if show_val:
        fv  = _f(max(9, h - 5))
        txt = f"{cur}/{mx}"
        d.text((x + w + 8, y + h // 2 - _th(d, "0", fv) // 2), txt,
               font=fv, fill=C.TXT_MID)


# ══════════════════════════════════════════════════════════════════
# 등급 배지 — 자간 균일 고정폭
# ══════════════════════════════════════════════════════════════════

def _grade_badge(img, d, x: int, y: int, grade) -> int:
    labels = {
        "Normal": "NORMAL", "Rare": "RARE", "Epic": "EPIC",
        "Legendary": "LEGENDARY", "Fail": "FAIL"
    }
    txt = labels.get(grade, grade.upper())
    col = C.RARITY.get(grade, (155, 155, 155))
    gl  = C.RARITY_GL.get(grade, (50, 50, 50, 35))
    f   = _f(15, bold=True)
    CW = 12; PAD = 10
    bx0 = x; by0 = y; bx1: int = x + len(txt) * CW + PAD * 2; by1 = y + 26
    _glow(img, bx0 - 3, by0 - 3, bx1 + 3, by1 + 3, (*gl[:3], gl[3]), rad=6, blur=5)
    _rr(img, bx0, by0, bx1, by1, 4, fill=(*C.BG2, 210), outline=col, lw=1)
    d  = ImageDraw.Draw(img)
    cx = bx0 + PAD
    for ch in txt:
        cw  = _tw(d, ch, f); off = (CW - cw) // 2
        d.text((cx + off, by0 + 5), ch, font=f, fill=col)
        cx += CW
    return bx1


# ══════════════════════════════════════════════════════════════════
# 초상화 플레이스홀더
# ══════════════════════════════════════════════════════════════════

def _ph_portrait(img, d, x0, y0, x1, y1):
    _rr(img, x0, y0, x1, y1, 8, fill=(*C.BG3, 200))
    d  = ImageDraw.Draw(img)
    cx = (x0 + x1) // 2; cy = (y0 + y1) // 2
    r  = min((x1 - x0), (y1 - y0)) // 5
    d.ellipse([cx - r, cy - r * 2, cx + r, cy - r // 3],   fill=C.BG2, outline=C.GOLD_LO, width=1)
    d.ellipse([cx - r, cy - r // 4, cx + r, cy + r + r // 2], fill=C.BG2, outline=C.GOLD_LO, width=1)
    fp = _f(10)
    d.text((cx - _tw(d, "초상화 없음", fp) // 2, cy + r + 8), "초상화 없음", font=fp, fill=C.TXT_LO)


# ══════════════════════════════════════════════════════════════════
# 스탯 아이콘 플레이스홀더
# ══════════════════════════════════════════════════════════════════

def _paste_stat_icon(img, d, stat_key, x, y, size=24):
    """스탯 아이콘 붙여넣기. 없으면 다이아몬드 플레이스홀더"""
    ico = _load_stat_icon(stat_key, size)
    if ico:
        img.paste(ico, (x, y), ico)
        return True
    # 다이아몬드 플레이스홀더
    cx, cy = x + size // 2, y + size // 2; s = size // 3
    d = ImageDraw.Draw(img)
    d.polygon([(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)], fill=C.GOLD_MID)
    return False
