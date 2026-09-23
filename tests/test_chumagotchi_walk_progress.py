from ui.care_ui import (
    WALK_ACTIVITY_SECONDS,
    _make_walk_progress_embed,
    _walk_progress_bar,
    _walk_scene,
)


def test_walk_is_a_real_timed_activity():
    assert WALK_ACTIVITY_SECONDS == 30
    start = _make_walk_progress_embed(30, 0)
    middle = _make_walk_progress_embed(15, 15)
    end = _make_walk_progress_embed(0, 30)
    assert "30초" in start.fields[0].value
    assert "15초" in middle.fields[0].value
    assert "0초" in end.fields[0].value
    assert start.description != middle.description
    assert middle.description != end.description


def test_walk_progress_bar_fills_over_time():
    assert _walk_progress_bar(0).count("▰") == 0
    assert _walk_progress_bar(15).count("▰") == 5
    assert _walk_progress_bar(30).count("▰") == 10


def test_walk_scenes_mix_formal_narration_with_churider_speech():
    _, start = _walk_scene(0)
    _, search = _walk_scene(16)
    _, returning = _walk_scene(29)
    assert "나갑니다." in start and "다녀오겠슴미댜." in start
    assert "더듬습니다." in search and "뭔가 있슴미댜." in search
    assert "돌아옵니다." in returning and "다녀왔슴미댜." in returning
