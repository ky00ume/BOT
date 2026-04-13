"""tests/test_quest.py — QuestManager 단위 테스트"""
import pytest


# ── helpers ─────────────────────────────────────────────────────────────────

def _first_quest_of_type(qtype: str):
    from quest import QUEST_DB
    for qid, q in QUEST_DB.items():
        if q["type"] == qtype:
            return qid, q
    pytest.skip(f"QUEST_DB에 '{qtype}' 타입 퀘스트 없음")


# ── list_quests ──────────────────────────────────────────────────────────────

class TestListQuests:
    def test_returns_string(self, quest_manager):
        result = quest_manager.list_quests()
        assert isinstance(result, str)

    def test_shows_available_quests(self, quest_manager):
        from quest import QUEST_DB
        result = quest_manager.list_quests()
        first_qid = next(iter(QUEST_DB))
        assert first_qid in result

    def test_shows_active_quest(self, quest_manager):
        qid = next(iter(
            qid for qid, q in __import__('quest').QUEST_DB.items()
            if q['type'] == 'kill'
        ))
        quest_manager.accept_quest(qid)
        result = quest_manager.list_quests()
        assert "진행 중" in result

    def test_shows_completed_quest(self, quest_manager):
        from quest import QUEST_DB
        # kill 퀘스트 중 easy 하나 완료시키기
        qid, q = _first_quest_of_type("kill")
        quest_manager.accept_quest(qid)
        # 충분한 kill progress 부여
        quest_manager.active_quests[qid]["progress"] = q.get("target_count", 1)
        quest_manager.complete_quest(qid)
        result = quest_manager.list_quests()
        assert "완료됨" in result


# ── accept_quest ─────────────────────────────────────────────────────────────

class TestAcceptQuest:
    def test_accept_valid_quest(self, quest_manager):
        qid = next(iter(__import__('quest').QUEST_DB))
        result = quest_manager.accept_quest(qid)
        assert qid in quest_manager.active_quests
        assert "수락" in result

    def test_reject_nonexistent_quest(self, quest_manager):
        result = quest_manager.accept_quest("nonexistent_quest_id")
        assert "존재하지 않는" in result

    def test_reject_already_completed_quest(self, quest_manager):
        qid, q = _first_quest_of_type("kill")
        quest_manager.accept_quest(qid)
        quest_manager.active_quests[qid]["progress"] = q.get("target_count", 1)
        quest_manager.complete_quest(qid)
        result = quest_manager.accept_quest(qid)
        assert "이미 완료" in result

    def test_reject_already_active_quest(self, quest_manager):
        qid = next(iter(__import__('quest').QUEST_DB))
        quest_manager.accept_quest(qid)
        result = quest_manager.accept_quest(qid)
        assert "이미 진행 중" in result

    def test_deliver_quest_gives_quest_item(self, quest_manager):
        qid, q = _first_quest_of_type("deliver")
        quest_item = q.get("quest_item")
        quest_manager.accept_quest(qid)
        if quest_item:
            assert quest_manager.player.inventory.get(quest_item, 0) >= 1


# ── complete_quest ───────────────────────────────────────────────────────────

class TestCompleteQuest:
    def test_collect_success(self, quest_manager):
        qid, q = _first_quest_of_type("collect")
        quest_manager.accept_quest(qid)
        item_id = q["target_item"]
        count = q["target_count"]
        quest_manager.player.inventory[item_id] = count
        result = quest_manager.complete_quest(qid)
        assert "완료" in result
        assert qid in quest_manager.completed_quests

    def test_collect_insufficient_items(self, quest_manager):
        qid, q = _first_quest_of_type("collect")
        quest_manager.accept_quest(qid)
        quest_manager.player.inventory[q["target_item"]] = 0
        result = quest_manager.complete_quest(qid)
        assert "필요" in result or "부족" in result
        assert qid not in quest_manager.completed_quests

    def test_kill_success(self, quest_manager):
        qid, q = _first_quest_of_type("kill")
        quest_manager.accept_quest(qid)
        quest_manager.active_quests[qid]["progress"] = q.get("target_count", 1)
        result = quest_manager.complete_quest(qid)
        assert "완료" in result
        assert qid in quest_manager.completed_quests

    def test_kill_insufficient_progress(self, quest_manager):
        qid, q = _first_quest_of_type("kill")
        quest_manager.accept_quest(qid)
        quest_manager.active_quests[qid]["progress"] = 0
        result = quest_manager.complete_quest(qid)
        assert "목표" in result or "달성" in result
        assert qid not in quest_manager.completed_quests

    def test_deliver_success(self, quest_manager):
        qid, q = _first_quest_of_type("deliver")
        quest_manager.accept_quest(qid)
        quest_manager.active_quests[qid]["delivered"] = True
        result = quest_manager.complete_quest(qid)
        assert "완료" in result
        assert qid in quest_manager.completed_quests

    def test_deliver_not_delivered_yet(self, quest_manager):
        qid, q = _first_quest_of_type("deliver")
        quest_manager.accept_quest(qid)
        quest_manager.active_quests[qid]["delivered"] = False
        result = quest_manager.complete_quest(qid)
        assert "전달" in result
        assert qid not in quest_manager.completed_quests

    def test_complete_nonexistent_quest(self, quest_manager):
        result = quest_manager.complete_quest("nonexistent_id")
        assert "존재하지 않는" in result

    def test_complete_not_accepted_quest(self, quest_manager):
        qid = next(iter(__import__('quest').QUEST_DB))
        result = quest_manager.complete_quest(qid)
        assert "수락하지 않은" in result

    def test_reward_gold_added(self, quest_manager):
        qid, q = _first_quest_of_type("kill")
        quest_manager.accept_quest(qid)
        quest_manager.active_quests[qid]["progress"] = q.get("target_count", 1)
        gold_before = quest_manager.player.gold
        quest_manager.complete_quest(qid)
        assert quest_manager.player.gold == gold_before + q["reward_gold"]


