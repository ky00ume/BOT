# cogs/character_cog.py
import discord
from discord.ext import commands
from items import ALL_ITEMS
from ui_theme import C, ansi, EMBED_COLOR
from bg3_renderer import get_renderer
from save_manager import save_manager
from shop import find_item_by_name
from status_window import create_status_image
from equipment_window import create_equipment_image
from utils.discord_helpers import send_image, send_msg_card, check_channel


class CharacterCog(commands.Cog, name="캐릭터"):
    def __init__(self, bot):
        self.bot = bot

    @property
    def ctx(self):
        return self.bot.ctx

    @commands.command(name="상태", aliases=["상태창"])
    async def status_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        buf = create_status_image(self.ctx.player)
        await send_image(ctx, buf, 'status.png')

    @commands.command(name="장비", aliases=["장비창"])
    async def equipment_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        buf = create_equipment_image(self.ctx.player)
        await send_image(ctx, buf, 'equipment.png')

    @commands.command(name="스왑")
    async def swap_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        self.ctx.player.swap_weapons()
        main_id   = self.ctx.player.equipment.get("main")
        sub_id    = self.ctx.player.equipment.get("sub")
        main_name = ALL_ITEMS.get(main_id, {}).get("name", "없음") if main_id else "없음"
        sub_name  = ALL_ITEMS.get(sub_id,  {}).get("name", "없음") if sub_id  else "없음"
        buf = get_renderer().render_card(
            "무기 교환",
            rows=[
                {"label": "주무기", "value": main_name},
                {"label": "보조무기", "value": sub_name},
            ],
            subtitle="주·보조 슬롯이 교환됐슴미댜!",
            system_key="system",
            footer="교환 완료",
        )
        await send_image(ctx, buf, "swap.png")
        save_manager.save(self.ctx.player)

    @commands.command(name="장착")
    async def equip_cmd(self, ctx, *, item_name: str = None):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        if not item_name:
            await ctx.send(ansi(f"  {C.RED}✖ /장착 [아이템이름] 형식으로 입력하셰요!{C.R}"))
            return
        item_id = find_item_by_name(item_name)
        if not item_id:
            await ctx.send(ansi(f"  {C.RED}✖ [{item_name}]을(를) 찾을 수 없슴미댜!{C.R}"))
            return
        if self.ctx.player.inventory.get(item_id, 0) == 0:
            await ctx.send(ansi(f"  {C.RED}✖ 인벤토리에 [{item_name}]가 없슴미댜!{C.R}"))
            return
        item_data = ALL_ITEMS.get(item_id, {})
        if item_data.get("type") not in ("weapon", "armor"):
            await ctx.send(ansi(f"  {C.RED}✖ [{item_data.get('name', item_name)}]은(는) 장착할 수 없는 아이템임미댜!{C.R}"))
            return
        msg = self.ctx.player.equip_item(item_id)
        _SLOT_KR = {"main": "주무기", "sub": "보조무기", "body": "갑옷", "head": "투구", "hands": "장갑", "feet": "신발"}
        slot_kr  = _SLOT_KR.get(item_data.get("slot", ""), item_data.get("slot", "?"))
        buf = get_renderer().render_card(
            "장비 장착",
            rows=[
                {"label": "아이템", "value": item_data.get("name", item_name)},
                {"label": "슬롯",   "value": slot_kr},
            ],
            subtitle=msg,
            system_key="system",
            footer="장착 완료",
        )
        await send_image(ctx, buf, "equip.png")
        save_manager.save(self.ctx.player)

    @commands.command(name="벗기", aliases=["탈착", "장비해제"])
    async def unequip_cmd(self, ctx, slot: str = None):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        if not slot:
            await ctx.send(ansi(
                f"  {C.RED}✖ /벗기 [슬롯] 형식으로 입력하셰요!{C.R}\n"
                f"  {C.DARK}슬롯: main(주무기) sub(보조) body(갑옷) head(투구) hands(장갑) feet(신발){C.R}"
            ))
            return
        msg = self.ctx.player.unequip_item(slot.lower())
        if "올바른 슬롯" in msg or "비어있" in msg:
            await ctx.send(ansi(f"  {C.RED}✖ {msg}{C.R}"))
        else:
            await send_msg_card(ctx, "장비 해제", msg, system_key="system")
            save_manager.save(self.ctx.player)

    @commands.command(name="치료")
    async def heal_cmd(self, ctx):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        cost = 50
        if self.ctx.player.gold < cost:
            await ctx.send(ansi(f"  {C.RED}✖ 골드 부족! 치료비: {cost}G{C.R}"))
            return
        self.ctx.player.gold -= cost
        heal_hp = self.ctx.player.max_hp - self.ctx.player.hp
        heal_mp = self.ctx.player.max_mp - self.ctx.player.mp
        self.ctx.player.hp = self.ctx.player.max_hp
        self.ctx.player.mp = self.ctx.player.max_mp
        buf = get_renderer().render_card(
            "치료 완료",
            rows=[
                {"label": "HP 회복", "value": f"+{heal_hp} HP"},
                {"label": "MP 회복", "value": f"+{heal_mp} MP"},
                {"label": "치료비",  "value": f"-{cost}G (잔액: {self.ctx.player.gold:,}G)"},
            ],
            subtitle="HP와 MP가 완전 회복됐슴미댜!",
            system_key="system",
            footer="비전 타운 의료소",
        )
        await send_image(ctx, buf, "heal.png")
        save_manager.save(self.ctx.player)

    @commands.command(name="먹기")
    async def eat_item(self, ctx, *, item_name: str = None):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        if not item_name:
            await ctx.send(ansi(f"  {C.RED}✖ /먹기 [아이템이름] 형식으로 입력하셰요!{C.R}"))
            return
        item_id = find_item_by_name(item_name)
        if not item_id or self.ctx.player.inventory.get(item_id, 0) == 0:
            await ctx.send(ansi(f"  {C.RED}✖ 인벤토리에 [{item_name}]가 없슴미댜!{C.R}"))
            return

        # 레벨업 사탕 특별 처리
        if item_id == "levelup_potion":
            self.ctx.player.remove_item(item_id, 1)
            old_level = self.ctx.player.level
            self.ctx.player.level += 1
            from player import apply_level_up
            gains = apply_level_up(self.ctx.player)
            rows = [{"label": "레벨", "value": f"{old_level} → {self.ctx.player.level}"}]
            rows += [{"label": k, "value": f"+{v}"} for k, v in gains.items()]
            buf = get_renderer().render_card(
                "레벨 업! ✨",
                rows=rows,
                grade="Legendary",
                subtitle="레벨업 사탕 사용!",
                system_key="system",
                footer="레벨 업 완료",
            )
            await send_image(ctx, buf, "levelup.png")
            save_manager.save(self.ctx.player)
            return

        item = self.ctx.edible_items.get(item_id)
        if not item:
            await ctx.send(ansi(f"  {C.RED}✖ [{item_name}]은(는) 먹을 수 없는 아이템임미댜!{C.R}"))
            return

        self.ctx.player.remove_item(item_id)

        hp_eff = item.get("hp", 0)
        mp_eff = item.get("mp", 0)
        en_eff = item.get("en", 0)

        if hp_eff:
            self.ctx.player.hp = min(self.ctx.player.max_hp, self.ctx.player.hp + hp_eff)
        if mp_eff:
            self.ctx.player.mp = min(self.ctx.player.max_mp, self.ctx.player.mp + mp_eff)
        if en_eff:
            self.ctx.player.energy = min(self.ctx.player.max_energy, self.ctx.player.energy + en_eff)

        name = item.get("name", item_id)
        rows = []
        if hp_eff: rows.append({"label": "HP", "value": f"+{hp_eff}"})
        if mp_eff: rows.append({"label": "MP", "value": f"+{mp_eff}"})
        if en_eff: rows.append({"label": "기력", "value": f"+{en_eff}"})
        if not rows: rows.append({"label": "효과", "value": "없음"})
        buf = get_renderer().render_card(
            "아이템 섭취",
            rows=rows,
            subtitle=f"{name} 을(를) 먹었슴미댜!",
            system_key="system",
            footer="섭취 완료",
        )
        await send_image(ctx, buf, "eat.png")
        save_manager.save(self.ctx.player)

    @commands.command(name="의장장착")
    async def equip_costume_cmd(self, ctx, *, item_name: str = None):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        if not item_name:
            await send_msg_card(ctx, "의장 장착", "/의장장착 [아이템이름] 형식으로 입력하셰요!", system_key="battle", grade="Fail")
            return
        from items import ALL_ITEMS
        item_id = None
        for iid, idata in ALL_ITEMS.items():
            if idata.get("name") == item_name or iid == item_name:
                item_id = iid
                break
        if not item_id:
            await send_msg_card(ctx, "의장 장착", f"[{item_name}] 아이템을 찾을 수 없슴미댜.", system_key="battle", grade="Fail")
            return
        msg = self.ctx.player.equip_costume(item_id)
        await send_msg_card(ctx, "의장 장착", msg, system_key="battle")

    @commands.command(name="의장해제")
    async def unequip_costume_cmd(self, ctx, *, slot: str = None):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        if not slot:
            slots = "toy(장난감) / hat(모자) / outfit(의상) / shoes(신발) / accessory(악세사리)"
            await send_msg_card(ctx, "의장 해제", f"/의장해제 [슬롯] 형식으로 입력하셰요!\n슬롯: {slots}", system_key="battle", grade="Fail")
            return
        msg = self.ctx.player.unequip_costume(slot)
        await send_msg_card(ctx, "의장 해제", msg, system_key="battle")

    @commands.command(name="타이틀")
    async def title_cmd(self, ctx, *, title_name: str = None):
        if not await check_channel(ctx, self.ctx.allowed_channel_id):
            return
        from title_data import format_title_effects, get_title_desc
        from achievements import achievement_manager
        owned_titles = achievement_manager.get_unlocked_titles()
        if self.ctx.player.current_title not in owned_titles:
            owned_titles = [self.ctx.player.current_title] + owned_titles

        if not title_name:
            embed = discord.Embed(
                title="🎀 보유 타이틀 목록",
                color=EMBED_COLOR.get("status", 0x5865F2),
            )
            for t in owned_titles:
                marker = "▶ (장착중)" if t == self.ctx.player.current_title else ""
                effect_str = format_title_effects(t)
                desc_str = get_title_desc(t)
                embed.add_field(
                    name=f"{'✨ ' if marker else '  '}{t} {marker}",
                    value=f"설명: {desc_str}\n효과: **{effect_str}**",
                    inline=False,
                )
            embed.set_footer(text="/타이틀 [이름] 으로 장착!")
            await ctx.send(embed=embed)
        else:
            if title_name in owned_titles:
                self.ctx.player.current_title = title_name
                effect_str = format_title_effects(title_name)
                await ctx.send(ansi(
                    f"  {C.GREEN}✔ [{title_name}] 타이틀을 장착했슴미댜! 🎀{C.R}\n"
                    f"  효과: {effect_str}"
                ))
            else:
                await ctx.send(ansi(
                    f"  {C.RED}✖ [{title_name}] 타이틀을 보유하고 있지 않슴미댜!{C.R}"
                ))


async def setup(bot):
    await bot.add_cog(CharacterCog(bot))
