from collections import deque
from typing import Dict, Any
from src.strategies.base import BaseStrategy
from src.features.atr import ATRCalculator
from src.features.donchian import DonchianEnsemble
from src.features.regime import RegimeDetector
from src.config import Config


class MomentumBreakout(BaseStrategy):
    """
    최근 N틱의 고점을 돌파할 때 강한 모멘텀(거래량 동반)으로 진입하는 전략

    v3 개선 (논문 기반):
    - Donchian 앙상블: 다중 기간 채널 투표로 노이즈 필터링
    - ATR 기반 동적 트레일링 스탑
    - EWMA 레짐 감지: 고변동성 시 스탑 확대 + 포지션 축소

    논문:
    - "Catching Crypto Trends" (Zarattini et al., 2025) — Donchian + ATR
    - "Volatility-Adaptive Trend-Following" (Karassavidis et al., 2025) — 레짐
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.lookback = config.get("lookback", Config.MOM_LOOKBACK)
        self.volume_multiplier = config.get("volume_multiplier", Config.MOM_VOLUME_MULT)
        self.trail_pct = config.get("trail_pct", Config.MOM_TRAIL_PCT)
        self.stop_loss_pct = config.get("stop_loss_pct", Config.MOM_STOP_LOSS_PCT)
        self.min_hold_ticks = config.get("min_hold_ticks", 2)

        # ATR 동적 스탑
        atr_period = config.get("atr_period", Config.ATR_PERIOD)
        self.atr = ATRCalculator(period=atr_period)
        self.atr_trail_mult = config.get("atr_trail_mult", Config.ATR_TRAIL_MULT)
        self.atr_stop_mult = config.get("atr_stop_mult", Config.ATR_STOP_MULT)

        # Donchian 앙상블 (다중 기간 돌파 투표)
        donchian_periods = config.get("donchian_periods", Config.DONCHIAN_PERIODS)
        self.donchian = DonchianEnsemble(periods=donchian_periods)
        self.use_donchian = config.get("use_donchian", True)

        # EWMA 레짐 감지
        self.regime = RegimeDetector(
            fast_span=config.get("regime_fast", Config.REGIME_FAST_SPAN),
            slow_span=config.get("regime_slow", Config.REGIME_SLOW_SPAN),
        )

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

            # 모듈 업데이트
            self.atr.update(price)
            self.donchian.update(price)
            self.regime.update(price)

            if self.state["in_position"]:
                self.state["ticks_in_position"] += 1
                if price > self.state["highest_since_entry"]:
                    self.state["highest_since_entry"] = price

    def should_enter(self) -> bool:
        """Donchian 앙상블 + 거래량 확인 진입"""
        if len(self.state["price_history"]) < self.lookback:
            return False

        price = self.state["current_price"]

        # Donchian 앙상블 돌파 (활성 시)
        if self.use_donchian and self.donchian.ready:
            if not self.donchian.breakout_signal(price):
                return False
        else:
            # 폴백: 기존 N-tick 고점 돌파
            history = list(self.state["price_history"])
            recent_high = max(history[:-1])
            if price <= recent_high:
                return False

        # 거래량 확인
        vol_history = list(self.state["volume_history"])
        avg_vol = sum(vol_history[:-1]) / (self.lookback - 1)
        volume_breakout = self.state["current_volume"] > (avg_vol * self.volume_multiplier)

        return volume_breakout

    def _get_stop_loss_pct(self) -> float:
        """ATR × 레짐 배수 기반 동적 손절"""
        atr_pct = self.atr.get_atr_pct(self.state["current_price"])
        base = (self.atr_stop_mult * atr_pct) if atr_pct is not None else self.stop_loss_pct
        return base * self.regime.get_stop_multiplier()

    def _get_trail_pct(self) -> float:
        """ATR × 레짐 배수 기반 동적 트레일링"""
        atr_pct = self.atr.get_atr_pct(self.state["current_price"])
        base = (self.atr_trail_mult * atr_pct) if atr_pct is not None else self.trail_pct
        return base * self.regime.get_stop_multiplier()

    def should_exit(self) -> bool:
        """ATR + 레짐 기반 동적 스탑"""
        if not self.state["in_position"]:
            return False

        price = self.state["current_price"]
        entry = self.state["entry_price"]
        highest = self.state["highest_since_entry"]

        # Stop Loss 즉시 발동
        dynamic_stop = self._get_stop_loss_pct()
        if entry > 0 and price <= entry * (1 - dynamic_stop):
            return True

        # Trailing Stop (최소 보유 틱 이후)
        if self.state["ticks_in_position"] < self.min_hold_ticks:
            return False

        dynamic_trail = self._get_trail_pct()
        if highest > 0 and price <= highest * (1 - dynamic_trail):
            return True

        # Donchian 하단 이탈 청산 (보조)
        if self.use_donchian and self.donchian.ready:
            if self.donchian.breakdown_signal(price):
                return True

        return False

    def on_enter(self) -> None:
        self.state["entry_price"] = self.state["current_price"]
        self.state["highest_since_entry"] = self.state["current_price"]
        self.state["ticks_in_position"] = 0

    def on_exit(self) -> None:
        self.state["ticks_in_position"] = 0

    def position_size(self) -> float:
        return self.config.get("position_size", 1.0)
