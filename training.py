"""training.py — 훈련소/학교 시스템 (골드+스탯 소비 수련)"""
from ui_theme import C, ansi, header_box, divider

# ─── 스탯 수련 설정 ─────────────────────────────────────────────────────────
# 각 스탯 1포인트 올리는 데 드는 골드 = BASE_COST + (현재 스탯 * SCALE_COST)
STAT_TRAIN_CONFIG = {
    "str":  {"name": "힘",   "icon": "⚔️",  "base_cost": 200,  "scale": 30,  "desc": "물리 공격력 증가"},
    "int":  {"name": "지력", "icon": "🔮",  "base_cost": 200,  "scale": 30,  "desc": "마법 공격력 증가"},
    "dex":  {"name": "민첩", "icon": "🏹",  "base_cost": 180,  "scale": 25,  "desc": "명중·회피 증가"},
    "will": {"name": "의지", "icon": "🛡️",  "base_cost": 180,  "scale": 25,  "desc": "최대 MP·정신력 증가"},
    "luck": {"name": "운",   "icon": "🍀",  "base_cost": 300,  "scale": 50,  "desc": "크리티컬·드랍률 증가"},
}

# 수련 시 현재 스탯×10의 에너지 소비
ENERGY_PER_POINT = 10
MIN_ENERGY_COST  = 5  # 에너지 최소 소모량


def _train_cost(stat_id: str, current_val: int) -> int:
    cfg = STAT_TRAIN_CONFIG[stat_id]
    return cfg["base_cost"] + current_val * cfg["scale"]


class TrainingSystem:
    def __init__(self, player):
        self.player = player

    def show_menu(self) -> str:
        """훈련 메뉴를 보여줍니다."""
        p = self.player
        lines = [
            header_box("🏋️  훈련소"),
            f"  보유 골드: {C.GOLD}{p.gold}G{C.R}   기력: {C.GREEN}{p.energy}/{p.max_energy}{C.R}",
            divider(),
            f"  {C.WHITE}스탯{C.R}       {C.GOLD}현재치{C.R}   {C.RED}수련 비용{C.R}   {C.DARK}기력 소모{C.R}",
            divider(),
        ]
        for stat_id, cfg in STAT_TRAIN_CONFIG.items():
            cur  = p.base_stats.get(stat_id, 0)
            cost = _train_cost(stat_id, cur)
            energy_cost = ENERGY_PER_POINT * cur
            lines.append(
                f"  {cfg['icon']} {C.WHITE}{cfg['name']:<4}{C.R}"
                f"  {C.CYAN}{cur:>3}{C.R}"
                f"  {C.GOLD}{cost:>6}G{C.R}"
                f"  {C.RED}{energy_cost:>4}{C.R}"
                f"  {C.DARK}{cfg['desc']}{C.R}"
            )
        lines.append(divider())
        lines.append(f"  {C.GREEN}/수련 [스탯]{C.R} — 예: /수련 str  /수련 힘")
        return ansi("\n".join(lines))

    def train(self, stat_input: str) -> str:
        """지정 스탯을 1 올립니다."""
        p = self.player

        # 한글 이름도 허용
        _name_map = {cfg["name"]: sid for sid, cfg in STAT_TRAIN_CONFIG.items()}
        stat_id = _name_map.get(stat_input, stat_input.lower())

        if stat_id not in STAT_TRAIN_CONFIG:
            valid = ", ".join(
                f"{v['icon']}{v['name']}({k})" for k, v in STAT_TRAIN_CONFIG.items()
            )
            return ansi(f"  {C.RED}✖ 유효한 스탯이 아님미댜! ({valid}){C.R}")

        cfg = STAT_TRAIN_CONFIG[stat_id]
        cur = p.base_stats.get(stat_id, 0)
        cost = _train_cost(stat_id, cur)
        energy_cost = max(MIN_ENERGY_COST, ENERGY_PER_POINT * cur)

        if p.gold < cost:
            return ansi(
                f"  {C.RED}✖ 골드가 부족함미댜! (필요: {cost}G, 보유: {p.gold}G){C.R}"
            )
        if p.energy < energy_cost:
            return ansi(
                f"  {C.RED}✖ 기력이 부족함미댜! (필요: {energy_cost}, 보유: {p.energy}){C.R}"
            )

        p.gold -= cost
        p.energy -= energy_cost
        p.base_stats[stat_id] = cur + 1

        # will 올리면 최대 MP도 증가
        if stat_id == "will":
            p.max_mp += 5
            p.mp = min(p.mp, p.max_mp)

        new_val = p.base_stats[stat_id]
        lines = [
            header_box(f"🏋️  수련 완료!"),
            f"  {cfg['icon']} {C.WHITE}{cfg['name']}{C.R}  "
            f"{C.DARK}{cur}{C.R} → {C.GREEN}{new_val}{C.R}",
            f"  {C.RED}-{cost}G{C.R}   기력 {C.RED}-{energy_cost}{C.R}",
        ]
        if stat_id == "will":
            lines.append(f"  {C.BLUE}최대 MP +5 (현재: {p.max_mp}){C.R}")
        lines.append(f"\n  {C.DARK}다음 수련 비용: {_train_cost(stat_id, new_val)}G{C.R}")
        return ansi("\n".join(lines))
