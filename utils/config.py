"""게임 설정 관리 시스템.

YAML 기반 설정 파일에서 게임 상수를 로드합니다.
"""
import os
from typing import Any, Dict, Optional

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class Config:
    """게임 설정 관리자.

    config/game.yaml 파일에서 설정을 로드하며,
    파일이 없거나 YAML 라이브러리가 없는 경우 기본값을 사용합니다.
    """

    _instance: Optional['Config'] = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """설정 파일 로드."""
        if not YAML_AVAILABLE:
            print("[경고] PyYAML이 설치되지 않아 기본 설정을 사용합니다.")
            self._config = self._get_defaults()
            return

        config_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'config',
            'game.yaml'
        )

        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
                print(f"[정보] 설정 파일 로드: {config_path}")
            else:
                print(f"[경고] 설정 파일 없음: {config_path}, 기본값 사용")
                self._config = self._get_defaults()
        except Exception as e:
            print(f"[오류] 설정 파일 로드 실패: {e}, 기본값 사용")
            self._config = self._get_defaults()

    def get(self, key_path: str, default: Any = None) -> Any:
        """설정값 조회.

        Args:
            key_path: "game.max_level" 형식의 경로 (점으로 구분)
            default: 기본값

        Returns:
            설정값 또는 기본값

        Example:
            >>> config = Config()
            >>> max_level = config.get('game.max_level', 100)
        """
        keys = key_path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def _get_defaults(self) -> Dict[str, Any]:
        """기본 설정값 반환."""
        return {
            'game': {
                'level_up_base': 100,
                'level_up_multiplier': 1.5,
                'max_level': 100,
                'max_energy': 100,
                'energy_regen_rate': 1,
                'base_inventory_slots': 20,
                'max_inventory_slots': 100,
            },
            'economy': {
                'shop_fee_rate': 0.1,
                'npc_shop_discount_rate': 0.05,
                'min_trade_gold': 1,
                'max_trade_gold': 999999,
            },
            'combat': {
                'base_crit_chance': 0.05,
                'base_dodge_chance': 0.05,
                'flee_success_rate': 0.7,
                'exp_multiplier_easy': 0.8,
                'exp_multiplier_normal': 1.0,
                'exp_multiplier_hard': 1.5,
            },
            'gathering': {
                'base_success_rate': 0.8,
                'quality_bonus_multiplier': 1.2,
            },
            'fishing': {
                'catch_window_ms': 2000,
                'perfect_window_ms': 500,
            },
            'movement': {
                'cooldown_seconds': 300,
                'energy_cost_multiplier': 1.0,
            },
        }


# 전역 config 인스턴스
config = Config()