# ── abandon_quest ────────────────────────────────────────────────────────────

class TestAbandonQuest:
    def test_abandon_active_quest(self, quest_manager):
        qid = next(iter(__import__('quest').QUEST_DB))
        quest_manager.accept_quest(qid)
        result = quest_manager.abandon_quest(qid)
        assert qid not in quest_manager.active_quests
        assert qid in quest_manager.failed_quests
        assert "포기" in result

    def test_abandon_non_active_quest(self, quest_manager):
        result = quest_manager.abandon_quest("some_nonactive_quest")
        assert "진행 중인 퀘스트" in result

    def test_abandon_deliver_removes_quest_item(self, quest_manager):
        qid, q = _first_quest_of_type("deliver")
        quest_item = q.get("quest_item")
        quest_manager.accept_quest(qid)
        if quest_item:
            assert quest_manager.player.inventory.get(quest_item, 0) >= 1
        quest_manager.abandon_quest(qid)
        if quest_item:
            assert quest_manager.player.inventory.get(quest_item, 0) == 0


# ── update_kill_count ────────────────────────────────────────────────────────

class TestUpdateKillCount:
    def test_kill_count_increases(self, quest_manager):
        qid, q = _first_quest_of_type("kill")
        quest_manager.accept_quest(qid)
        zone = q.get("target_zone")
        quest_manager.update_kill_count(count=1, zone=zone)
        assert quest_manager.active_quests[qid]["progress"] == 1

    def test_kill_count_capped_at_target(self, quest_manager):
        qid, q = _first_quest_of_type("kill")
        quest_manager.accept_quest(qid)
        target = q.get("target_count", 1)
        zone = q.get("target_zone")
        quest_manager.update_kill_count(count=target + 10, zone=zone)
        assert quest_manager.active_quests[qid]["progress"] == target

    def test_kill_count_filtered_by_zone(self, quest_manager):
        qid, q = _first_quest_of_type("kill")
        quest_manager.accept_quest(qid)
        required_zone = q.get("target_zone")
        if not required_zone:
            pytest.skip("target_zone이 없는 퀘스트")
        quest_manager.update_kill_count(count=1, zone="완전히다른지역")
        assert quest_manager.active_quests[qid]["progress"] == 0


# ── update_collect_count ─────────────────────────────────────────────────────

class TestUpdateCollectCount:
    def test_collect_count_increases(self, quest_manager):
        qid, q = _first_quest_of_type("collect")
        quest_manager.accept_quest(qid)
        item_id = q["target_item"]
        quest_manager.update_collect_count(item_id=item_id, count=1)
        assert quest_manager.active_quests[qid]["progress"] == 1

    def test_collect_count_wrong_item_ignored(self, quest_manager):
        qid, q = _first_quest_of_type("collect")
        quest_manager.accept_quest(qid)
        quest_manager.update_collect_count(item_id="wrong_item_id", count=5)
        assert quest_manager.active_quests[qid]["progress"] == 0


# ── deliver_to_npc ───────────────────────────────────────────────────────────

class TestDeliverToNpc:
    def test_deliver_marks_delivered(self, quest_manager):
        qid, q = _first_quest_of_type("deliver")
        quest_manager.accept_quest(qid)
        deliver_to = q["deliver_to"]
        result = quest_manager.deliver_to_npc(deliver_to)
        assert quest_manager.active_quests[qid]["delivered"] is True
        assert "전달 완료" in result

    def test_deliver_wrong_npc_does_nothing(self, quest_manager):
        qid, q = _first_quest_of_type("deliver")
        quest_manager.accept_quest(qid)
        result = quest_manager.deliver_to_npc("존재하지않는NPC")
        assert result == ""
        assert quest_manager.active_quests[qid]["delivered"] is False


# ── to_dict / from_dict ──────────────────────────────────────────────────────

class TestSerialization:
    def test_roundtrip(self, quest_manager, fresh_player):
        qid, q = _first_quest_of_type("kill")
        quest_manager.accept_quest(qid)
        quest_manager.active_quests[qid]["progress"] = 3
        quest_manager.completed_quests.add("fake_done_id")
        quest_manager.failed_quests.add("fake_failed_id")

        data = quest_manager.to_dict()

        from quest import QuestManager
        qm2 = QuestManager(fresh_player)
        qm2.from_dict(data)

        assert qm2.active_quests == quest_manager.active_quests
        assert qm2.completed_quests == quest_manager.completed_quests
        assert qm2.failed_quests == quest_manager.failed_quests

    def test_to_dict_structure(self, quest_manager):
        data = quest_manager.to_dict()
        assert "active_quests" in data
        assert "completed_quests" in data
        assert "failed_quests" in data
        assert isinstance(data["completed_quests"], list)
        assert isinstance(data["failed_quests"], list)
