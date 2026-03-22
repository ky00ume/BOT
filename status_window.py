import io
from bg3_renderer import get_renderer


def create_status_image(player) -> io.BytesIO:
    """상태창 — BG3 스타일 PIL 이미지 반환"""
    name   = getattr(player, 'name',          '모험가')
    level  = getattr(player, 'level',         1)
    title  = getattr(player, 'current_title', '비전의 탑 신입')
    hp     = getattr(player, 'hp',            100)
    max_hp = getattr(player, 'max_hp',        100)
    mp     = getattr(player, 'mp',            50)
    max_mp = getattr(player, 'max_mp',        50)
    en     = getattr(player, 'energy',        100)
    max_en = getattr(player, 'max_energy',    100)
    gold   = getattr(player, 'gold',          0)
    exp    = getattr(player, 'exp',           0.0)
    stats  = getattr(player, 'base_stats',    {})
    used, max_slots = (player.inventory_check()
                       if hasattr(player, 'inventory_check') else (0, 10))
    return get_renderer().render_status_card(
        name=name, level=level, title_str=title,
        hp=hp, max_hp=max_hp, mp=mp, max_mp=max_mp,
        en=en, max_en=max_en, gold=gold,
        exp=float(exp), exp_needed=level*100,
        stats=stats, inv_used=used, inv_max=max_slots,
    )


def create_party_status_image(player) -> io.BytesIO:
    """파티 상태 — BG3 스타일 PIL 이미지 반환"""
    name   = getattr(player, 'name',       '모험가')
    level  = getattr(player, 'level',      1)
    hp     = getattr(player, 'hp',         100)
    max_hp = getattr(player, 'max_hp',     100)
    mp     = getattr(player, 'mp',         50)
    max_mp = getattr(player, 'max_mp',     50)
    en     = getattr(player, 'energy',     100)
    max_en = getattr(player, 'max_energy', 100)

    rows = [
        {"label": f"Lv.{level} {name}", "value": ""},
        {"label": "HP", "value": f"{hp}/{max_hp}"},
        {"label": "MP", "value": f"{mp}/{max_mp}"},
        {"label": "EN", "value": f"{en}/{max_en}"},
    ]
    return get_renderer().render_card(
        title="파티 상태", rows=rows,
        system_key="status", footer="✦ 파티 정보 ✦",
        w=400, h=260,
    )
