from PIL import Image

from renderer.cards import BG3Renderer
from renderer.palette import C


def test_recipe_detail_card_renders_bg3_image_and_material_states():
    renderer = BG3Renderer()
    buf = renderer.render_recipe_detail(
        "철검",
        [
            {"name": "철광석", "have": 2, "need": 5, "ok": False},
            {"name": "목재", "have": 3, "need": 3, "ok": True},
        ],
        can_craft=False,
    )
    img = Image.open(buf)
    assert img.format == "PNG"
    assert img.width == 520
    assert img.height >= 380


def test_recipe_detail_uses_red_only_for_missing_material(monkeypatch):
    captured = {}
    renderer = BG3Renderer()

    def fake_render(title, rows, **kwargs):
        captured["title"] = title
        captured["rows"] = rows
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setattr(renderer, "render_card", fake_render)
    renderer.render_recipe_detail(
        "철검",
        [
            {"name": "철광석", "have": 2, "need": 5, "ok": False},
            {"name": "목재", "have": 3, "need": 3, "ok": True},
        ],
        can_craft=False,
    )
    assert captured["title"] == "제작"
    assert captured["rows"][0]["label"] == "지금 만들려는 물건"
    assert captured["rows"][0]["value"] == "철검"
    assert captured["rows"][1]["color"] == C.RARITY["Fail"]
    assert captured["rows"][2]["color"] == C.TXT_HI
    assert all("츄라이더" not in str(row) for row in captured["rows"])
