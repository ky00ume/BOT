import random
from ui_theme import C, section, divider, header_box, ansi, rank_badge, FOOTERS

FISH_GUIDE = {
    "방울숲 강": {
        "desc": "조용한 방울숲 근처의 작은 강.",
        "fish": [
            {"id": "fs_carp_01",   "name": "잉어",   "rate": 0.50, "rank_req": "연습"},
            {"id": "fs_salmon_01", "name": "연어",   "rate": 0.25, "rank_req": "F"},
            {"id": "fs_eel_01",    "name": "장어",   "rate": 0.15, "rank_req": "E"},
        ],
        "energy_cost": 10,
    },
    "소금광산 지하호수": {
        "desc": "소금 광산 깊은 곳의 지하호수.",
        "fish": [
            {"id": "fs_carp_01",   "name": "잉어",   "rate": 0.30, "rank_req": "연습"},
            {"id": "fs_salmon_01", "name": "연어",   "rate": 0.35, "rank_req": "D"},
            {"id": "fs_eel_01",    "name": "장어",   "rate": 0.30, "rank_req": "C"},
        ],
        "energy_cost": 20,
    },
}

RANK_ORDER_FISH = ["연습", "F", "E", "D", "C", "B", "A", "9", "8", "7", "6", "5", "4", "3", "2", "1"]


def _rank_gte(rank_a: str, rank_b: str) -> bool:
    if rank_a not in RANK_ORDER_FISH or rank_b not in RANK_ORDER_FISH:
        return False
    return RANK_ORDER_FISH.index(rank_a) >= RANK_ORDER_FISH.index(rank_b)


class FishingEngine:
    def __init__(self, player):
        self.player = player
        self.current_spot = "방울숲 강"

    def show_fish_guide(self) -> str:
        rank = self.player.skill_ranks.get("fishing", "연습")
        lines = [header_box("🎣 낚시 도감"), section("낚시터 & 물고기")]

        for spot_name, spot in FISH_GUIDE.items():
            lines.append(f"  {C.GOLD}[{spot_name}]{C.R}")
            lines.append(f"    {C.DARK}{spot['desc']}{C.R}")
            for fish in spot["fish"]:
                rr = fish.get("rank_req", "연습")
                unlocked = _rank_gte(rank, rr)
                badge    = rank_badge(rr)
                avail    = f"{C.GREEN}[가능]{C.R}" if unlocked else f"{C.DARK}[미해금]{C.R}"
                pct      = int(fish["rate"] * 100)
                lines.append(
                    f"    {avail} {badge} {C.WHITE}{fish['name']}{C.R}  "
                    f"{C.DARK}확률 {pct}%{C.R}"
                )
            lines.append(f"    {C.RED}기력 -{spot['energy_cost']}{C.R}")

        lines.append(divider())
        lines.append(f"  {C.GREEN}/낚시{C.R} 로 낚시하셰요!")
        return ansi("\n".join(lines))

    def fish(self) -> str:
        spot_name = self.current_spot
        spot = FISH_GUIDE.get(spot_name, list(FISH_GUIDE.values())[0])

        energy_cost = spot.get("energy_cost", 10)
        if not self.player.consume_energy(energy_cost):
            return ansi(
                f"  {C.RED}✖ 기력이 부족함미댜! (필요: {energy_cost}, 보유: {self.player.energy}){C.R}"
            )

        rank = self.player.skill_ranks.get("fishing", "연습")
        luck = self.player.base_stats.get("luck", 5)

        # 낚시 성공률 (luck 기반)
        bite_rate = min(0.9, 0.5 + luck * 0.02)
        if random.random() > bite_rate:
            self.player.train_skill("fishing", 3.0)
            return ansi(
                f"  {C.DARK}🎣 낚싯대를 드리웠지만... 아무것도 걸리지 않았슴미댜.{C.R}"
            )

        # 물고기 결정
        available_fish = [
            f for f in spot["fish"]
            if _rank_gte(rank, f.get("rank_req", "연습"))
        ]
        if not available_fish:
            available_fish = spot["fish"]

        total_rate = sum(f["rate"] for f in available_fish)
        roll = random.uniform(0, total_rate)
        caught = None
        cumulative = 0
        for fish in available_fish:
            cumulative += fish["rate"]
            if roll <= cumulative:
                caught = fish
                break
        if not caught:
            caught = available_fish[-1]

        fish_id   = caught["id"]
        fish_name = caught["name"]

        added = self.player.add_item(fish_id)
        exp   = 15.0
        rank_msg = self.player.train_skill("fishing", exp)

        lines = [header_box("🎣 낚시 성공!")]
        if added:
            lines.append(f"  {C.GREEN}✔ {fish_name}{C.R} 을(를) 낚았슴미댜!")
        else:
            lines.append(f"  {C.RED}✖ 인벤토리가 가득 차서 {fish_name}을(를) 놓쳤슴미댜.{C.R}")
        lines.append(f"  {C.GOLD}낚시 숙련도 +{exp}{C.R}")
        if rank_msg:
            lines.append(f"  {C.GOLD}{rank_msg}{C.R}")

        return ansi("\n".join(lines))
