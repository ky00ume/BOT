"""user_data.py — 유저 데이터 클래스 (스키마 버전 관리)

Player를 래핑하는 데이터 클래스로, schema_version 필드를 통해
저장 데이터의 마이그레이션을 안전하게 처리합니다.
"""

SCHEMA_VERSION = 2

# 버전별 마이그레이션 함수: data dict을 받아 in-place로 수정 후 반환
SCHEMA_MIGRATIONS = {
    # 1 → 2: costume/condition/stability/_flags 기본값 추가
    1: lambda data: _migrate_v1_to_v2(data),
}


def _migrate_v1_to_v2(data: dict) -> dict:
    """v1 → v2 마이그레이션: 새 필드를 기본값으로 추가 (기존 값은 보존)."""
    data.setdefault("costume", {
        "toy": None,
        "hat": None,
        "outfit": None,
        "shoes": None,
        "accessory": None,
    })
    data.setdefault("condition", 50)
    data.setdefault("stability", 50)
    data.setdefault("_flags", {})
    return data


class UserData:
    """Player 저장 데이터를 schema_version과 함께 관리하는 유틸리티 클래스."""

    @staticmethod
    def to_save_dict(player) -> dict:
        """Player → 저장용 dict (schema_version 포함)."""
        data = player.get_save_data()
        data["schema_version"] = SCHEMA_VERSION
        return data

    @staticmethod
    def from_save_dict(data: dict, player):
        """dict → Player 로드 (마이그레이션 적용 후)."""
        migrated = UserData._migrate(data)
        player.load_from_dict(migrated)

    @staticmethod
    def _migrate(data: dict) -> dict:
        """schema_version을 비교하여 순차적으로 마이그레이션을 적용합니다.

        기존 값은 절대 건드리지 않고, 새 필드만 기본값으로 추가합니다(MERGE).
        """
        version = data.get("schema_version", 1)
        for v in range(version, SCHEMA_VERSION):
            migrate_fn = SCHEMA_MIGRATIONS.get(v)
            if migrate_fn:
                data = migrate_fn(data) or data
        data["schema_version"] = SCHEMA_VERSION
        return data
