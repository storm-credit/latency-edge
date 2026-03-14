from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseStrategy(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.state = {}

    @abstractmethod
    def on_tick(self, market_state: Dict[str, Any]) -> None:
        """시장 데이터 틱이 들어올 때 호출"""
        pass

    @abstractmethod
    def should_enter(self) -> bool:
        """진입 조건 검사"""
        pass

    @abstractmethod
    def should_exit(self) -> bool:
        """청산 조건 검사"""
        pass

    @abstractmethod
    def position_size(self) -> float:
        """진입 사이즈 계산"""
        pass

    @abstractmethod
    def risk_limits(self) -> Dict[str, float]:
        """전략별 리스크 리밋 반환"""
        pass
