"""weather.py — 6시간 주기 랜덤 날씨 시스템"""
import random
from datetime import datetime
import discord

WEATHERS = [
    {"id": "clear",  "name": "맑음", "emoji": "☀️", "effects": {"fishing": +0.0, "gathering": True,  "combat_range": 0}},
    {"id": "cloudy", "name": "흐림", "emoji": "☁️", "effects": {"fishing": +0.0, "gathering": True,  "combat_range": 0}},
    {"id": "rain",   "name": "비",   "emoji": "🌧",  "effects": {"fishing": +0.2, "gathering": False, "combat_range": 0}},
    {"id": "storm",  "name": "폭풍", "emoji": "⛈",  "effects": {"fishing": None, "gathering": False, "combat_range": -2}},
    {"id": "snow",   "name": "눈",   "emoji": "❄️", "effects": {"fishing": +0.0, "gathering": True,  "combat_range": 0}},
    {"id": "fog",    "name": "안개", "emoji": "🌫️", "effects": {"fishing": +0.0, "gathering": True,  "combat_range": -2}},
]

_WEATHER_BY_ID = {w["id"]: w for w in WEATHERS}


class WeatherSystem:
    def __init__(self):
        self._current      = "clear"
        self._last_change  = None

    def update(self):
        """6시간 이상 지났으면 날씨를 교체합니다."""
        now = datetime.now()
        if self._last_change is None or (now - self._last_change).total_seconds() >= 6 * 3600:
            self._current     = random.choice(WEATHERS)["id"]
            self._last_change = now

    def get_current(self) -> dict:
        self.update()
        return _WEATHER_BY_ID.get(self._current, WEATHERS[0])

    def get_current_name(self) -> str:
        w = self.get_current()
        return f"{w['emoji']} {w['name']}"

    def can_fish(self) -> bool:
        w = self.get_current()
        return w["effects"].get("fishing") is not None

    def can_gather(self) -> bool:
        w = self.get_current()
        return bool(w["effects"].get("gathering", True))

    def fishing_bonus_rate(self) -> float:
        w   = self.get_current()
        val = w["effects"].get("fishing", 0.0)
        return float(val) if val is not None else 0.0

    def make_weather_embed(self) -> discord.Embed:
        w      = self.get_current()
        eff    = w["effects"]
        fish   = "가능 (보너스 없음)" if eff["fishing"] == 0.0 else (
                     f"가능 (확률 +{int(eff['fishing']*100)}%)" if eff["fishing"] else "불가 (폭풍)"
                 )
        gather = "가능" if eff["gathering"] else "불가"
        cr     = eff.get("combat_range", 0)
        combat = f"원거리 사거리 {cr}" if cr else "정상"

        embed = discord.Embed(
            title=f"{w['emoji']} 현재 날씨: {w['name']}",
            color=0x87ceeb,
        )
        embed.add_field(name="낚시",   value=fish,   inline=True)
        embed.add_field(name="채집",   value=gather, inline=True)
        embed.add_field(name="전투",   value=combat, inline=True)
        if self._last_change:
            embed.set_footer(text=f"마지막 업데이트: {self._last_change.strftime('%H:%M')}")
        return embed


weather_system = WeatherSystem()
