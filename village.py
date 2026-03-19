"""village.py — 마을 레벨 & 기여도 & 랜덤 이벤트"""
import asyncio
import random
import json
import discord
from ui_theme import C, ansi, header_box, divider, EMBED_COLOR

VILLAGE_LEVEL_THRESHOLDS = [0, 500, 1200, 2500, 4500, 7500, 12000]

VILLAGE_LEVEL_BUFFS = {
    1: {"label": "기본 마을",       "job_bonus_pct": 0,  "drop_bonus_pct": 0,  "cooking_quality": 0},
    2: {"label": "성장하는 마을",   "job_bonus_pct": 10, "drop_bonus_pct": 5,  "cooking_quality": 0},
    3: {"label": "번영하는 마을",   "job_bonus_pct": 15, "drop_bonus_pct": 8,  "cooking_quality": 1},
    4: {"label": "부유한 마을",     "job_bonus_pct": 20, "drop_bonus_pct": 12, "cooking_quality": 1},
    5: {"label": "전설의 마을",     "job_bonus_pct": 30, "drop_bonus_pct": 20, "cooking_quality": 2},
}

CONTRIBUTION_AMOUNTS = {
    "job": 5, "battle": 3, "cooking": 2, "fishing": 1, "smelting": 4, "gathering": 2
}

RANDOM_EVENTS = [
    {"id": "merchant",  "emoji": "🛒", "name": "수상한 상인 방문",  "effect": "당일만 특가 아이템 판매!",     "type": "bonus"},
    {"id": "monster",   "emoji": "👹", "name": "몬스터 습격!",      "effect": "마을 기여도 -50pt",            "type": "penalty", "contrib_delta": -50},
    {"id": "lucky_day", "emoji": "🍀", "name": "행운의 날",          "effect": "드랍률 2배, 낚시 희귀어 2배!", "type": "bonus"},
    {"id": "storm",     "emoji": "🌧", "name": "폭풍",              "effect": "낚시·채집 불가, 실내 알바 +50%","type": "mixed"},
    {"id": "festival",  "emoji": "🎪", "name": "축제의 날",          "effect": "모든 보상 1.5배!",             "type": "bonus"},
]


class VillageManager:
    def __init__(self, channel_id=None):
        self.contribution  = 0
        self.level         = 1
        self.active_event  = None
        self.channel_id    = channel_id

    def add_contribution(self, amount: int, activity_type: str = None) -> tuple:
        """기여도 추가. (new_total, leveled_up, new_level) 반환."""
        if activity_type:
            amount = CONTRIBUTION_AMOUNTS.get(activity_type, amount)
        self.contribution += amount
        old_level = self.level
        self.level = self.get_level()
        leveled_up = self.level > old_level
        return (self.contribution, leveled_up, self.level)

    def get_level(self) -> int:
        lv = 1
        for i, threshold in enumerate(VILLAGE_LEVEL_THRESHOLDS):
            if self.contribution >= threshold:
                lv = i + 1
        return min(lv, len(VILLAGE_LEVEL_BUFFS))

    def get_current_buffs(self) -> dict:
        return VILLAGE_LEVEL_BUFFS.get(self.level, VILLAGE_LEVEL_BUFFS[1])

    def to_dict(self) -> dict:
        return {
            "contribution": self.contribution,
            "level":        self.level,
            "active_event": self.active_event,
            "channel_id":   self.channel_id,
        }

    def from_dict(self, data: dict):
        self.contribution = data.get("contribution", 0)
        self.level        = data.get("level",        1)
        self.active_event = data.get("active_event", None)
        self.channel_id   = data.get("channel_id",   self.channel_id)
        return self

    async def trigger_random_event(self, bot, channel_id: int = None):
        event = random.choice(RANDOM_EVENTS)

        if event.get("type") == "penalty":
            delta = event.get("contrib_delta", 0)
            self.contribution = max(0, self.contribution + delta)
            self.level = self.get_level()

        self.active_event = event

        target_ch = channel_id or self.channel_id
        if target_ch:
            ch = bot.get_channel(target_ch)
            if ch:
                color = {"bonus": 0x00cc66, "penalty": 0xcc2200, "mixed": 0xccaa00}.get(
                    event.get("type"), 0x7777aa
                )
                embed = discord.Embed(
                    title=f"{event['emoji']} 마을 이벤트: {event['name']}",
                    description=event["effect"],
                    color=color,
                )
                embed.set_footer(text="비전 타운 이벤트 시스템")
                await ch.send(embed=embed)

        return event

    def make_status_embed(self) -> discord.Embed:
        buffs = self.get_current_buffs()
        max_lv = len(VILLAGE_LEVEL_BUFFS)
        next_thresh = VILLAGE_LEVEL_THRESHOLDS[self.level] if self.level < max_lv else None

        embed = discord.Embed(
            title="🏘 비전 타운 마을 상태",
            color=EMBED_COLOR.get("npc", 0x4A7856),
        )
        embed.add_field(
            name="마을 레벨",
            value=f"**Lv.{self.level}** — {buffs['label']}",
            inline=True,
        )
        embed.add_field(
            name="기여도",
            value=(
                f"{self.contribution:,} pt"
                + (f"  (다음 레벨: {next_thresh:,})" if next_thresh else "  (최고 레벨!)")
            ),
            inline=True,
        )
        embed.add_field(
            name="마을 버프",
            value=(
                f"알바 보너스: +{buffs['job_bonus_pct']}%\n"
                f"드랍 보너스: +{buffs['drop_bonus_pct']}%\n"
                f"요리 품질: +{buffs['cooking_quality']}"
            ),
            inline=False,
        )
        if self.active_event:
            ev = self.active_event
            embed.add_field(
                name=f"{ev['emoji']} 현재 이벤트",
                value=f"**{ev['name']}**\n{ev['effect']}",
                inline=False,
            )
        embed.set_footer(text="✦ 마을에 기여하면 모두에게 버프가! ✦")
        return embed


village_manager = VillageManager()
