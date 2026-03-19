"""fishing_card.py — PIL 통일 카드 이미지 생성기 (모든 컨텐츠 공용)"""
import io

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# 등급별 그라데이션 (상단 RGB, 하단 RGB)
GRADE_GRADIENTS = {
    "Normal":    ((22, 22, 58),   (10, 10, 38)),
    "Rare":      ((8,  55, 75),   (4,  38, 55)),
    "Epic":      ((48, 8,  88),   (30, 4,  60)),
    "Legendary": ((78, 52, 4),    (50, 30, 0)),
    "Fail":      ((68, 18, 18),   (42, 8,  8)),
}

# 등급별 강조색 (테두리·라인·배지)
GRADE_ACCENT_COLORS = {
    "Normal":    (100, 130, 255),
    "Rare":      (0,   200, 160),
    "Epic":      (200, 100, 255),
    "Legendary": (255, 200,  50),
    "Fail":      (220,  80,  80),
}

# 등급별 값 텍스트 색상
GRADE_VALUE_COLORS = {
    "Normal":    (180, 200, 255),
    "Rare":      (100, 240, 190),
    "Epic":      (220, 150, 255),
    "Legendary": (255, 230, 100),
    "Fail":      (255, 150, 150),
}

# 등급 표시 라벨
GRADE_LABELS = {
    "Normal":    "★ NORMAL",
    "Rare":      "★★ RARE",
    "Epic":      "★★★ EPIC",
    "Legendary": "★★★★ LEGENDARY",
    "Fail":      "✖ FAIL",
}

_FONT_CACHE: dict = {}

_CORNER_RADIUS = 18


