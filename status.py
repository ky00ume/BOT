import json
import os

STATUS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "status.json")

DEFAULT_STATUS = {
    "name":        "츄라이더",
    "level":       1,
    "hp":          100,
    "max_hp":      100,
    "mp":          50,
    "max_mp":      50,
    "energy":      100,
    "max_energy":  100,
    "gold":        500,
    "base_stats": {
        "str":  10,
        "int":  10,
        "dex":  10,
        "will": 10,
        "luck": 5,
    },
    "inventory":  {},
    "equipment": {
        "main":  None,
        "sub":   None,
        "body":  None,
        "head":  None,
        "hands": None,
        "feet":  None,
    },
}


def ensure_status_json():
    """status.json이 없으면 기본값으로 생성."""
    if not os.path.exists(STATUS_PATH):
        with open(STATUS_PATH, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_STATUS, f, ensure_ascii=False, indent=2)
    else:
        # 기존 파일에 누락된 키 보완
        with open(STATUS_PATH, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
        updated = False
        for key, val in DEFAULT_STATUS.items():
            if key not in data:
                data[key] = val
                updated = True
        if updated:
            with open(STATUS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    return STATUS_PATH
