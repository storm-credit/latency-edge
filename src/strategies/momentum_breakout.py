from collections import deque
from typing import Dict, Any
from src.strategies.base import BaseStrategy


class MomentumBreakout(BaseStrategy):
    """
    최근 N틱의 고점을 돌파할 때 강한 모멘텀(거래량 동반)으로 진입하는 전략
    청산: Trailing Stop (고점 대비 trail_pct% 하락 시) 또는 Stop Loss (진입가 대비 stop_loss_pct% 하락 시)
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.lookback = config.get("lookback", 5)
        self.volume_multiplier = config.get("volume_multiplier", 1.5)
        self.trail_pct = config.get("trail_pct", 0.01)
        self.stop_loss_pct = config.get("stop_loss_pct", 0.02)
        self.min_hold_ticks = config.get("min_hold_ticks", 2)

        self.state: Dict[str, Any] = {
            "price_history": deque(maxlen=self.lookback),
            "volume_history": deque(maxlen=self.lookback),
            "current_price": 0.0,
            "current_volume": 0.0,
            "in_position": False,
            "entry_price": 0.0,
            "highest_since_entry": 0.0,
            "ticks_in_position": 0,
        }

    def on_tick(self, market_state: Dict[str, Any]) -> None:
        price = market_state.get('price', 0.0)
        volume = market_state.get('volume', 0.0)

        if price > 0:
            self.state["current_price"] = price
            self.state["current_volume"] = volume
            self.state["price_history"].append(price)
            self.state["volume_history"].append(volume)

            # 포지션 보유 중이면 고점 갱신 + 틱 카운트
            if self.state["in_position"]:
                self.state["ticks_in_position"] += 1
                if price > self.state["highest_since_entry"]:
                    self.state["highest_since_entry"] = price

    def should_enter(self) -> bool:
        """순수 판정 — 상태 변이 없음"""
        if len(self.state["price_history"]) < self.lookback:
            return False

        history = list(self.state["price_history"])
        recent_high = max(history[:-1])
        vol_history = list(self.state["volume_history"])
        avg_vol = sum(vol_history[:-1]) / (self.lookback - 1)

        price_breakout = self.state["current_price"] > recent_high
        volume_breakout = self.state["current_volume"] > (avg_vol * self.volume_multiplier)

        return price_breakout and volume_breakout

    def on_enter(self) -> None:
        """진입 확정 후 상태 갱신"""
        self.state["entry_price"] = self.state["current_price"]
        self.state["highest_since_entry"] = self.state["current_price"]
        self.state["ticks_in_position"] = 0

    def should_exit(self) -> bool:
        """순수 판정 — 상태 변이 없음"""
        if not self.state["in_position"]:
            return False

        price = self.state["current_price"]
        entry = self.state["entry_price"]
        highest = self.state["highest_since_entry"]

        # Stop Loss는 즉시 발동 (최소 보유 무시)
        if entry > 0 and price <= entry * (1 - self.stop_loss_pct):
            return True

        # Trailing Stop은 최소 보유 틱 이후만
        if self.state["ticks_in_position"] < self.min_hold_ticks:
            return False

        if highest > 0 and price <= highest * (1 - self.trail_pct):
            return True

        return False

    def on_exit(self) -> None:
        """청산 확정 후 상태 갱신"""
        self.state["ticks_in_position"] = 0

    def position_size(self) -> float:
        return self.config.get("position_size", 1.0)
