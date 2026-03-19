"""affinity.py — NPC 호감도 시스템"""
from ui_theme import C, ansi, header_box, divider

AFFINITY_LEVELS = [
    {"level": 0, "name": "낯선이",       "threshold": 0,   "discount": 0},
    {"level": 1, "name": "지인",          "threshold": 50,  "discount": 5},
    {"level": 2, "name": "친구",          "threshold": 150, "discount": 10},
    {"level": 3, "name": "절친",          "threshold": 350, "discount": 15},
    {"level": 4, "name": "영혼의 동반자", "threshold": 700, "discount": 20},
]


def _calc_level(points: int) -> dict:
    current = AFFINITY_LEVELS[0]
    for lv in AFFINITY_LEVELS:
        if points >= lv["threshold"]:
            current = lv
        else:
            break
    return current


class AffinityManager:
    def __init__(self, player):
        self.player      = player
        self.affinities  = {}   # npc_name: int (포인트)

    def add_affinity(self, npc_name: str, amount: int) -> tuple:
        """호감도 추가. (new_points, leveled_up, new_level_name) 반환."""
        old_points   = self.affinities.get(npc_name, 0)
        old_lv       = _calc_level(old_points)
        new_points   = old_points + amount
        self.affinities[npc_name] = new_points
        new_lv       = _calc_level(new_points)
        leveled_up   = new_lv["level"] > old_lv["level"]
        return (new_points, leveled_up, new_lv["name"])

    def get_level(self, npc_name: str) -> dict:
        pts = self.affinities.get(npc_name, 0)
        return _calc_level(pts)

    def get_level_name(self, npc_name: str) -> str:
        return self.get_level(npc_name)["name"]

    def get_shop_discount_pct(self, npc_name: str) -> int:
        return self.get_level(npc_name)["discount"]

    def show_affinity(self, npc_name: str = None) -> str:
        lines = [header_box("💖 NPC 호감도")]

        targets = [npc_name] if npc_name else list(self.affinities.keys())

        if not targets:
            lines.append(f"  {C.DARK}아직 NPC와 교류한 기록이 없슴미댜.{C.R}")
        else:
            for name in targets:
                pts  = self.affinities.get(name, 0)
                lv   = _calc_level(pts)
                disc = lv["discount"]
                # 다음 레벨까지 필요한 포인트
                next_lv = None
                for al in AFFINITY_LEVELS:
                    if al["threshold"] > pts:
                        next_lv = al
                        break

                bar_filled = min(10, int(pts / max(next_lv["threshold"] if next_lv else pts + 1, 1) * 10))
                bar_str    = "█" * bar_filled + "░" * (10 - bar_filled)

                lines.append(f"\n  {C.GOLD}{name}{C.R}  [{lv['name']}]")
                lines.append(f"    {C.WHITE}{bar_str}{C.R}  {pts}pt")
                if disc:
                    lines.append(f"    {C.GREEN}상점 할인 -{disc}%{C.R}")
                if next_lv:
                    need = next_lv["threshold"] - pts
                    lines.append(f"    {C.DARK}다음 단계까지 {need}pt 필요{C.R}")

        lines.append(divider())
        return ansi("\n".join(lines))

    def to_dict(self) -> dict:
        return {"affinities": self.affinities}

    def from_dict(self, data: dict):
        self.affinities = data.get("affinities", {})
        return self
