"""npc_dialogue_db.py — NPC 키워드 대화 DB 및 선물 반응 대사

데이터는 data/npc_dialogues.json 에서 로드한다.
"""
import json
from pathlib import Path

_DATA_PATH = Path(__file__).parent / "data" / "npc_dialogues.json"

with _DATA_PATH.open(encoding="utf-8") as _f:
    _data = json.load(_f)

# ───────────────────────────────────────────────
# NPC 키워드-응답 맵
# 구조:
#   NPC_KEYWORDS[npc_name][keyword] = {
#       "default": "기본 응답",
#       "지인": "지인 단계 이상일 때 응답",
#       "친구": "친구 단계 이상일 때 응답",
#       "절친": "절친 단계 이상일 때 응답",
#       "영혼의 동반자": "영혼의 동반자 단계 응답",
#       "unlock_keyword": "이 대화 시 해금되는 키워드 (str 또는 list)",
#       "required_keyword": "이 키워드 접근에 필요한 선행 키워드 (str 또는 list)",
#       "affinity_points": 대화 시 호감도 증가량 (기본 2),
#   }
# ───────────────────────────────────────────────

NPC_KEYWORDS: dict = _data["NPC_KEYWORDS"]
NPC_GIFT_REACTIONS: dict = _data["NPC_GIFT_REACTIONS"]
AFFINITY_UNLOCK_KEYWORDS: dict = _data["AFFINITY_UNLOCK_KEYWORDS"]
DEFAULT_KEYWORDS: list = _data["DEFAULT_KEYWORDS"]
