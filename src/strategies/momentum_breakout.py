from collections import deque
from typing import Dict, Any
from src.strategies.base import BaseStrategy
from src.features.atr import ATRCalculator
from src.config import Config


class MomentumBreakout(BaseStrategy):
    """
    최근 N틱의 고점을 돌파할 때 강한 모멘텀(거래량 동반)으로 진입하는 전략

    v2 개선 (논문 기반):
    - ATR 기반 동적 트레일링 스탑 (고정 1% → 변동성 비례)
    - ATR 기반 동적 손절 (고정 2% → 변동성 비례)
    - 데이터 부족 시 기존 고정 % 폴백

    논문: "Catching Crypto Trends" (Zarattini et al., 2025)
    - Donchian + ATR 앙상블: CAGR 30%, Sharpe 1.58, MDD 19%
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.lookback = config.get("lookback", Config.MOM_LOOKBACK)
        self.volume_multiplier = config.get("volume_multiplier", Config.MOM_VOLUME_MULT)
        # 폴백용 고정 비율
        self.trail_pct = config.get("trail_pct", Config.MOM_TRAIL_PCT)
        self.stop_loss_pct = config.get("stop_loss_pct", Config.MOM_STOP_LOSS_PCT)
        self.min_hold_ticks = config.get("min_hold_ticks", 2)

        # ATR 동적 스탑
        atr_period = config.get("atr_period", Config.ATR_PERIOD)
        self.atr = ATRCalculator(period=atr_period)
        self.atr_trail_mult = config.get("atr_trail_mult", Config.ATR_TRAIL_MULT)
        self.atr_stop_mult = config.get("atr_stop_mult", Config.ATR_STOP_MULT)

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

            # ATR 업데이트
            self.atr.update(price)

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

    def _get_stop_loss_pct(self) -> float:
        """ATR 기반 동적 손절 비율 (폴백: 고정 %)"""
        atr_pct = self.atr.get_atr_pct(self.state["current_price"])
        if atr_pct is not None:
            return self.atr_stop_mult * atr_pct
        return self.stop_loss_pct

    def _get_trail_pct(self) -> float:
        """ATR 기반 동적 트레일링 비율 (폴백: 고정 %)"""
        atr_pct = self.atr.get_atr_pct(self.state["current_price"])
        if atr_pct is not None:
            return self.atr_trail_mult * atr_pct
        return self.trail_pct

    def should_exit(self) -> bool:
        """ATR 기반 동적 스탑 — 순수 판정"""
        if not self.state["in_position"]:
            return False

        price = self.state["current_price"]
        entry = self.state["entry_price"]
        highest = self.state["highest_since_entry"]

        # Stop Loss는 즉시 발동 (최소 보유 무시)
        dynamic_stop = self._get_stop_loss_pct()
        if entry > 0 and price <= entry * (1 - dynamic_stop):
            return True

        # Trailing Stop은 최소 보유 틱 이후만
        if self.state["ticks_in_position"] < self.min_hold_ticks:
            return False

        dynamic_trail = self._get_trail_pct()
        if highest > 0 and price <= highest * (1 - dynamic_trail):
            return True

        return False

    def on_enter(self) -> None:
        """진입 확정 후 상태 갱신"""
        self.state["entry_price"] = self.state["current_price"]
        self.state["highest_since_entry"] = self.state["current_price"]
        self.state["ticks_in_position"] = 0

    def on_exit(self) -> None:
        """청산 확정 후 상태 갱신"""
        self.state["ticks_in_position"] = 0

    def position_size(self) -> float:
        return self.config.get("position_size", 1.0)
