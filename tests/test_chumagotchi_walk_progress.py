from ui.care_ui import (
    WALK_ROUTES,
    WalkRouteView,
    _make_walk_progress_embed,
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
