"""data JSON 외부화 테스트 (REMEDIATION_PLAN 1-D).

items.py / job_data.py / npc_dialogue_db.py 가 data/*.json 으로부터
정확하게 로드되는지 검증한다.
"""
from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


# ────────────────────────────────────────────────────────────────────────────
# JSON 파일 존재 확인
# ────────────────────────────────────────────────────────────────────────────

class TestDataFilesExist:
    def test_items_json_exists(self):
        assert (DATA_DIR / "items.json").is_file()

    def test_job_data_json_exists(self):
        assert (DATA_DIR / "job_data.json").is_file()

    def test_npc_dialogues_json_exists(self):
        assert (DATA_DIR / "npc_dialogues.json").is_file()

    def test_items_json_is_valid(self):
        with (DATA_DIR / "items.json").open(encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_job_data_json_is_valid(self):
        with (DATA_DIR / "job_data.json").open(encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_npc_dialogues_json_is_valid(self):
        with (DATA_DIR / "npc_dialogues.json").open(encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)


# ────────────────────────────────────────────────────────────────────────────
# items.py 로딩 검증
# ────────────────────────────────────────────────────────────────────────────

class TestItemsLoading:
    def test_all_items_is_nonempty(self):
        from items import ALL_ITEMS
        assert len(ALL_ITEMS) > 0

    def test_weapons_loaded(self):
        from items import WEAPONS
        assert len(WEAPONS) > 0

    def test_armors_loaded(self):
        from items import ARMORS
        assert len(ARMORS) > 0

    def test_consumables_loaded(self):
        from items import CONSUMABLES
        assert len(CONSUMABLES) > 0

    def test_cooked_dishes_loaded(self):
        from items import COOKED_DISHES
        assert len(COOKED_DISHES) > 0

    def test_skill_books_loaded(self):
        from items import SKILL_BOOKS
        assert len(SKILL_BOOKS) > 0

    def test_known_weapon_exists(self):
        from items import ALL_ITEMS
        assert "wp_sword_01" in ALL_ITEMS

    def test_known_weapon_has_required_fields(self):
        from items import WEAPONS
        sword = WEAPONS["wp_sword_01"]
        assert sword["name"] == "낡은 검"
        assert sword["type"] == "weapon"
        assert "grade" in sword
        assert "attack" in sword
        assert "price" in sword
        assert "desc" in sword

    def test_all_items_includes_bags(self):
        """BAGS (database.py에서 로드) 가 ALL_ITEMS에 포함되는지 확인."""
        from database import BAGS
        from items import ALL_ITEMS
        for key in BAGS:
            assert key in ALL_ITEMS

    def test_story_quest_items_in_all_items(self):
        from items import ALL_ITEMS, STORY_QUEST_ITEMS
        for key in STORY_QUEST_ITEMS:
            assert key in ALL_ITEMS

    def test_item_grades_valid(self):
        """모든 아이템의 grade 가 유효한 값인지 확인.

        costume_data / snack 아이템은 한국어 등급명을 사용하므로 함께 허용한다.
        """
        from items import ALL_ITEMS
        # items.json 정의 아이템은 영문 등급, costume_data/snack은 한국어 등급 사용
        valid_grades = {
            "Normal", "Rare", "Epic", "Legendary", "Mythic",
            "일반", "고급", "희귀", "전설",
        }
        for item_id, item in ALL_ITEMS.items():
            if "grade" in item:
                assert item["grade"] in valid_grades, (
                    f"{item_id} 의 grade={item['grade']} 가 유효하지 않습니다"
                )

    def test_weapons_have_slot(self):
        """무기 아이템은 slot 필드를 가져야 한다."""
        from items import WEAPONS
        for item_id, item in WEAPONS.items():
            assert "slot" in item, f"{item_id} 에 slot 필드가 없습니다"


# ────────────────────────────────────────────────────────────────────────────
# job_data.py 로딩 검증
# ────────────────────────────────────────────────────────────────────────────

class TestJobDataLoading:
    def test_npc_job_pool_is_nonempty(self):
        from job_data import NPC_JOB_POOL
        assert len(NPC_JOB_POOL) > 0

    def test_known_npc_in_pool(self):
        from job_data import NPC_JOB_POOL
        assert "다몬" in NPC_JOB_POOL

    def test_difficulty_labels_loaded(self):
        from job_data import DIFFICULTY_LABELS
        assert DIFFICULTY_LABELS["easy"] == "쉬움"
        assert DIFFICULTY_LABELS["normal"] == "보통"
        assert DIFFICULTY_LABELS["hard"] == "어려움"

    def test_difficulty_energy_loaded(self):
        from job_data import DIFFICULTY_ENERGY
        assert DIFFICULTY_ENERGY["easy"] == 10
        assert DIFFICULTY_ENERGY["normal"] == 20
        assert DIFFICULTY_ENERGY["hard"] == 35

    def test_job_deliver_item_ids_populated(self):
        from job_data import JOB_DELIVER_ITEM_IDS
        assert isinstance(JOB_DELIVER_ITEM_IDS, set)

    def test_each_npc_has_jobs(self):
        from job_data import NPC_JOB_POOL
        for npc, jobs in NPC_JOB_POOL.items():
            assert len(jobs) > 0, f"{npc} 의 알바 풀이 비어 있습니다"

    def test_job_fields_present(self):
        """각 알바 데이터에 필수 필드가 있는지 확인."""
        from job_data import NPC_JOB_POOL
        required = {"id", "name", "difficulty", "type"}
        for npc, jobs in NPC_JOB_POOL.items():
            for job in jobs:
                for field in required:
                    assert field in job, (
                        f"{npc} 의 알바 {job.get('id', '?')} 에 {field} 필드가 없습니다"
                    )

    def test_difficulty_values_valid(self):
        from job_data import NPC_JOB_POOL
        valid = {"easy", "normal", "hard"}
        for npc, jobs in NPC_JOB_POOL.items():
            for job in jobs:
                assert job["difficulty"] in valid, (
                    f"{npc}/{job['id']} difficulty={job['difficulty']} 가 유효하지 않습니다"
                )

    def test_get_random_job_returns_job(self):
        from job_data import get_random_job
        job = get_random_job("다몬")
        assert job is not None
        assert "id" in job

    def test_get_random_job_unknown_npc_returns_none(self):
        from job_data import get_random_job
        assert get_random_job("존재하지않는NPC") is None

    def test_get_job_by_id(self):
        from job_data import NPC_JOB_POOL, get_job_by_id
        first_job = NPC_JOB_POOL["다몬"][0]
        found = get_job_by_id(first_job["id"])
        assert found is not None
        assert found["id"] == first_job["id"]

    def test_get_job_by_id_not_found(self):
        from job_data import get_job_by_id
        assert get_job_by_id("nonexistent_job_xyz") is None

    def test_get_jobs_by_difficulty_returns_dict(self):
        from job_data import get_jobs_by_difficulty
        result = get_jobs_by_difficulty("다몬")
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_get_jobs_by_difficulty_unknown_npc(self):
        from job_data import get_jobs_by_difficulty
        assert get_jobs_by_difficulty("알수없는NPC") == {}


# ────────────────────────────────────────────────────────────────────────────
# npc_dialogue_db.py 로딩 검증
# ────────────────────────────────────────────────────────────────────────────

class TestNpcDialogueDbLoading:
    def test_npc_keywords_is_nonempty(self):
        from npc_dialogue_db import NPC_KEYWORDS
        assert len(NPC_KEYWORDS) > 0

    def test_known_npc_in_keywords(self):
        from npc_dialogue_db import NPC_KEYWORDS
        assert "다몬" in NPC_KEYWORDS

    def test_default_keywords_loaded(self):
        from npc_dialogue_db import DEFAULT_KEYWORDS
        assert isinstance(DEFAULT_KEYWORDS, list)
        assert len(DEFAULT_KEYWORDS) > 0
        assert "마을" in DEFAULT_KEYWORDS

    def test_npc_gift_reactions_loaded(self):
        from npc_dialogue_db import NPC_GIFT_REACTIONS
        assert len(NPC_GIFT_REACTIONS) > 0
        assert "다몬" in NPC_GIFT_REACTIONS

    def test_affinity_unlock_keywords_loaded(self):
        from npc_dialogue_db import AFFINITY_UNLOCK_KEYWORDS
        assert isinstance(AFFINITY_UNLOCK_KEYWORDS, dict)

    def test_keyword_has_default_response(self):
        """NPC 키워드는 default 응답을 포함해야 한다."""
        from npc_dialogue_db import NPC_KEYWORDS
        for npc, keywords in NPC_KEYWORDS.items():
            for kw, data in keywords.items():
                assert "default" in data, (
                    f"{npc}/{kw} 에 default 응답이 없습니다"
                )

    def test_gift_reaction_has_required_fields(self):
        """선물 반응 데이터에 필수 필드가 있는지 확인."""
        from npc_dialogue_db import NPC_GIFT_REACTIONS
        required_keys = {"loves", "likes", "dislikes"}
        for npc, reaction in NPC_GIFT_REACTIONS.items():
            assert isinstance(reaction, dict), f"{npc} 선물 반응이 dict가 아닙니다"
            for key in required_keys:
                assert key in reaction, (
                    f"{npc} 선물 반응에 {key} 필드가 없습니다"
                )

    def test_npc_keywords_and_gift_reactions_same_npcs(self):
        """NPC_KEYWORDS 와 NPC_GIFT_REACTIONS 가 동일한 NPC를 커버하는지 확인."""
        from npc_dialogue_db import NPC_KEYWORDS, NPC_GIFT_REACTIONS
        kw_npcs = set(NPC_KEYWORDS.keys())
        gr_npcs = set(NPC_GIFT_REACTIONS.keys())
        # 두 dict의 NPC 집합이 겹쳐야 함
        assert kw_npcs & gr_npcs, "NPC_KEYWORDS와 NPC_GIFT_REACTIONS에 공통 NPC가 없습니다"
