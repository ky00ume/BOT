"""bulletin.py — 마을 게시판 & 명예의전당 & 주간 낚시대회"""
import json
import os
from datetime import datetime, timedelta
import discord
from ui_theme import C, ansi, header_box, divider, EMBED_COLOR

_DIR = os.path.dirname(os.path.abspath(__file__))
BULLETIN_PATH       = os.path.join(_DIR, "bulletin.json")
WEEKLY_FISHING_PATH = os.path.join(_DIR, "weekly_fishing.json")


class BulletinBoard:
    def __init__(self):
        self.entries = []
        self.load()

    def add_entry(self, category: str, player_name: str, content: str, value=None):
        entry = {
            "category":    category,
            "player_name": player_name,
            "content":     content,
            "value":       value,
            "timestamp":   datetime.now().isoformat(),
        }
        self.entries.insert(0, entry)
        if len(self.entries) > 10:
            self.entries = self.entries[:10]
        self.save()

    def get_recent(self, count: int = 10) -> list:
        return self.entries[:count]

    def make_board_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📋 마을 게시판",
            color=EMBED_COLOR.get("npc", 0x4A7856),
        )
        recent = self.get_recent(10)
        if not recent:
            embed.description = "아직 게시물이 없슴미댜."
        else:
            lines = []
            for e in recent:
                ts   = e.get("timestamp", "")[:10]
                cat  = e.get("category",    "기타")
                pname = e.get("player_name","???")
                cont = e.get("content",     "")
                val  = e.get("value")
                val_s = f"  `{val}`" if val is not None else ""
                lines.append(f"[{ts}] **{cat}** — {pname}: {cont}{val_s}")
            embed.description = "\n".join(lines)
        embed.set_footer(text="✦ 비전 타운 게시판 ✦")
        return embed

    def make_hall_of_fame_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🏆 명예의 전당",
            description="최고 기록들이 여기에 새겨집니다!",
            color=0xffd700,
        )
        records = {}
        for e in self.entries:
            cat = e.get("category", "기타")
            val = e.get("value")
            if val is None:
                continue
            if cat not in records or val > records[cat]["value"]:
                records[cat] = e

        if not records:
            embed.description = "아직 기록이 없슴미댜."
        else:
            for cat, e in records.items():
                embed.add_field(
                    name=f"🏅 {cat}",
                    value=f"**{e['player_name']}** — {e['content']}  `{e['value']}`",
                    inline=False,
                )
        embed.set_footer(text="✦ 최고의 모험가들 ✦")
        return embed

    def save(self):
        try:
            with open(BULLETIN_PATH, "w", encoding="utf-8") as f:
                json.dump(self.entries, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load(self):
        try:
            if os.path.exists(BULLETIN_PATH):
                with open(BULLETIN_PATH, "r", encoding="utf-8") as f:
                    self.entries = json.load(f)
        except Exception:
            self.entries = []


class WeeklyFishing:
    def __init__(self):
        self.records    = []
        self.week_start = None
        self.load()
        self.reset_if_new_week()

    def add_catch(self, player_name: str, fish_name: str, size_cm: float):
        self.reset_if_new_week()
        self.records.append({
            "player_name": player_name,
            "fish_name":   fish_name,
            "size_cm":     size_cm,
            "timestamp":   datetime.now().isoformat(),
        })
        self.save()

    def get_rankings(self, top: int = 10) -> list:
        sorted_records = sorted(self.records, key=lambda r: r["size_cm"], reverse=True)
        return sorted_records[:top]

    def make_rankings_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎣 주간 낚시 대회 순위",
            color=0x1a6ba0,
        )
        rankings = self.get_rankings(10)
        if not rankings:
            embed.description = "아직 기록이 없슴미댜."
        else:
            lines = []
            medals = ["🥇", "🥈", "🥉"]
            for i, r in enumerate(rankings):
                medal = medals[i] if i < 3 else f"{i+1}."
                lines.append(
                    f"{medal} **{r['player_name']}** — {r['fish_name']} "
                    f"**{r['size_cm']:.1f}cm**"
                )
            embed.description = "\n".join(lines)

        if self.week_start:
            ws = datetime.fromisoformat(self.week_start)
            we = ws + timedelta(days=7)
            embed.set_footer(text=f"기간: {ws.strftime('%m/%d')} ~ {we.strftime('%m/%d')}")
        return embed

    def reset_if_new_week(self):
        """월요일이 되면 기록을 초기화합니다."""
        now = datetime.now()
        if self.week_start is None:
            self.week_start = (now - timedelta(days=now.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            ).isoformat()
            self.save()
            return

        ws   = datetime.fromisoformat(self.week_start)
        diff = (now - ws).total_seconds()
        if diff >= 7 * 24 * 3600:
            self.records    = []
            self.week_start = (now - timedelta(days=now.weekday())).replace(
                hour=0, minute=0, second=0, microsecond=0
            ).isoformat()
            self.save()

    def award_winner(self) -> dict:
        rankings = self.get_rankings(1)
        if not rankings:
            return {}
        winner = rankings[0]
        return {
            "player_name": winner["player_name"],
            "fish_name":   winner["fish_name"],
            "size_cm":     winner["size_cm"],
            "reward_gold": 1000,
        }

    def save(self):
        try:
            data = {"week_start": self.week_start, "records": self.records}
            with open(WEEKLY_FISHING_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load(self):
        try:
            if os.path.exists(WEEKLY_FISHING_PATH):
                with open(WEEKLY_FISHING_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.records    = data.get("records",    [])
                self.week_start = data.get("week_start", None)
        except Exception:
            self.records    = []
            self.week_start = None


bulletin_board  = BulletinBoard()
weekly_fishing  = WeeklyFishing()
