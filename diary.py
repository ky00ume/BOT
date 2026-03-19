"""diary.py — 츄라이더 일기 시스템 (매일 22시 자동 생성 + /일기 명령어)"""
import json
import os
import random
from datetime import datetime

DIARY_FILE = os.path.join(os.path.dirname(__file__), "diaries.json")
MAX_DIARY_ENTRIES = 365  # 최대 보관 일기 수 (약 1년)

# ─── 일기 템플릿 (플레이어 행동 기반) ────────────────────────────────────
_DIARY_TEMPLATES = [
    # 전투
    (
        "battles_won",
        1,
        lambda stats: (
            f"오늘은 전투를 {stats.get('battles_won', 0)}번 이겼슴미댜! "
            "막상 싸울 땐 무서웠는데 이기고 나니까 기분이 좋슴미댜~~ 💪"
        ),
    ),
    # 낚시
    (
        "fish_caught",
        1,
        lambda stats: (
            f"낚시를 해서 물고기를 {stats.get('fish_caught', 0)}마리 잡았슴미댜! "
            "찌가 움직였을 때 심장이 두근두근했슴미댜 🎣"
        ),
    ),
    # 골드
    (
        "gold_earned",
        1,
        lambda stats: (
            f"오늘 {stats.get('gold_earned', 0)}골드를 벌었슴미댜! "
            "열심히 하면 언젠간 부자가 될 것 같슴미댜~ 💰"
        ),
    ),
    # 요리
    (
        "items_cooked",
        1,
        lambda stats: (
            f"요리를 {stats.get('items_cooked', 0)}번 했슴미댜! "
            "맛있는 걸 만들 때 제일 행복한 것 같슴미댜 🍳"
        ),
    ),
    # 쓰다듬
    (
        "pet_count",
        1,
        lambda stats: (
            f"오늘 {stats.get('pet_count', 0)}번이나 쓰다듬어 주셨슴미댜!! "
            "기분이 너무너무 좋슴미댜~ 히히 🕷️💕"
        ),
    ),
    # 스킬 랭크업
    (
        "skill_rankups",
        1,
        lambda stats: (
            f"스킬이 {stats.get('skill_rankups', 0)}번이나 올랐슴미댜! "
            "연습은 배신하지 않는다는 걸 알았슴미댜 ✨"
        ),
    ),
]

# ─── 기본 일기 (특별한 일이 없을 때) ─────────────────────────────────────
_DEFAULT_DIARY_ENTRIES = [
    "오늘은 특별한 일이 없었슴미댜. 그냥 마을을 산책하고, 거미줄을 다듬고, 맛있는 걸 먹었슴미댜. 평화로운 하루였슴미댜~ 🕸️",
    "오늘은 구름을 구경하며 쉬었슴미댜. 구름이 거미처럼 생긴 것도 있었슴미댜! 거짓말이 아님미댜~ 🌤️",
    "오늘은 도서관에서 책을 읽었슴미댜. 모험가의 일대기를 읽었는데 언젠가 저도 그렇게 될 것 같슴미댜! ✨",
    "오늘은 강가에서 돌멩이를 던지며 놀았슴미댜. 물수제비를 8번이나 튕겼슴미댜!! (다리가 8개라 그런가요...?)",
    "오늘은 마을 장인아저씨한테 망치 다루는 법을 조금 배웠슴미댜. 어렵지만 재미있슴미댜 ⚒️",
]

_DIARY_ART = (
    "```\n"
    "   📖 ✨ 오늘의 일기 ✨ 📖\n"
    "     🕷️ 쓰는 중...\n"
    "  ═══════🕸️═══════\n"
    "```"
)


class DiaryManager:
    def __init__(self, player=None):
        self.player = player
        self._daily_stats: dict = {}

    def set_player(self, player):
        self.player = player

    def increment(self, key: str, amount: int = 1):
        """하루 통계 카운터 증가"""
        self._daily_stats[key] = self._daily_stats.get(key, 0) + amount

    def _load_diaries(self) -> list:
        if not os.path.isfile(DIARY_FILE):
            return []
        try:
            with open(DIARY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_diaries(self, entries: list):
        try:
            with open(DIARY_FILE, "w", encoding="utf-8") as f:
                json.dump(entries, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _generate_entry_text(self) -> str:
        stats = self._daily_stats
        triggered = []
        for key, threshold, fn in _DIARY_TEMPLATES:
            if stats.get(key, 0) >= threshold:
                triggered.append(fn(stats))

        if triggered:
            random.shuffle(triggered)
            body = "  ".join(triggered[:2])
        else:
            body = random.choice(_DEFAULT_DIARY_ENTRIES)

        date_str = datetime.now().strftime("%Y년 %m월 %d일")
        return f"{date_str} 일기\n\n{body}"

    async def write_and_send(self, channel):
        """일기를 생성하고 채널에 전송한 뒤 파일에 저장합니다."""
        content = self._generate_entry_text()
        date_str = datetime.now().strftime("%Y-%m-%d")

        entries = self._load_diaries()
        entries.append({"date": date_str, "content": content})
        # 최대 MAX_DIARY_ENTRIES개 보관
        if len(entries) > MAX_DIARY_ENTRIES:
            entries = entries[-MAX_DIARY_ENTRIES:]
        self._save_diaries(entries)

        # 채널에 전송
        await channel.send(
            f"{_DIARY_ART}\n"
            f"**{content}**\n\n"
            f"🕷️ 츄라이더의 오늘 일기가 완성됐슴미댜! 📖✨"
        )

        # 하루치 통계 초기화
        self._daily_stats = {}

    def get_diary_list(self, page: int = 0, per_page: int = 5) -> str:
        """저장된 일기 목록을 반환합니다."""
        from ui_theme import C, ansi, header_box, divider
        entries = self._load_diaries()
        if not entries:
            return ansi(f"  {C.DARK}아직 일기가 없슴미댜...{C.R}")

        # 최신순 정렬
        entries = list(reversed(entries))
        start = page * per_page
        page_entries = entries[start:start + per_page]

        lines = [header_box("📖 츄라이더 일기")]
        for e in page_entries:
            lines.append(f"  {C.GOLD}[{e['date']}]{C.R}")
            # 내용이 길면 첫 줄만 표시
            preview = e.get("content", "").splitlines()[0] if e.get("content") else ""
            if len(preview) > 40:
                preview = preview[:40] + "..."
            lines.append(f"  {C.WHITE}{preview}{C.R}")
            lines.append(divider())

        total_pages = (len(entries) + per_page - 1) // per_page
        lines.append(f"  {C.DARK}페이지 {page + 1}/{total_pages}{C.R}")
        return ansi("\n".join(lines))

    def get_diary_detail(self, date_str: str) -> str:
        """특정 날짜의 일기 전문을 반환합니다."""
        from ui_theme import C, ansi, header_box, divider
        entries = self._load_diaries()
        for e in entries:
            if e.get("date") == date_str:
                lines = [
                    header_box(f"📖 {date_str} 일기"),
                    f"  {C.WHITE}{e.get('content', '')}{C.R}",
                    divider(),
                ]
                return ansi("\n".join(lines))
        return ansi(f"  {C.RED}✖ [{date_str}] 날짜의 일기를 찾을 수 없슴미댜!{C.R}")


# 싱글턴 인스턴스
diary_manager = DiaryManager()
