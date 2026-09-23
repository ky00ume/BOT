from ui.care_ui import (
    WALK_ROUTES,
    WALK_RARE_EVENTS,
    WalkRouteView,
    _choose_walk_rare_event,
    _make_walk_progress_embed,
    _walk_rare_event_scene,
    _walk_progress_bar,
    _walk_scene,
)


def test_walk_has_three_distance_routes_with_different_durations():
    assert list(WALK_ROUTES) == ["indoor", "near", "far"]
    assert WALK_ROUTES["indoor"]["duration"] < WALK_ROUTES["near"]["duration"] < WALK_ROUTES["far"]["duration"]
    assert WALK_ROUTES["indoor"]["label"] == "🏠 실내"
    assert WALK_ROUTES["near"]["label"] == "🌿 집 근처"
    assert WALK_ROUTES["far"]["label"] == "🌒 좀 멀리"


def test_walk_progress_embed_counts_down_for_each_route():
    for route, profile in WALK_ROUTES.items():
        duration = profile["duration"]
        start = _make_walk_progress_embed(route, duration, 0)
        middle = _make_walk_progress_embed(route, duration // 2, duration / 2)
        end = _make_walk_progress_embed(route, 0, duration)
        assert f"{duration}초" in start.fields[0].value
        assert "0초" in end.fields[0].value
        assert start.description != middle.description
        assert middle.description != end.description


def test_walk_progress_bar_fills_over_time():
    assert _walk_progress_bar(0, 30).count("▰") == 0
    assert _walk_progress_bar(15, 30).count("▰") == 5
    assert _walk_progress_bar(30, 30).count("▰") == 10


def test_each_route_has_distinct_princess_maker_style_scenes():
    indoor = [_walk_scene(t, WALK_ROUTES["indoor"]["duration"], "indoor")[1] for t in (0, 10, 18, 23)]
    near = [_walk_scene(t, WALK_ROUTES["near"]["duration"], "near")[1] for t in (0, 15, 25, 35)]
    far = [_walk_scene(t, WALK_ROUTES["far"]["duration"], "far")[1] for t in (0, 22, 34, 53)]
    assert len(set(indoor)) > 2
    assert len(set(near)) > 2
    assert len(set(far)) > 2
    assert indoor != near != far
    assert "다녀오겠슴미댜." in indoor[0]
    assert "다녀왔슴미댜." in indoor[-1]


def test_route_rewards_scale_with_distance():
    assert WALK_ROUTES["indoor"]["items"] == (1, 1)
    assert WALK_ROUTES["near"]["items"] == (1, 2)
    assert WALK_ROUTES["far"]["items"] == (2, 3)


def test_each_route_has_multiple_rare_events():
    assert set(WALK_RARE_EVENTS) == {"indoor", "near", "far"}
    assert all(len(events) >= 3 for events in WALK_RARE_EVENTS.values())


def test_rare_event_only_triggers_below_thirty_percent_roll():
    assert _choose_walk_rare_event("indoor", roll=0.99) is None
    chosen = _choose_walk_rare_event("indoor", roll=0.0)
    assert chosen in WALK_RARE_EVENTS["indoor"]


def test_route_specific_rare_scene_overrides_normal_scene_in_window():
    duration = WALK_ROUTES["near"]["duration"]
    event_id = "bug"
    event = WALK_RARE_EVENTS["near"][event_id]
    midpoint = sum(event["window"]) / 2 * duration
    rare = _walk_rare_event_scene("near", event_id, midpoint, duration)
    assert rare is not None
    phase, text = rare
    assert "벌레" in phase
    assert "잡을 수 있슴미댜." in text


def test_rare_event_can_add_bonus_item_or_persistent_trace():
    indoor = WALK_RARE_EVENTS["indoor"]
    far = WALK_RARE_EVENTS["far"]
    assert indoor["button"]["bonus_item"] == "mat_shiny_button"
    assert far["strange_object"]["bonus_item"] == "mat_magic_dust"
    assert "trace" in far["echo"]
