from pathlib import Path
import xml.etree.ElementTree as ET


SVG = Path(__file__).parents[1] / "static" / "churider" / "svg" / "base" / "churider-idle-anatomy.svg"


def test_idle_anatomy_svg_keeps_drider_structure():
    root = ET.parse(SVG).getroot()
    ids = {node.attrib["id"] for node in root.iter() if "id" in node.attrib}

    assert root.attrib["data-character"] == "churider"
    assert root.attrib["data-state"] == "idle"
    assert root.attrib["data-stage"] == "appearance-blockout-v2"
    assert {"churider", "torso", "head", "thorax", "abdomen", "arm_l", "arm_r"} <= ids
    assert {f"leg_{side}{index}" for side in ("l", "r") for index in range(1, 5)} <= ids
    assert {"hair_back", "hair_front", "eye_l_main", "eye_r_main"} <= ids
    assert {f"eye_r_extra_{index}" for index in range(1, 6)} <= ids


def test_idle_anatomy_svg_does_not_embed_bitmap_character_art():
    root = ET.parse(SVG).getroot()
    local_names = {node.tag.rsplit("}", 1)[-1] for node in root.iter()}
    assert "image" not in local_names


def test_idle_appearance_encodes_exactly_seven_canonical_eye_groups():
    root = ET.parse(SVG).getroot()
    ids = {node.attrib["id"] for node in root.iter() if "id" in node.attrib}
    eye_ids = {ident for ident in ids if ident.startswith("eye_")}
    assert eye_ids == {
        "eye_l_main", "eye_r_main",
        "eye_r_extra_1", "eye_r_extra_2", "eye_r_extra_3",
        "eye_r_extra_4", "eye_r_extra_5",
    }