def _get_font(size: int):
    if not PIL_AVAILABLE:
        return None
    if size in _FONT_CACHE:
        return _FONT_CACHE[size]

    candidates = [
        "NanumGothic", "NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "MalgunGothic", "malgun.ttf",
        "NanumBarunGothic", "NanumBarunGothic.ttf",
        "DejaVuSans", "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for name in candidates:
        try:
            font = ImageFont.truetype(name, size)
            _FONT_CACHE[size] = font
            return font
        except (IOError, OSError):
            pass

    font = ImageFont.load_default()
    _FONT_CACHE[size] = font
    return font


def _draw_gradient(img: "Image.Image", top_color: tuple, bottom_color: tuple) -> None:
    """이미지에 상단→하단 RGB 그라데이션을 칠합니다."""
    w, h = img.size
    draw = ImageDraw.Draw(img)
    tr, tg, tb = top_color[:3]
    br, bg, bb = bottom_color[:3]
    for y in range(h):
        t = y / max(h - 1, 1)
        r = int(tr + (br - tr) * t)
        g = int(tg + (bg - tg) * t)
        b = int(tb + (bb - tb) * t)
        draw.line([(0, y), (w - 1, y)], fill=(r, g, b))


def _text_width(draw: "ImageDraw.ImageDraw", text: str, font) -> int:
    try:
        bb = draw.textbbox((0, 0), text, font=font)
        return bb[2] - bb[0]
    except AttributeError:
        return len(text) * (getattr(font, "size", 10) // 2 + 3)


def generate_card(
    title: str,
    icon: str,
    rows: list,
    grade: str = "Normal",
    width: int = 520,
    height: int = 320,
) -> io.BytesIO:
    """
    통일 카드 이미지를 생성하고 BytesIO로 반환합니다.
    rows: [{"label": str, "value": str}, ...]
    """
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow가 설치되지 않았슴미댜.")

    top_col  = GRADE_GRADIENTS.get(grade, GRADE_GRADIENTS["Normal"])[0]
    bot_col  = GRADE_GRADIENTS.get(grade, GRADE_GRADIENTS["Normal"])[1]
    accent   = GRADE_ACCENT_COLORS.get(grade,  (100, 130, 255))
    val_col  = GRADE_VALUE_COLORS.get(grade,   (180, 200, 255))
    lbl_col  = (175, 180, 200)
    txt_col  = (230, 232, 245)
    grade_lbl = GRADE_LABELS.get(grade, grade)

    # ── 1. 그라데이션 배경 ──────────────────────────────────────────
    bg = Image.new("RGB", (width, height))
    _draw_gradient(bg, top_col, bot_col)

    # ── 2. 둥근 모서리 마스크 ────────────────────────────────────────
    mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, width - 1, height - 1], radius=_CORNER_RADIUS, fill=255
    )
    base = Image.new("RGB", (width, height), (12, 12, 28))
    base.paste(bg, mask=mask)
    img = base

    draw = ImageDraw.Draw(img)

    # ── 3. 테두리 ────────────────────────────────────────────────────
    draw.rounded_rectangle(
        [1, 1, width - 2, height - 2],
        radius=_CORNER_RADIUS - 1,
        outline=accent,
        width=2,
    )

    # ── 4. 폰트 ──────────────────────────────────────────────────────
    font_title = _get_font(24)
    font_label = _get_font(15)
    font_value = _get_font(16)
    font_grade = _get_font(18)

    # ── 5. 헤더: 제목 + 등급 배지 ──────────────────────────────────
    HEADER_H = 62
    title_text = f"{icon}  {title}"
    draw.text((20, 16), title_text, font=font_title, fill=txt_col)

    gw = _text_width(draw, grade_lbl, font_grade)
    draw.text((width - gw - 16, 20), grade_lbl, font=font_grade, fill=accent)

    # ── 6. 장식 라인 ─────────────────────────────────────────────────
    line_y = HEADER_H
    draw.line([(16, line_y), (width - 16, line_y)], fill=accent, width=2)
    draw.ellipse([12, line_y - 3, 20, line_y + 3], fill=accent)
    draw.ellipse([width - 20, line_y - 3, width - 12, line_y + 3], fill=accent)

    # ── 7. 반투명 정보 박스 ──────────────────────────────────────────
    BOTTOM_H = 52
    bx0, by0 = 16, HEADER_H + 8
    bx1, by1 = width - 16, height - BOTTOM_H - 4

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rounded_rectangle(
        [bx0, by0, bx1, by1], radius=10, fill=(0, 0, 0, 115)
    )
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # ── 8. 행 데이터 ─────────────────────────────────────────────────
    row_h   = max(28, (by1 - by0 - 12) // max(len(rows), 1))
    row_h   = min(row_h, 34)
    pad_l   = bx0 + 14
    mid_x   = bx0 + (bx1 - bx0) // 2 + 10
    y       = by0 + 10

    for idx, row in enumerate(rows):
        label = row.get("label", "")
        value = row.get("value", "")
        if idx > 0:
            sep_y = y - 5
            draw.line([(pad_l, sep_y), (bx1 - 14, sep_y)], fill=(55, 58, 78), width=1)
        draw.text((pad_l, y), f"{label}:", font=font_label, fill=lbl_col)
        draw.text((mid_x,  y), str(value), font=font_value, fill=val_col)
        y += row_h

    # ── 9. 하단 등급 배지 ────────────────────────────────────────────
    sep_y2 = height - BOTTOM_H
    draw.line([(16, sep_y2), (width - 16, sep_y2)], fill=accent, width=1)

    badge_pad  = 12
    badge_w    = _text_width(draw, grade_lbl, font_grade) + badge_pad * 2
    badge_h    = BOTTOM_H - 14
    badge_x0   = width // 2 - badge_w // 2
    badge_y0   = sep_y2 + 6
    badge_x1   = badge_x0 + badge_w
    badge_y1   = badge_y0 + badge_h

    ov2 = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    r, g, b = accent
    ImageDraw.Draw(ov2).rounded_rectangle(
        [badge_x0, badge_y0, badge_x1, badge_y1], radius=8, fill=(r, g, b, 55)
    )
    img = Image.alpha_composite(img.convert("RGBA"), ov2).convert("RGB")
    draw = ImageDraw.Draw(img)

    btext_x = badge_x0 + badge_pad
    btext_y = badge_y0 + (badge_h - 18) // 2
    draw.text((btext_x, btext_y), grade_lbl, font=font_grade, fill=txt_col)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def generate_fishing_card(
    fish_name: str,
    size_cm: float,
    price: int,
    fee: int,
    bonus: int,
    net_profit: int,
    grade: str = "Normal",
) -> io.BytesIO:
    rows = [
        {"label": "물고기",   "value": fish_name},
        {"label": "크기",     "value": f"{size_cm:.1f} cm"},
        {"label": "판매가",   "value": f"{price:,} G"},
        {"label": "수수료",   "value": f"-{fee:,} G"},
        {"label": "보너스",   "value": f"+{bonus:,} G"},
        {"label": "순수익",   "value": f"{net_profit:,} G"},
    ]
    return generate_card(f"와! {fish_name}을(를) 낚았다!!", "🎣", rows, grade=grade)


def generate_cooking_card(
    dish_name: str,
    quality_stars: str,
    hp_en: str,
    price: int,
    grade: str = "Normal",
) -> io.BytesIO:
    rows = [
        {"label": "요리",   "value": dish_name},
        {"label": "품질",   "value": quality_stars},
        {"label": "회복",   "value": hp_en},
        {"label": "가치",   "value": f"{price:,} G"},
    ]
    return generate_card("요리 완성", "🍳", rows, grade=grade)


def generate_smelt_card(
    bar_name: str,
    purity_pct: float,
    count: int,
    price: int,
    grade: str = "Normal",
) -> io.BytesIO:
    rows = [
        {"label": "주괴",   "value": bar_name},
        {"label": "순도",   "value": f"{purity_pct:.1f}%"},
        {"label": "개수",   "value": f"{count}개"},
        {"label": "가치",   "value": f"{price:,} G"},
    ]
    return generate_card("제련 결과", "⚒", rows, grade=grade)


def generate_gather_card(
    item_name: str,
    count: int,
    rarity: str,
    grade: str = "Normal",
) -> io.BytesIO:
    rows = [
        {"label": "아이템", "value": item_name},
        {"label": "개수",   "value": f"{count}개"},
        {"label": "희귀도", "value": rarity},
    ]
    return generate_card("채집 결과", "🌿", rows, grade=grade)


def generate_job_card(
    job_name: str,
    result: str,
    gold: int,
    stat_up: str,
    grade: str = "Normal",
) -> io.BytesIO:
    rows = [
        {"label": "알바",     "value": job_name},
        {"label": "결과",     "value": result},
        {"label": "수입",     "value": f"+{gold:,} G"},
        {"label": "스탯 상승", "value": stat_up or "없음"},
    ]
    return generate_card("알바 완료", "💼", rows, grade=grade)


def generate_rest_card(
    recovered: int,
    current_energy: int,
    max_energy: int,
    elapsed_sec: float,
    grade: str = "Normal",
) -> io.BytesIO:
    minutes = int(elapsed_sec // 60)
    seconds = int(elapsed_sec % 60)
    elapsed_str = f"{minutes}분 {seconds}초" if minutes else f"{seconds}초"
    rows = [
        {"label": "회복량",   "value": f"+{recovered} EN"},
        {"label": "현재기력", "value": f"{current_energy}/{max_energy}"},
        {"label": "소요시간", "value": elapsed_str},
    ]
    return generate_card("휴식 완료!", "💤", rows, grade=grade)
