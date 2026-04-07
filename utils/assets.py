"""에셋 무결성 검증 유틸리티.

``static/`` 아래의 필수 에셋(폰트 등)이 모두 존재하는지 봇 시작 시에
검증해 FileNotFoundError 가 런타임 렌더링 도중에 터지는 상황을 막는다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from utils.logger import setup_logger


logger = setup_logger("assets")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = _PROJECT_ROOT / "static"

# 누락되면 봇이 정상 동작할 수 없는 필수 에셋 목록.
REQUIRED_ASSETS: List[Path] = [
    STATIC_DIR / "fonts" / "NotoSansCJKkr-Regular.otf",
    STATIC_DIR / "fonts" / "NotoSansCJKkr-Bold.otf",
]


def find_missing_assets(assets: Iterable[Path] = REQUIRED_ASSETS) -> List[Path]:
    """누락된 에셋 경로를 리스트로 반환."""
    return [p for p in assets if not p.exists()]


def verify_assets(assets: Iterable[Path] = REQUIRED_ASSETS) -> None:
    """필수 에셋이 모두 존재하는지 검증.

    Raises:
        FileNotFoundError: 하나라도 누락된 경우.
    """
    asset_list = list(assets)
    missing = find_missing_assets(asset_list)
    if missing:
        logger.critical(
            "필수 에셋 누락 (%d개): %s",
            len(missing),
            ", ".join(str(p) for p in missing),
        )
        raise FileNotFoundError(
            f"필수 에셋 {len(missing)}개 누락: {[str(p) for p in missing]}"
        )
    logger.info("에셋 검증 완료: %d개", len(asset_list))
