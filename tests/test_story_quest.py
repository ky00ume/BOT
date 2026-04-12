"""tests/test_story_quest.py — StoryQuestManager 단위 테스트"""
import datetime
import pytest
from unittest.mock import patch


# ── get_shadow_hint ───────────────────────────────────────────────────────────

class TestGetShadowHint:
    @pytest.mark.parametrize("value,expected_fragment", [
        (50,   "감싸안"),
        (30,   "조금 더 짙어"),
        (10,   "미세하게"),
        (0,    "평온하게"),
        (-10,  "희미하게"),
        (-30,  "너머로"),
        (-50,  "투명해"),
    ])
    def test_hint_per_range(self, story_quest_manager, value, expected_fragment):
        result = story_quest_manager.get_shadow_hint(value)
        assert expected_fragment in result

    def test_uses_instance_value_by_default(self, story_quest_manager):
        story_quest_manager.shadow_sync = 50
        result = story_quest_manager.get_shadow_hint()
        assert "감싸안" in result

    def test_explicit_override(self, story_quest_manager):
        story_quest_manager.shadow_sync = 0
        result = story_quest_manager.get_shadow_hint(50)
        assert "감싸안" in result


# ── get_game_time ─────────────────────────────────────────────────────────────

class TestGetGameTime:
    def _mock_now(self, hour: int):
        """주어진 시(hour)를 가진 datetime 객체를 반환하는 mock."""
        dt = datetime.datetime(2024, 1, 1, hour, 0, 0)
        return dt

    def test_daytime_hour(self, story_quest_manager):
        mock_dt = self._mock_now(12)
        with patch("story_quest.datetime") as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_dt
            mock_datetime.datetime.utcnow.return_value = mock_dt
            result = story_quest_manager.get_game_time()
        assert result == "day"

    def test_nighttime_hour(self, story_quest_manager):
        mock_dt = self._mock_now(22)
        with patch("story_quest.datetime") as mock_datetime:
            mock_datetime.datetime.now.return_value = mock_dt
            mock_datetime.datetime.utcnow.return_value = mock_dt
            result = story_quest_manager.get_game_time()
        assert result == "night"

    def test_returns_string(self, story_quest_manager):
        result = story_quest_manager.get_game_time()
        assert result in ("day", "night")


# ── is_quest_done / complete_quest ────────────────────────────────────────────

class TestQuestDoneAndComplete:
    def test_initially_not_done(self, story_quest_manager):
        assert story_quest_manager.is_quest_done(1, 1) is False

    def test_complete_marks_done(self, story_quest_manager):
        story_quest_manager.complete_quest(1, 1)
        assert story_quest_manager.is_quest_done(1, 1) is True

    def test_complete_idempotent(self, story_quest_manager):
        story_quest_manager.complete_quest(1, 2)
        story_quest_manager.complete_quest(1, 2)
        assert story_quest_manager.quest_log.count("ch1_q2") == 1

    def test_multiple_quests_independent(self, story_quest_manager):
        story_quest_manager.complete_quest(1, 1)
        assert story_quest_manager.is_quest_done(1, 2) is False


# ── add_hint ──────────────────────────────────────────────────────────────────

class TestAddHint:
    def test_add_new_hint(self, story_quest_manager):
        story_quest_manager.add_hint("신비로운 단서")
        assert "신비로운 단서" in story_quest_manager.hints

    def test_no_duplicate_hints(self, story_quest_manager):
        story_quest_manager.add_hint("중복 힌트")
        story_quest_manager.add_hint("중복 힌트")
        assert story_quest_manager.hints.count("중복 힌트") == 1

    def test_multiple_different_hints(self, story_quest_manager):
        story_quest_manager.add_hint("힌트1")
        story_quest_manager.add_hint("힌트2")
        assert len(story_quest_manager.hints) == 2


# ── add_shadow_sync ───────────────────────────────────────────────────────────

class TestAddShadowSync:
    def test_increase(self, story_quest_manager):
        story_quest_manager.shadow_sync = 0
        story_quest_manager.add_shadow_sync(30)
        assert story_quest_manager.shadow_sync == 30

    def test_decrease(self, story_quest_manager):
        story_quest_manager.shadow_sync = 0
        story_quest_manager.add_shadow_sync(-20)
        assert story_quest_manager.shadow_sync == -20

    def test_clamped_at_positive_100(self, story_quest_manager):
        story_quest_manager.shadow_sync = 90
        story_quest_manager.add_shadow_sync(50)
        assert story_quest_manager.shadow_sync == 100

    def test_clamped_at_negative_100(self, story_quest_manager):
        story_quest_manager.shadow_sync = -90
        story_quest_manager.add_shadow_sync(-50)
        assert story_quest_manager.shadow_sync == -100

    def test_stays_within_bounds(self, story_quest_manager):
        story_quest_manager.shadow_sync = 0
        story_quest_manager.add_shadow_sync(200)
        assert -100 <= story_quest_manager.shadow_sync <= 100


# ── to_dict / from_dict ───────────────────────────────────────────────────────

class TestSerialization:
    def test_to_dict_structure(self, story_quest_manager):
        data = story_quest_manager.to_dict()
        assert "chapter" in data
        assert "quest" in data
        assert "shadow_sync" in data
        assert "hints" in data
        assert "flags" in data
        assert "quest_log" in data

    def test_roundtrip_preserves_state(self, story_quest_manager, fresh_player):
        story_quest_manager.chapter = 2
        story_quest_manager.quest = 3
        story_quest_manager.shadow_sync = 42
        story_quest_manager.add_hint("힌트A")
        story_quest_manager.flags["some_flag"] = True
        story_quest_manager.complete_quest(1, 1)

        data = story_quest_manager.to_dict()

        from story_quest import StoryQuestManager
        sqm2 = StoryQuestManager(fresh_player)
        sqm2.from_dict(data)

        assert sqm2.chapter == 2
        assert sqm2.quest == 3
        assert sqm2.shadow_sync == 42
        assert "힌트A" in sqm2.hints
        assert sqm2.flags.get("some_flag") is True
        assert sqm2.is_quest_done(1, 1) is True

    def test_from_dict_defaults_on_empty(self, story_quest_manager):
        story_quest_manager.from_dict({})
        assert story_quest_manager.chapter == 1
        assert story_quest_manager.quest == 1
        assert story_quest_manager.shadow_sync == 0
        assert story_quest_manager.hints == []
        assert story_quest_manager.flags == {}
        assert story_quest_manager.quest_log == []

    def test_to_dict_hints_is_list(self, story_quest_manager):
        story_quest_manager.add_hint("test")
        data = story_quest_manager.to_dict()
        assert isinstance(data["hints"], list)

    def test_to_dict_flags_is_dict(self, story_quest_manager):
        story_quest_manager.flags["key"] = "value"
        data = story_quest_manager.to_dict()
        assert isinstance(data["flags"], dict)
        assert data["flags"]["key"] == "value"
