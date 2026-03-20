"""restaurant.py — 식당 납품 알바 및 요리 버프 시스템"""
import asyncio
import random
import discord
from ui_theme import C, ansi, header_box, divider, EMBED_COLOR, FOOTERS


DELIVERY_MENU = {
    "ck_soup_01":    {"name": "수프",        "delivery_price": 180,  "desc": "브룩샤 식당 기본 메뉴"},
    "ck_steak_01":   {"name": "스테이크",    "delivery_price": 350,  "desc": "브룩샤 식당 인기 메뉴"},
    "ck_special_01": {"name": "특제 요리",   "delivery_price": 600,  "desc": "브룩샤 식당 특선 메뉴"},
}

FOOD_BUFFS = {
    "ck_soup_01":    {"str": 2,  "duration_min": 10, "desc": "10분간 힘 +2"},
    "ck_steak_01":   {"str": 5,  "int": 3, "duration_min": 20, "desc": "20분간 힘 +5, 지력 +3"},
    "ck_special_01": {"str": 8,  "int": 5, "dex": 5, "duration_min": 30, "desc": "30분간 힘 +8, 지력 +5, 민첩 +5"},
}


class RestaurantEngine:
    def __init__(self, player):
        self.player = player

    async def deliver_food(self, ctx, item_name: str = None):
        """브룩샤 식당에 요리를 납품합니다 (/납품 [요리이름])."""
        if not item_name:
            lines = [
                header_box("🍽 식당 납품 목록"),
                f"  브룩샤 식당에 납품 가능한 요리:",
                divider(),
            ]
            for item_id, info in DELIVERY_MENU.items():
                lines.append(
                    f"  🍴 {C.WHITE}{info['name']}{C.R}  "
                    f"{C.GOLD}{info['delivery_price']}G{C.R}  "
                    f"{C.DARK}{info['desc']}{C.R}"
                )
            lines.append(divider())
            lines.append(f"  {C.GREEN}/납품 [요리이름]{C.R} 으로 납품하셰요!")
            await ctx.send(ansi("\n".join(lines)))
            return

        from shop import find_item_by_name
        item_id = find_item_by_name(item_name)
        delivery = DELIVERY_MENU.get(item_id) if item_id else None

        if not delivery:
            await ctx.send(ansi(f"  {C.RED}✖ [{item_name}]은(는) 납품 가능한 요리가 아님미댜!{C.R}"))
            return

        if self.player.inventory.get(item_id, 0) == 0:
            await ctx.send(ansi(f"  {C.RED}✖ [{delivery['name']}]이(가) 인벤토리에 없슴미댜!{C.R}"))
            return

        await ctx.send(ansi(
            f"  {C.GOLD}🍽 브룩샤 식당에 납품 중임미댜...{C.R}\n"
            f"  {C.DARK}브룩샤가 맛있게 쓰겠다고 했슴미댜~{C.R}"
        ))
        await asyncio.sleep(2)

        self.player.remove_item(item_id, 1)
        reward = delivery["delivery_price"]
        self.player.gold += reward

        lines = [
            header_box("🍽 납품 완료!"),
            f"  {C.WHITE}{delivery['name']}{C.R} 1개 납품",
            divider(),
            f"  {C.GOLD}+{reward}G{C.R} (현재: {self.player.gold:,}G)",
        ]
        await ctx.send(ansi("\n".join(lines)))

    async def gift_food(self, ctx, npc_name: str = None, item_name: str = None):
        """NPC에게 요리를 선물합니다 (/선물 [NPC이름] [요리이름])."""
        if not npc_name or not item_name:
            await ctx.send(ansi(
                f"  {C.RED}✖ /선물 [NPC이름] [요리이름] 형식으로 입력하셰요!{C.R}\n"
                f"  예시: /선물 브룩샤 수프"
            ))
            return

        from database import NPC_DATA
        npc = NPC_DATA.get(npc_name)
        if not npc:
            await ctx.send(ansi(f"  {C.RED}✖ [{npc_name}]을(를) 찾을 수 없슴미댜!{C.R}"))
            return

        from shop import find_item_by_name
        from items import COOKED_DISHES, CONSUMABLES
        item_id = find_item_by_name(item_name)
        all_food = {**COOKED_DISHES, **CONSUMABLES}
        item = all_food.get(item_id) if item_id else None

        if not item:
            await ctx.send(ansi(f"  {C.RED}✖ [{item_name}]은(는) 선물할 수 있는 아이템이 아님미댜!{C.R}"))
            return

        if self.player.inventory.get(item_id, 0) == 0:
            await ctx.send(ansi(f"  {C.RED}✖ [{item['name']}]이(가) 인벤토리에 없슴미댜!{C.R}"))
            return

        self.player.remove_item(item_id, 1)

        aff_bonus = random.randint(3, 8)
        try:
            if hasattr(self.player, "_affinity_manager") and self.player._affinity_manager:
                aff = self.player._affinity_manager
                if hasattr(aff, "add_affinity"):
                    aff.add_affinity(npc_name, aff_bonus)
        except Exception:
            pass

        lines = [
            header_box(f"🎁 {npc_name}에게 선물!"),
            f"  {C.WHITE}{item['name']}{C.R} 을(를) {npc['name']}에게 선물했슴미댜!",
            divider(),
            f"  {C.PINK}💕 호감도 +{aff_bonus}{C.R}",
            f"  {C.DARK}\"{random.choice(['고마워요~!', '맛있어 보여요!', '어머, 이걸 저한테?', '감사합니다!'])}\"{C.R}",
        ]
        await ctx.send(ansi("\n".join(lines)))
