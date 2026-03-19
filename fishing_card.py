"""fishing_card.py — PIL 통일 카드 이미지 생성기 (모든 컨텐츠 공용)"""
import io

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

GRADE_COLORS = {
    "Normal":    "#1a1a2e",
    "Rare":      "#0d3320",
    "Epic":      "#2d0a4e",
    "Legendary": "#3d2b00",
    "Fail":      "#3d1a1a",
}

GRADE_TITLE_COLORS = {
    "Normal":    (180, 180, 220),
    "Rare":      (100, 220, 150),
    "Epic":      (180, 120, 255),
    "Legendary": (255, 215,   0),
    "Fail":      (200, 100, 100),
}

_FONT_CACHE = {}


def _hex_to_rgb(hex_str: str) -> tuple:
    hex_str = hex_str.lstrip("#")
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))


def _get_font(size: int):
    if not PIL_AVAILABLE:
        return None
    key = size
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]

    candidates = [
        "NanumGothic", "NanumGothic.ttf",
        "MalgunGothic", "malgun.ttf",
        "NanumBarunGothic", "NanumBarunGothic.ttf",
    ]
    for name in candidates:
        try:
            font = ImageFont.truetype(name, size)
            _FONT_CACHE[key] = font
            return font
        except (IOError, OSError):
            pass

    font = ImageFont.load_default()
    _FONT_CACHE[key] = font
    return font


def generate_card(
    title: str,
    icon: str,
    rows: list,
    grade: str = "Normal",
    width: int = 400,
    height: int = 250,
) -> io.BytesIO:
    """
    통일 카드 이미지를 생성하고 BytesIO로 반환합니다.
    rows: [{"label": str, "value": str}, ...]
    """
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow가 설치되지 않았슴미댜.")

    bg_color  = _hex_to_rgb(GRADE_COLORS.get(grade, GRADE_COLORS["Normal"]))
    tc_color  = GRADE_TITLE_COLORS.get(grade, (180, 180, 220))
    txt_color = (220, 220, 230)
    val_color = (255, 255, 200)

    img  = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # 테두리
    for i in range(3):
        draw.rectangle([i, i, width - 1 - i, height - 1 - i], outline=tc_color)

    font_title = _get_font(20)
    font_label = _get_font(14)
    font_value = _get_font(14)

    # 제목
    title_text = f"{icon} {title}"
    draw.text((16, 14), title_text, font=font_title, fill=tc_color)

    # 구분선
    draw.line([(16, 44), (width - 16, 44)], fill=tc_color, width=1)

    # 행 데이터
    y = 54
    row_h = 26
    for row in rows:
        label = row.get("label", "")
        value = row.get("value", "")
        draw.text((20,         y), f"{label}:", font=font_label, fill=txt_color)
        draw.text((width // 2, y), str(value),  font=font_value, fill=val_color)
        y += row_h

    # 등급 배지
    grade_text = f"[ {grade} ]"
    draw.text((width - 90, height - 22), grade_text, font=font_label, fill=tc_color)

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
    return generate_card("낚시 결과", "🎣", rows, grade=grade)


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
