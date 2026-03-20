"""movement.py — 이동 시스템 (맵 구조 + 쿨다운)"""
import time
from ui_theme import C, ansi, header_box, divider

# ─── 맵 구조 ───────────────────────────────────────────────────────────────
# 각 노드: 이름, 설명, 레벨 요구, 아이콘, 인접 노드 목록
MAP_NODES = {
    "마을": {
        "name":              "비전의 마을",
        "icon":              "🏘️",
        "desc":              "모험가들이 모이는 평화로운 마을.",
        "level":             1,
        "hunting_available": False,
        "adjacent":          ["방울숲"],
    },
    "방울숲": {
        "name":              "방울숲",
        "icon":              "🌲",
        "desc":              "초보 모험가들이 처음 발을 내딛는 아담한 숲.",
        "level":             1,
        "hunting_available": True,
        "adjacent":          ["마을", "고블린동굴"],
    },
    "고블린동굴": {
        "name":              "고블린 동굴",
        "icon":              "🪨",
        "desc":              "고블린들이 소굴을 이룬 지하 동굴.",
        "level":             5,
        "hunting_available": True,
        "adjacent":          ["방울숲", "소금광산"],
    },
    "소금광산": {
        "name":              "소금 광산",
        "icon":              "⛏️",
        "desc":              "소금 결정이 빛나는 어둠의 광산.",
        "level":             10,
        "hunting_available": True,
        "adjacent":          ["고블린동굴", "요정의 숲"],
    },
    "요정의 숲": {
        "name":              "요정의 숲",
        "icon":              "🧚",
        "desc":              "요정들이 살아가는 신비로운 마법의 숲.",
        "level":             15,
        "hunting_available": True,
        "adjacent":          ["소금광산", "용암 동굴"],
    },
    "용암 동굴": {
        "name":              "용암 동굴",
        "icon":              "🌋",
        "desc":              "불꽃과 용암이 흐르는 위험한 동굴.",
        "level":             25,
        "hunting_available": True,
        "adjacent":          ["요정의 숲", "심해 던전"],
    },
    "심해 던전": {
        "name":              "심해 던전",
        "icon":              "🌊",
        "desc":              "바다 깊은 곳에 잠긴 고대의 던전.",
        "level":             35,
        "hunting_available": True,
        "adjacent":          ["용암 동굴"],
    },
}

# 이동 쿨다운 (초)
MOVE_COOLDOWN_SEC = 180  # 3분


class MovementSystem:
    def __init__(self, player):
        self.player   = player
        self._cooldowns: dict[int, float] = {}

    def _get_location(self) -> str:
        return getattr(self.player, "current_location", "마을")

    def _set_location(self, loc: str):
        self.player.current_location = loc

    def show_map(self, user_id: int) -> str:
        """현재 위치와 이동 가능한 곳을 보여줍니다."""
        current = self._get_location()
        node    = MAP_NODES.get(current, MAP_NODES["마을"])
        lines   = [
            header_box(f"🗺️  현재 위치: {node['icon']} {node['name']}"),
            f"  {C.DARK}{node['desc']}{C.R}",
            divider(),
            f"  {C.GOLD}이동 가능한 곳:{C.R}",
        ]
        for adj in node["adjacent"]:
            adj_node = MAP_NODES[adj]
            lv_color = C.GREEN if self.player.level >= adj_node["level"] else C.RED
            lv_text  = f"Lv.{adj_node['level']}+" if adj_node["level"] > 1 else "입문"
            lines.append(
                f"  {adj_node['icon']} {C.WHITE}{adj_node['name']}{C.R}"
                f" {lv_color}({lv_text}){C.R}"
                f"  {C.GREEN}/이동 {adj}{C.R}"
            )
        # 쿨다운 표시
        now      = time.time()
        last     = self._cooldowns.get(user_id, 0)
        remain   = MOVE_COOLDOWN_SEC - (now - last)
        if remain > 0:
            m, s = int(remain // 60), int(remain % 60)
            lines.append(divider())
            lines.append(f"  {C.RED}⏳ 이동 쿨다운: {m}분 {s}초 남음{C.R}")
        return ansi("\n".join(lines))

    def move_to(self, user_id: int, destination: str) -> str:
        """지정한 장소로 이동합니다."""
        current = self._get_location()

        if destination not in MAP_NODES:
            return ansi(f"  {C.RED}✖ [{destination}]은(는) 존재하지 않는 장소임미댜!{C.R}")

        if destination == current:
            return ansi(f"  {C.YELLOW}⚠ 이미 {MAP_NODES[current]['icon']} {MAP_NODES[current]['name']}에 있슴미댜!{C.R}")

        node = MAP_NODES.get(current, MAP_NODES["마을"])
        if destination not in node["adjacent"]:
            return ansi(
                f"  {C.RED}✖ {MAP_NODES[current]['icon']} {MAP_NODES[current]['name']}에서는"
                f" {MAP_NODES[destination]['icon']} {MAP_NODES[destination]['name']}으로 직접 이동할 수 없슴미댜!{C.R}"
            )

        dest_node = MAP_NODES[destination]
        if self.player.level < dest_node["level"]:
            return ansi(
                f"  {C.RED}✖ {dest_node['icon']} {dest_node['name']}은(는)"
                f" Lv.{dest_node['level']} 이상 필요합미댜! (현재: Lv.{self.player.level}){C.R}"
            )

        now  = time.time()
        last = self._cooldowns.get(user_id, 0)
        remain = MOVE_COOLDOWN_SEC - (now - last)
        if remain > 0:
            m, s = int(remain // 60), int(remain % 60)
            return ansi(f"  {C.RED}⏳ 아직 이동할 수 없슴미댜! 남은 시간: {m}분 {s}초{C.R}")

        self._cooldowns[user_id] = now
        self._set_location(destination)

        lines = [
            header_box(f"🚶 이동 완료!"),
            f"  {MAP_NODES[current]['icon']} {C.DARK}{MAP_NODES[current]['name']}{C.R}"
            f"  →  {dest_node['icon']} {C.WHITE}{dest_node['name']}{C.R}",
            f"  {C.DARK}{dest_node['desc']}{C.R}",
        ]
        # 사냥 가능 지역 안내
        if dest_node.get("hunting_available", False):
            lines.append(f"\n  {C.GREEN}/사냥 {destination}{C.R} 으로 바로 사냥 가능합미댜!")
        return ansi("\n".join(lines))
