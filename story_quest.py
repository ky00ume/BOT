"""story_quest.py — 스토리 퀘스트 엔진 (챕터 1~3)"""
import datetime
try:
    import pytz
except ImportError:
    pytz = None


class StoryQuestManager:
    """챕터 1~3 스토리 퀘스트 진행을 관리하는 클래스."""

    def __init__(self, player):
        self.player      = player
        self.chapter     = 1        # 현재 챕터 (1~3, 4는 미해금)
        self.quest       = 1        # 현재 퀘스트 번호
        self.shadow_sync = 0        # 히든 스탯 (-100 ~ +100)
        self.hints       = []       # 수집한 힌트 목록
        self.flags       = {}       # 스토리 플래그 딕셔너리
        self.quest_log   = []       # 완료된 퀘스트 기록

    # ─── shadow_sync 암시 텍스트 ──────────────────────────────────────────

    def get_shadow_hint(self, shadow_sync: int = None) -> str:
        """shadow_sync 수치를 수치 비공개 텍스트로 암시합니다."""
        v = shadow_sync if shadow_sync is not None else self.shadow_sync
        if v >= 40:
            return "그림자가 당신을 감싸안듯 짙게 드리워져 있습니다."
        elif v >= 20:
            return "그림자가 평소보다 조금 더 짙어 보입니다."
        elif v >= 5:
            return "그림자가 미세하게 흔들리고 있습니다."
        elif v >= -5:
            return "그림자가 평온하게 발밑에 머물러 있습니다."
        elif v >= -20:
            return "그림자의 끝자락이 희미하게 빛나는 듯합니다."
        elif v >= -40:
            return "그림자가 얇아지고, 그 너머로 무언가 비치는 듯합니다."
        else:
            return "그림자가 거의 투명해졌습니다. 빛이 당신을 관통합니다."

    # ─── 게임 내 시간 (KST 기준) ──────────────────────────────────────────

    def get_game_time(self) -> str:
        """실제 시간(KST) 기반 낮/밤 판단. 6~18시: day, 그 외: night."""
        try:
            kst = pytz.timezone("Asia/Seoul")
            now = datetime.datetime.now(kst)
            hour = now.hour
        except Exception:
            # pytz 미설치 시 UTC 폴백
            now = datetime.datetime.utcnow()
            hour = (now.hour + 9) % 24
        return "day" if 6 <= hour < 18 else "night"

    def get_embed_theme(self, game_time: str = None) -> int:
        """시간대별 임베드 테마 색상을 반환합니다."""
        t = game_time if game_time is not None else self.get_game_time()
        if t == "night":
            return 0x1a0033  # 어두운 보라
        return 0xf5deb3      # 밝은 베이지

    # ─── 퀘스트 진행 헬퍼 ─────────────────────────────────────────────────

    def is_quest_done(self, chapter: int, quest: int) -> bool:
        """특정 챕터·퀘스트가 완료됐는지 확인합니다."""
        return f"ch{chapter}_q{quest}" in self.quest_log

    def complete_quest(self, chapter: int, quest: int):
        """퀘스트를 완료 기록합니다."""
        key = f"ch{chapter}_q{quest}"
        if key not in self.quest_log:
            self.quest_log.append(key)

    def add_hint(self, hint: str):
        """힌트를 추가합니다 (중복 방지)."""
        if hint not in self.hints:
            self.hints.append(hint)

    def add_shadow_sync(self, delta: int):
        """shadow_sync를 변경하고 -100~+100 범위 내로 유지합니다."""
        self.shadow_sync = max(-100, min(100, self.shadow_sync + delta))

    # ─── 직렬화/역직렬화 ──────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """세이브 시스템 호환 직렬화."""
        return {
            "chapter":     self.chapter,
            "quest":       self.quest,
            "shadow_sync": self.shadow_sync,
            "hints":       list(self.hints),
            "flags":       dict(self.flags),
            "quest_log":   list(self.quest_log),
        }

    def from_dict(self, data: dict):
        """세이브 데이터로부터 복원."""
        self.chapter     = data.get("chapter",     1)
        self.quest       = data.get("quest",       1)
        self.shadow_sync = data.get("shadow_sync", 0)
        hints = data.get("hints", [])
        self.hints       = list(hints) if isinstance(hints, list) else []
        flags = data.get("flags", {})
        self.flags       = dict(flags) if isinstance(flags, dict) else {}
        log = data.get("quest_log", [])
        self.quest_log   = list(log) if isinstance(log, list) else []
