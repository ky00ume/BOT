"""job_data.py — NPC별 알바 데이터 (난이도 3단계 × 바리에이션 3개 = 9개/NPC)

알바 데이터는 data/job_data.json 에서 로드한다.

알바 유형:
  - deliver: 퀘스트 전용 아이템 수령 → 대상 NPC에게 전달
  - gather:  특정 아이템 N개 채집/제출
  - hunt:    몬스터 N마리 처치 후 보고
"""
import json
import random
from pathlib import Path

from utils.logger import setup_logger

logger = setup_logger('job_data')

_DATA_PATH = Path(__file__).parent / "data" / "job_data.json"

with _DATA_PATH.open(encoding="utf-8") as _f:
    _data = json.load(_f)

# 각 NPC별 알바 풀 (9개)
# 난이도: easy / normal / hard
# type: deliver / gather / hunt
# reward: item_id 또는 None (없으면 골드+exp만)
NPC_JOB_POOL: dict = _data["NPC_JOB_POOL"]
DIFFICULTY_LABELS: dict = _data["DIFFICULTY_LABELS"]
DIFFICULTY_ENERGY: dict = _data["DIFFICULTY_ENERGY"]

JOB_DELIVER_ITEM_IDS: set = set()
for _jobs in NPC_JOB_POOL.values():
    for _job in _jobs:
        if _job.get("type") == "deliver" and _job.get("deliver_item"):
            JOB_DELIVER_ITEM_IDS.add(_job["deliver_item"])


def _can_do_job(job: dict, player) -> bool:
    """플레이어가 gather 알바의 제작 대상을 만들 수 있는지 확인."""
    if player is None or job.get("type") != "gather":
        return True
    target_item = job.get("target_item", "")
    try:
        from crafting import CRAFTING_RECIPES, _rank_gte as craft_gte
        if target_item in CRAFTING_RECIPES:
            rank_req = CRAFTING_RECIPES[target_item].get("rank_req", "연습")
            player_rank = getattr(player, "skill_ranks", {}).get("crafting", "연습")
            return craft_gte(player_rank, rank_req)
    except Exception:
        logger.warning('job_data: crafting 랭크 확인 실패', exc_info=True)
    try:
        from metallurgy import SMELT_RECIPES, _rank_gte as smelt_gte
        for recipe in SMELT_RECIPES.values():
            if target_item in recipe.get("output", {}):
                rank_req = recipe.get("rank_req", "연습")
                player_rank = getattr(player, "skill_ranks", {}).get("metallurgy", "연습")
                return smelt_gte(player_rank, rank_req)
    except Exception:
        logger.warning('job_data: metallurgy 랭크 확인 실패', exc_info=True)
    return True


def get_random_job(npc_name: str, player=None) -> dict | None:
    """NPC의 알바 풀에서 랜덤으로 1개 반환.

    player가 전달되면 플레이어가 수행 가능한 알바만 후보로 고려합니다.
    gather 유형 알바의 target_item이 제작/제련 결과물인 경우
    플레이어의 스킬 랭크가 rank_req를 충족하지 못하면 해당 알바는 제외됩니다.
    가능한 알바가 하나도 없으면 None을 반환합니다.
    player가 None이면 기존처럼 완전 랜덤으로 동작합니다.
    """
    pool = NPC_JOB_POOL.get(npc_name, [])
    if not pool:
        return None
    if player is None:
        return random.choice(pool)
    candidates = [job for job in pool if _can_do_job(job, player)]
    if not candidates:
        return None
    return random.choice(candidates)


def get_jobs_by_difficulty(npc_name: str, player=None) -> dict:
    """NPC의 알바를 난이도별(easy/normal/hard)로 1개씩 반환.

    player가 제공되면 gather 알바의 제작 가능 여부를 체크하여
    수행 불가능한 알바를 최대한 제외합니다.
    반환 형식: {"easy": job_dict, "normal": job_dict, "hard": job_dict}
    해당 난이도 알바가 없으면 해당 키 생략.
    """
    pool = NPC_JOB_POOL.get(npc_name, [])
    if not pool:
        return {}

    by_diff: dict[str, list[dict]] = {"easy": [], "normal": [], "hard": []}
    for job in pool:
        diff = job.get("difficulty", "easy")
        if diff in by_diff:
            by_diff[diff].append(job)

    result = {}
    for diff, jobs in by_diff.items():
        if not jobs:
            continue
        feasible = [j for j in jobs if _can_do_job(j, player)]
        chosen_pool = feasible if feasible else jobs
        result[diff] = random.choice(chosen_pool)
    return result


def get_job_by_id(job_id: str) -> dict | None:
    """알바 ID로 알바 데이터 반환."""
    for jobs in NPC_JOB_POOL.values():
        for job in jobs:
            if job.get("id") == job_id:
                return job
    return None
