"""
fishing_card.py — BG3 스타일 카드 이미지 생성기 (모든 콘텐츠 공용)

기존 함수 시그니처 100% 유지.
내부 렌더링은 bg3_renderer.BG3Renderer.render_card()에 위임.
"""
import io

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from bg3_renderer import get_renderer

# ── 등급별 타이틀 텍스트 (원본 유지) ────────────────────────────
GRADE_TITLE_TEXT = {
    "Normal":    "🕷️ {name}을(를) 낚았슴미댜!",
    "Rare":      "🕷️✨ 오! {name} 발견임미댜!!",
    "Epic":      "🕷️🔥 와앗! {name}이(가) 잡혔슴미댜!!!",
    "Legendary": "🕷️👑 전설이댜!!! {name}?!?!",
    "Fail":      "🕷️💦 이건... 쓰레기...",
}

# ── 등급 라벨 (표시용) ───────────────────────────────────────────
GRADE_LABELS = {
    "Normal":    "★ NORMAL",
    "Rare":      "★★ RARE",
    "Epic":      "★★★ EPIC",
    "Legendary": "★★★★ LEGENDARY",
    "Fail":      "✖ FAIL",
}


def generate_card(
    title: str,
    icon: str,
    rows: list,
    grade: str = "Normal",
    width: int = 480,
    height: int = 320,
    subtitle: str = None,
) -> io.BytesIO:
    """
    범용 카드 생성 — bg3_renderer에 위임.
    icon 파라미터는 이모지 제거 후 타이틀에 결합.
    """
    r = get_renderer()
    # 콘텐츠별 system_key 자동 매핑
    sys_map = {
        "🎣": "fishing", "🍳": "cooking", "⚒": "metallurgy",
        "🌿": "gathering", "💼": "system", "💤": "rest",
    }
    sys_key = sys_map.get(icon, "system")
    return r.render_card(
        title=title,
        rows=rows,
        grade=grade,
        subtitle=subtitle,
        system_key=sys_key,
        footer=GRADE_LABELS.get(grade, grade),
        w=width,
        h=height,
    )


def generate_fishing_card(
    fish_name: str,
    size_cm: float,
    price: int,
    fee: int,
    bonus: int,
    net_profit: int,
    grade: str = "Normal",
) -> io.BytesIO:
    title_tmpl = GRADE_TITLE_TEXT.get(grade, "🕷️ {name}을(를) 낚았슴미댜!")
    title = title_tmpl.format(name=fish_name)
    rows  = [
        {"label": "물고기",  "value": fish_name},
        {"label": "크기",    "value": f"{size_cm:.1f} cm"},
    ]
    return generate_card(title, "🎣", rows, grade=grade)


def generate_card_v2(
    title: str,
    icon: str,
    rows: list,
    grade: str = "Normal",
    width: int = 480,
    height: int = 320,
    subtitle: str = None,
    spider_art_key: str = None,
) -> io.BytesIO:
    # spider_art_key는 BG3 스타일에서 더 이상 카드에 삽입하지 않음
    # 기존 호출 호환성 유지를 위해 시그니처 보존
    return generate_card(title, icon, rows,
                         grade=grade, width=width,
                         height=height, subtitle=subtitle)


def generate_cooking_card(
    dish_name: str,
    quality_stars: str,
    hp_en: str,
    price: int,
    grade: str = "Normal",
) -> io.BytesIO:
    rows = [
        {"label": "요리",  "value": dish_name},
        {"label": "품질",  "value": quality_stars},
        {"label": "회복",  "value": hp_en},
        {"label": "가치",  "value": f"{price:,} G"},
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
        {"label": "주괴",  "value": bar_name},
        {"label": "순도",  "value": f"{purity_pct:.1f}%"},
        {"label": "개수",  "value": f"{count}개"},
        {"label": "가치",  "value": f"{price:,} G"},
    ]
    return generate_card("제련 결과", "⚒", rows, grade=grade)


def generate_gather_card(
    item_name: str,
    count: int,
    rarity: str,
    grade: str = "Normal",
) -> io.BytesIO:
    from bg3_renderer import C
    grade_color = C.RARITY.get(grade, C.TXT_HI)
    rows = [
        {"label": "아이템", "value": item_name},
        {"label": "개수",   "value": f"{count}개"},
        {"label": "희귀도", "value": rarity, "color": grade_color},
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
        {"label": "보상", "value": stat_up or "없음"},
    ]
    return generate_card("알바 완료", "💼", rows, grade=grade)


def generate_rest_card(
    recovered: int,
    current_energy: int,
    max_energy: int,
    elapsed_sec: float,
    grade: str = "Normal",
) -> io.BytesIO:
    minutes     = int(elapsed_sec // 60)
    seconds     = int(elapsed_sec % 60)
    elapsed_str = f"{minutes}분 {seconds}초" if minutes else f"{seconds}초"
    rows = [
        {"label": "회복량",   "value": f"+{recovered} EN"},
        {"label": "현재기력", "value": f"{current_energy}/{max_energy}"},
        {"label": "소요시간", "value": elapsed_str},
    ]
    return generate_card("휴식 완료", "💤", rows, grade=grade)
