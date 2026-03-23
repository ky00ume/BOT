"""transaction_log.py — 트랜잭션 로그 시스템

모든 재화 변동(아이템 획득/소비, 골드 변동, EXP 변동)에 [LOG: TRANSACTION] 태그를
붙여 기록하는 모듈.
"""
import logging
import os

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")


class TransactionLog:
    """모든 재화 변동을 시간/소스/상세 정보와 함께 기록하는 로거."""

    def __init__(self):
        os.makedirs(LOG_DIR, exist_ok=True)
        self._logger = logging.getLogger("transaction")
        if not self._logger.handlers:
            self._logger.setLevel(logging.DEBUG)
            fmt = logging.Formatter(
                "%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            )
            fh = logging.FileHandler(
                os.path.join(LOG_DIR, "transactions.log"), encoding="utf-8"
            )
            fh.setFormatter(fmt)
            self._logger.addHandler(fh)

            ch = logging.StreamHandler()
            ch.setFormatter(fmt)
            self._logger.addHandler(ch)

    def log(
        self,
        user_name: str,
        tag: str,
        source: str,
        detail: str = "",
        changes: dict = None,
    ):
        """변동 내역을 시간/소스/상세 정보와 함께 기록합니다.

        Args:
            user_name: 대상 플레이어 이름
            tag: 로그 태그 (예: "TRANSACTION")
            source: 변동 원인 (예: "알바:다몬", "낚시", "판매:허브")
            detail: 추가 상세 설명
            changes: 변동 내역 dict (예: {"gold": 150, "exp": 20, "herb": -1})
        """
        changes_str = ""
        if changes:
            parts = []
            for k, v in changes.items():
                if isinstance(v, (int, float)):
                    parts.append(f"+{v} {k}" if v >= 0 else f"{v} {k}")
                else:
                    parts.append(f"{k}={v}")
            if parts:
                changes_str = "  변동: " + ", ".join(parts)

        msg = f"[LOG: TRANSACTION] [{user_name}] [{tag}] 출처={source}"
        if detail:
            msg += f"  {detail}"
        if changes_str:
            msg += changes_str
        self._logger.info(msg)

    def query(
        self, user_name: str, time_range=None, tag: str = None
    ) -> list:
        """저장된 로그에서 특정 유저/태그의 항목을 조회합니다.

        Args:
            user_name: 조회할 플레이어 이름
            time_range: (시작시각, 종료시각) 튜플 (현재 미사용, 확장 가능)
            tag: 필터할 태그 문자열

        Returns:
            매칭된 로그 라인 목록
        """
        log_path = os.path.join(LOG_DIR, "transactions.log")
        results = []
        if not os.path.exists(log_path):
            return results
        with open(log_path, encoding="utf-8") as f:
            for line in f:
                if f"[{user_name}]" not in line:
                    continue
                if tag and f"[{tag}]" not in line:
                    continue
                results.append(line.rstrip())
        return results


# 싱글톤 인스턴스
tx_log = TransactionLog()
