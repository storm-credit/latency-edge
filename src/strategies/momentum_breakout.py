from typing import Dict, Any
from src.strategies.base import BaseStrategy

class MomentumBreakout(BaseStrategy):
    """
    최근 N틱의 고점을 돌파할 때 강한 모멘텀(거래량 동반)으로 진입하는 전략
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.lookback = config.get("lookback", 10)
        self.volume_multiplier = config.get("volume_multiplier", 2.0)
        
        self.state = {
            "price_history": [],
            "volume_history": [],
            "current_price": 0.0,
            "current_volume": 0.0
        }

    def on_tick(self, market_state: Dict[str, Any]) -> None:
        price = market_state.get('price', 0.0)
        volume = market_state.get('volume', 0.0)
        
        if price > 0:
            self.state["current_price"] = price
            self.state["current_volume"] = volume
            
            self.state["price_history"].append(price)
            self.state["volume_history"].append(volume)
            
            if len(self.state["price_history"]) > self.lookback:
                self.state["price_history"].pop(0)
                self.state["volume_history"].pop(0)

    def should_enter(self) -> bool:
        if len(self.state["price_history"]) < self.lookback:
            return False
            
        recent_high = max(self.state["price_history"][:-1])
        avg_vol = sum(self.state["volume_history"][:-1]) / (self.lookback - 1)
        
        price_breakout = self.state["current_price"] > recent_high
        volume_breakout = self.state["current_volume"] > (avg_vol * self.volume_multiplier)
        
        return price_breakout and volume_breakout

    def should_exit(self) -> bool:
        # 1틱 뒤 바로 청산하거나 손절 등의 단순 조건 (스캐폴딩)
        # 실제로는 Trailing Stop 등이 구현됨
        return True 

    def position_size(self) -> float:
        return 1.0

    def risk_limits(self) -> Dict[str, float]:
        return {"max_loss_per_trade": 0.01}
