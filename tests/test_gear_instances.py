from blacksmith import BlacksmithEngine
from player import Player


class FixedRng:
    def __init__(self, values):
        self.values = iter(values)

    def randint(self, lo, hi):
        value = next(self.values)
        assert lo <= value <= hi
        return value


def _forge_masterpiece(player):
    player.inventory["iron_bar"] = 3
    player.inventory["gt_wood_01"] = 1
    engine = BlacksmithEngine(player)
    session = engine.start_session("wp_sword_02")
    engine.apply_stage(session, "steady", rng=FixedRng([18]))
    engine.apply_stage(session, "steady", rng=FixedRng([16]))
    engine.apply_stage(session, "careful", rng=FixedRng([14]))
    return engine.finish_session(session)


def test_blacksmith_creates_distinct_equipment_instance_with_quality():
    p = Player("릴리")
    result = _forge_masterpiece(p)
    assert result["quality_score"] == 98
    rows = p.get_gear_instances("wp_sword_02")
    assert len(rows) == 1
    inst = rows[0]
    assert inst["quality_key"] == "Masterpiece"
    assert inst["quality_label"] == "🏆 걸작"
    assert inst["durability"] == 120
    assert inst["max_durability"] == 120
    assert inst["crafted_by"] == "릴리"
    assert inst["source"] == "blacksmith"


def test_same_item_can_have_multiple_distinct_quality_instances():
    p = Player()
    p.add_gear_item("wp_sword_02", quality_score=45, quality_key="Normal", quality_label="⚒️ 보통")
    p.add_gear_item("wp_sword_02", quality_score=95, quality_key="Masterpiece", quality_label="🏆 걸작")
    rows = p.get_gear_instances("wp_sword_02")
    assert len(rows) == 2
    assert len({row["uid"] for row in rows}) == 2
    assert sorted(row["quality_score"] for row in rows) == [45, 95]
    assert p.gear_inventory["wp_sword_02"] == 2


def test_equip_by_name_selects_best_instance_and_unequip_preserves_it():
    p = Player()
    p.add_gear_item("wp_sword_02", quality_score=45, quality_key="Normal", quality_label="⚒️ 보통")
    p.add_gear_item("wp_sword_02", quality_score=95, quality_key="Masterpiece", quality_label="🏆 걸작")
    msg = p.equip_item("wp_sword_02")
    assert "걸작" in msg
    equipped = p.get_equipped_gear_instance("main")
    assert equipped["quality_score"] == 95
    assert p.gear_inventory["wp_sword_02"] == 1

    p.unequip_item("main")
    rows = p.get_gear_instances("wp_sword_02")
    assert sorted(row["quality_score"] for row in rows) == [45, 95]
    assert p.gear_inventory["wp_sword_02"] == 2


def test_quality_changes_equipment_stats_but_not_costume_system():
    normal = Player()
    normal.add_gear_item("wp_sword_02", quality_score=50, quality_key="Normal", quality_label="⚒️ 보통")
    normal.equip_item("wp_sword_02")

    masterpiece = Player()
    masterpiece.add_gear_item("wp_sword_02", quality_score=95, quality_key="Masterpiece", quality_label="🏆 걸작")
    masterpiece.equip_item("wp_sword_02")

    assert masterpiece.get_attack() > normal.get_attack()
    assert not hasattr(masterpiece, "costume_instances")
    assert masterpiece.costume == normal.costume


def test_legacy_count_inventory_migrates_to_normal_instances():
    p = Player()
    p.gear_inventory = {"wp_sword_01": 2}
    p._flags = {}
    p.ensure_gear_instances()
    rows = p.get_gear_instances("wp_sword_01")
    assert len(rows) == 2
    assert all(row["quality_key"] == "Normal" for row in rows)
    # 두 번 호출해도 중복 생성하지 않는다.
    p.ensure_gear_instances()
    assert len(p.get_gear_instances("wp_sword_01")) == 2


def test_instance_metadata_survives_player_save_dict_round_trip():
    p = Player("대장장이")
    p.add_gear_item("wp_sword_02", quality_score=87, quality_key="Excellent", quality_label="✨ 훌륭함", crafted_by="대장장이", source="blacksmith")
    p.equip_item("wp_sword_02")
    data = p.get_save_data()

    restored = Player()
    restored.load_from_dict(data)
    inst = restored.get_equipped_gear_instance("main")
    assert inst["quality_score"] == 87
    assert inst["quality_key"] == "Excellent"
    assert inst["crafted_by"] == "대장장이"
    assert inst["source"] == "blacksmith"


def test_instance_metadata_survives_database_round_trip(temp_db):
    from db.player import load_player_from_db, save_player_to_db

    p = Player("DB대장장이")
    p.user_id = 424242
    p.add_gear_item(
        "wp_sword_02",
        quality_score=93,
        quality_key="Masterpiece",
        quality_label="🏆 걸작",
        crafted_by="DB대장장이",
        source="blacksmith",
    )
    p.equip_item("wp_sword_02")
    save_player_to_db(p)

    data = load_player_from_db(424242)
    restored = Player()
    restored.load_from_dict(data)
    inst = restored.get_equipped_gear_instance("main")
    assert inst["quality_score"] == 93
    assert inst["quality_key"] == "Masterpiece"
    assert inst["crafted_by"] == "DB대장장이"
    assert inst["durability"] == 120
