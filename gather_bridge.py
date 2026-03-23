"""gather_bridge.py — 채집 결과 통합 브릿지

fishing.py, gathering.py 등에서 채집 완료 시 호출하는 브릿지.
기존의 산발적인 try/except: pass 패턴을 명시적 에러 로깅으로 교체합니다.
"""
import logging

logger = logging.getLogger(__name__)


class GatherBridge:
    """채집/낚시 결과를 Economy를 통해 처리하고 연관 시스템을 호출하는 브릿지."""

    def on_gather_complete(
        self,
        economy,
        item_id: str,
        item_name: str,
        count: int,
        grade: str,
    ) -> dict:
        """채집 완료 처리.

        Economy를 통해 아이템을 추가하고, village/collection을
        try/except 대신 명시적 에러 로깅으로 호출합니다.

        Returns:
            {
                "added": bool,           # 인벤토리 추가 성공 여부
                "is_new_collection": bool  # 도감 신규 등록 여부
            }
        """
        added = economy.add_item("채집", item_id, count)
        is_new_collection = False

        try:
            from village import village_manager
            village_manager.add_contribution(2, "gathering")
        except Exception as e:
            logger.error(f"[GatherBridge] village contribution 실패: {e}")

        if added:
            try:
                from collection import collection_manager
                is_new, _total = collection_manager.register(
                    "채집", item_id, item_name, grade
                )
                is_new_collection = bool(is_new)
            except Exception as e:
                logger.error(f"[GatherBridge] collection register 실패: {e}")

        return {"added": added, "is_new_collection": is_new_collection}

    def on_fish_caught(
        self,
        economy,
        fish_id: str,
        fish_name: str,
        size_cm: float,
        price: int,
        grade: str,
    ) -> dict:
        """낚시 완료 처리.

        Economy를 통해 물고기를 추가하고, village/weekly_fishing/
        collection/achievement를 명시적 에러 로깅으로 호출합니다.

        Returns:
            {
                "added": bool,           # 인벤토리 추가 성공 여부
                "is_new_collection": bool  # 도감 신규 등록 여부
            }
        """
        added = economy.add_item("낚시", fish_id, 1)
        is_new_collection = False

        try:
            from village import village_manager
            village_manager.add_contribution(1, "fishing")
        except Exception as e:
            logger.error(f"[GatherBridge] village contribution 실패: {e}")

        try:
            from bulletin import weekly_fishing
            weekly_fishing.add_catch(economy.player.name, fish_name, size_cm)
        except Exception as e:
            logger.error(f"[GatherBridge] weekly_fishing 실패: {e}")

        if added:
            try:
                from collection import collection_manager
                is_new, _total = collection_manager.register(
                    "낚시", fish_id, fish_name, grade, size_cm
                )
                is_new_collection = bool(is_new)
            except Exception as e:
                logger.error(f"[GatherBridge] collection register 실패: {e}")

        try:
            from achievements import achievement_manager
            achievement_manager.increment("fish_caught", 1)
        except Exception as e:
            logger.error(f"[GatherBridge] achievement increment 실패: {e}")

        return {"added": added, "is_new_collection": is_new_collection}


# 모듈 레벨 싱글톤
gather_bridge = GatherBridge()
