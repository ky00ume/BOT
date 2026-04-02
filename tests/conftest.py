"""Pytest configuration and fixtures.

이 파일은 모든 테스트에서 사용할 수 있는 공통 fixture들을 정의합니다.
"""
import pytest
import os
import tempfile
from typing import Generator


@pytest.fixture
def fresh_player():
    """테스트용 새 플레이어 인스턴스.

    Returns:
        초기 상태의 Player 객체
    """
    from player import Player
    return Player(name="테스트플레이어")


@pytest.fixture
def player_with_gold(fresh_player):
    """골드를 보유한 플레이어.

    Returns:
        1000 골드를 보유한 Player 객체
    """
    fresh_player.gold = 1000
    return fresh_player


@pytest.fixture
def player_with_items(fresh_player):
    """아이템을 보유한 플레이어.

    Returns:
        여러 아이템을 보유한 Player 객체
    """
    fresh_player.inventory = {
        "herb_01": 10,
        "ore_iron": 5,
        "potion_hp": 3,
    }
    return fresh_player


@pytest.fixture
def economy(fresh_player):
    """Economy 인스턴스.

    Returns:
        fresh_player와 연결된 Economy 객체
    """
    from economy import Economy
    return Economy(fresh_player)


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """임시 데이터베이스 fixture.

    테스트용 임시 DB 파일을 생성하고 테스트 후 삭제합니다.

    Yields:
        임시 DB 파일 경로
    """
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # DB 환경변수 설정
    old_db = os.environ.get('DB_PATH')
    os.environ['DB_PATH'] = path

    # DB 초기화
    from database import init_db
    init_db()

    yield path

    # 정리
    if old_db:
        os.environ['DB_PATH'] = old_db
    else:
        if 'DB_PATH' in os.environ:
            del os.environ['DB_PATH']

    # 파일 삭제
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture(autouse=True)
def reset_singletons():
    """각 테스트마다 싱글톤 인스턴스 리셋.

    Config 등의 싱글톤 객체가 테스트 간 영향을 주지 않도록 합니다.
    """
    from utils.config import Config

    # Config 싱글톤 리셋
    Config._instance = None

    yield

    # 테스트 후 정리
    Config._instance = None
