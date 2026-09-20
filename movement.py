"""movement.py — 이동 시스템 (맵 구조 + 쿨다운)"""
import time
from ui_theme import C, ansi, header_box, divider

# ─── 맵 구조 ───────────────────────────────────────────────────────────────
# 각 노드: 이름, 설명, 레벨 요구, 아이콘, 인접 노드 목록
MAP_NODES = {
    "비전의 탑": {"name":"비전의 탑", "icon":"🏰", "desc":"에본레이크 남서쪽 절벽에 선 츄라이더의 집이자 생활 거점.", "level":1, "hunting_available":False, "adjacent":["드레드 할로우", "에본레이크"]},
    "마이코니드 군락": {"name":"마이코니드 군락", "icon":"🍄", "desc":"발광버섯과 포자 속에 자리한 언더다크의 안전한 생활 거점.", "level":1, "hunting_available":False, "adjacent":["드레드 할로우", "에본레이크", "비버뱅 군락"]},
    "드레드 할로우": {"name":"드레드 할로우 · 수서 나무", "icon":"🌳", "desc":"거대한 수서 나무와 푸른 발광 식물이 자라는 위험한 숲.", "level":1, "hunting_available":True, "adjacent":["비전의 탑", "마이코니드 군락", "폐허가 된 마을"]},
    "에본레이크": {"name":"에본레이크", "icon":"🌊", "desc":"언더다크 깊은 곳의 검은 호수. 낚시와 선착장 이동의 중심.", "level":1, "hunting_available":False, "adjacent":["비전의 탑", "마이코니드 군락", "폐허가 된 마을", "곪아가는 만"]},
    "폐허가 된 마을": {"name":"폐허가 된 마을", "icon":"🏚️", "desc":"에본레이크 가장자리의 버려진 듀에르가 정착지와 선착장.", "level":5, "hunting_available":True, "adjacent":["드레드 할로우", "에본레이크", "그림포지"]},
    "그림포지": {"name":"그림포지", "icon":"⛏️", "desc":"에본레이크 건너편의 듀에르가 유적. 광맥과 제련 시설이 남아 있다.", "level":10, "hunting_available":True, "adjacent":["폐허가 된 마을", "아다만틴 대장간"]},
    "아다만틴 대장간": {"name":"아다만틴 대장간", "icon":"🔥", "desc":"그림포지 깊은 곳, 용암과 고대 제련 장치가 남은 위험 지역.", "level":25, "hunting_available":True, "adjacent":["그림포지", "샤의 고대 사원"]},
    "샤의 고대 사원": {"name":"샤의 고대 사원", "icon":"🌑", "desc":"그림포지 너머로 보이는 오래된 샤의 유적. 고난도 탐험 지역.", "level":35, "hunting_available":True, "adjacent":["아다만틴 대장간"]},
    "셀루네 전초기지": {"name":"셀루네 전초기지", "icon":"🌙", "desc":"언더다크 남동쪽의 셀루네 요새 유적. 방어 시설과 위험한 길목이 남아 있다.", "level":15, "hunting_available":True, "adjacent":["드레드 할로우"]},
    "곪아가는 만": {"name":"곪아가는 만", "icon":"🐟", "desc":"비전의 탑 인근 절벽 아래 숨은 쿠오토아의 만. 낚시와 비밀 탐험에 적합하다.", "level":8, "hunting_available":False, "adjacent":["에본레이크"]},
    "비버뱅 군락": {"name":"비버뱅 군락", "icon":"💥", "desc":"마이코니드 군락 바깥의 위험한 버섯 지대. 작은 실수도 연쇄 폭발로 이어진다.", "level":5, "hunting_available":False, "adjacent":["마이코니드 군락"], "story_locked":True},
}

# 이동 쿨다운 (초)
MOVE_COOLDOWN_SEC = 180  # 3분


class MovementSystem:
    def __init__(self, player):
        self.player   = player
        self._cooldowns: dict[int, float] = {}

    def _get_location(self) -> str:
        return getattr(self.player, "current_location", "비전의 탑")

    def _set_location(self, loc: str):
        self.player.current_location = loc

    def show_map(self, user_id: int) -> str:
        """현재 위치와 이동 가능한 곳을 보여줍니다."""
        current = self._get_location()
        node    = MAP_NODES.get(current, MAP_NODES["비전의 탑"])
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

        node = MAP_NODES.get(current, MAP_NODES["비전의 탑"])
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

        # 스토리 잠금 구역 체크
        if dest_node.get("story_locked"):
            sq_mgr = getattr(self.player, "_story_quest_manager", None)
            unlocked = False
            if sq_mgr is not None:
                unlocked = sq_mgr.flags.get("비버뱅 군락_해금", False)
            if not unlocked:
                return ansi(
                    f"  {C.RED}🔒 {dest_node['icon']} {dest_node['name']}은(는) 스토리 진행 후 입장 가능합미댜!{C.R}\n"
                    f"  {C.DARK}(챕터 3 Q1 완료 후 접근 가능){C.R}"
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
