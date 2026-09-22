from pathlib import Path
import xml.etree.ElementTree as ET


SVG = Path(__file__).parents[1] / "static" / "churider" / "svg" / "base" / "churider-idle-anatomy.svg"


def test_idle_anatomy_svg_keeps_drider_structure():
    root = ET.parse(SVG).getroot()
    ids = {node.attrib["id"] for node in root.iter() if "id" in node.attrib}

    assert root.attrib["data-character"] == "churider"
    assert root.attrib["data-state"] == "idle"
    assert root.attrib["data-stage"] == "anatomy-blockout"
    assert {"churider", "torso", "head", "thorax", "abdomen", "arm_l", "arm_r"} <= ids
    assert {f"leg_{side}{index}" for side in ("l", "r") for index in range(1, 5)} <= ids


def test_idle_anatomy_svg_does_not_embed_bitmap_character_art():
    root = ET.parse(SVG).getroot()
    local_names = {node.tag.rsplit("}", 1)[-1] for node in root.iter()}
    assert "image" not in local_names
