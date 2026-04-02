"""커스텀 예외 클래스.

게임 로직에서 발생하는 다양한 예외 상황을 명확히 구분합니다.
"""


class GameError(Exception):
    """게임 로직 기본 예외 클래스."""
    pass


class InsufficientResourceError(GameError):
    """자원 부족 예외.

    골드, 기력, 아이템 등이 부족할 때 발생합니다.
    """
    pass


class InvalidItemError(GameError):
    """잘못된 아이템 예외.

    존재하지 않는 아이템 ID나 잘못된 아이템 사용 시 발생합니다.
    """
    pass


class InventoryFullError(GameError):
    """인벤토리 가득 참 예외.

    인벤토리 슬롯이 가득 차서 아이템을 추가할 수 없을 때 발생합니다.
    """
    pass


class DatabaseError(GameError):
    """데이터베이스 오류 예외.

    DB 연결, 저장, 로드 실패 시 발생합니다.
    """
    pass


class RenderError(GameError):
    """렌더링 오류 예외.

    이미지 생성, 폰트 로드 실패 등 렌더링 오류 시 발생합니다.
    """
    pass


class BattleError(GameError):
    """전투 로직 오류 예외.

    잘못된 전투 액션이나 전투 상태 오류 시 발생합니다.
    """
    pass


class ConfigError(GameError):
    """설정 오류 예외.

    설정 파일 로드 실패나 잘못된 설정값 시 발생합니다.
    """
    pass
