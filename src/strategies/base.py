from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseStrategy(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.state: Dict[str, Any] = {}

    @abstractmethod
    def on_tick(self, market_state: Dict[str, Any]) -> None:
        """시장 데이터 틱이 들어올 때 호출"""
        pass

    @abstractmethod
    def should_enter(self) -> bool:
        """진입 조건 검사 (순수 판정, 상태 변이 금지)"""
        pass

    @abstractmethod
    def should_exit(self) -> bool:
        """청산 조건 검사 (순수 판정, 상태 변이 금지)"""
        pass

    def on_enter(self) -> None:
        """진입 확정 후 상태 갱신 (엔진이 호출)"""
        pass

    def on_exit(self) -> None:
        """청산 확정 후 상태 갱신 (엔진이 호출)"""
        pass

    @abstractmethod
    def position_size(self) -> float:
        """진입 사이즈 계산"""
        pass
