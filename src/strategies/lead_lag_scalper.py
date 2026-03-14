from typing import Dict, Any
from src.strategies.base import BaseStrategy
from src.features.imbalance import calculate_premium

class LeadLagScalper(BaseStrategy):
    """
    바이낸스(Lead)와 업비트(Lag)의 가격 차이(프리미엄)를 이용한 전략
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.entry_threshold = config.get("entry_threshold", 0.05) # 5% 차이 날 때 진입
        self.exit_threshold = config.get("exit_threshold", 0.01)  # 1%로 좁혀지면 청산
        self.fx_rate = config.get("fx_rate", 1300.0)
        self.position_limit = config.get("position_size", 1.0)
        
        self.state = {
            "current_premium": 0.0,
            "in_position": False
        }

    def on_tick(self, market_state: Dict[str, Any]) -> None:
        local_price = market_state.get('upbit_price', 0)
        global_price = market_state.get('binance_price', 0)
        
        if local_price > 0 and global_price > 0:
            self.state["current_premium"] = calculate_premium(local_price, global_price, self.fx_rate)

    def should_enter(self) -> bool:
        return self.state["current_premium"] >= self.entry_threshold

    def should_exit(self) -> bool:
        return self.state["current_premium"] <= self.exit_threshold

    def position_size(self) -> float:
        return self.position_limit

    def risk_limits(self) -> Dict[str, float]:
        return {"max_loss_per_trade": 0.02} # 2% 손절 제한
