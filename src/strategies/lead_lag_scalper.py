from typing import Dict, Any
from src.strategies.base import BaseStrategy
from src.features.imbalance import calculate_premium
from src.features.ou_calibration import OUCalibrator
from src.features.atr import ATRCalculator
from src.config import Config


class LeadLagScalper(BaseStrategy):
    """
    바이낸스(Lead)와 업비트(Lag)의 가격 차이(프리미엄)를 이용한 전략

    v2 개선 (논문 기반):
    - OU 프로세스 기반 동적 진입/청산 임계값 (z-score)
    - ATR 기반 동적 손절 (고정 3% → 변동성 비례)
    - 데이터 부족 시 기존 고정 임계값으로 폴백
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # 기존 파라미터 (폴백용)
        self.entry_threshold = config.get("entry_threshold", Config.LL_ENTRY_THRESHOLD)
        self.exit_threshold = config.get("exit_threshold", Config.LL_EXIT_THRESHOLD)
        self.fx_rate = config.get("fx_rate", Config.FX_RATE)
        self.position_limit = config.get("position_size", 1.0)
        self.min_hold_ticks = config.get("min_hold_ticks", 3)
        self.cooldown_ticks = config.get("cooldown_ticks", 5)
        self.max_loss_pct = config.get("max_loss_pct", 0.03)

        # OU 캘리브레이터 (동적 임계값)
        ou_lookback = config.get("ou_lookback", Config.OU_LOOKBACK)
        self.ou = OUCalibrator(lookback=ou_lookback)
        self.ou_entry_z = config.get("ou_entry_zscore", Config.OU_ENTRY_ZSCORE)
        self.ou_exit_z = config.get("ou_exit_zscore", Config.OU_EXIT_ZSCORE)

        # ATR 계산기 (동적 손절)
        atr_period = config.get("atr_period", Config.ATR_PERIOD)
        self.atr = ATRCalculator(period=atr_period)
        self.atr_stop_mult = config.get("atr_stop_mult", Config.ATR_STOP_MULT)

        self.state: Dict[str, Any] = {
            "current_premium": 0.0,
            "in_position": False,
            "entry_price": 0.0,
            "ticks_in_position": 0,
            "cooldown_remaining": 0,
        }

    def on_tick(self, market_state: Dict[str, Any]) -> None:
        local_price = market_state.get('upbit_price', 0)
        global_price = market_state.get('binance_price', 0)

        if local_price > 0 and global_price > 0:
            premium = calculate_premium(local_price, global_price, self.fx_rate)
            self.state["current_premium"] = premium
            # OU 캘리브레이터에 프리미엄 피드
            self.ou.update(premium)

        # ATR 업데이트 (업비트 가격 기준)
        if local_price > 0:
            self.atr.update(local_price)

        # 보유 중이면 틱 카운트 증가
        if self.state["in_position"]:
            self.state["ticks_in_position"] += 1

        # 쿨다운 감소
        if self.state["cooldown_remaining"] > 0:
            self.state["cooldown_remaining"] -= 1

    def should_enter(self) -> bool:
        """OU z-score 기반 진입 판정 (폴백: 고정 임계값)"""
        if self.state["cooldown_remaining"] > 0:
            return False

        zscore = self.ou.get_zscore(self.state["current_premium"])
        if zscore is not None and self.ou.is_mean_reverting():
            # OU 모델 활성 → z-score 기반 진입
            return zscore <= self.ou_entry_z
        else:
            # 폴백 → 기존 고정 임계값
            return self.state["current_premium"] <= self.entry_threshold

    def should_exit(self) -> bool:
        """OU z-score 기반 청산 판정 + ATR 손절"""
        if not self.state["in_position"]:
            return False

        entry = self.state.get("entry_price", 0)
        premium = self.state["current_premium"]

        # ATR 기반 동적 손절 (데이터 있으면 ATR 사용, 없으면 고정 %)
        if entry > 0:
            atr_pct = self.atr.get_atr_pct(entry)
            stop_pct = (self.atr_stop_mult * atr_pct) if atr_pct is not None else self.max_loss_pct
            # 손절 판정
            current_local = self.state.get("_current_local_price", entry)
            if current_local <= entry * (1 - stop_pct):
                return True

        # 최소 보유 틱 미달이면 청산 안 함
        if self.state["ticks_in_position"] < self.min_hold_ticks:
            return False

        # OU z-score 기반 청산
        zscore = self.ou.get_zscore(premium)
        if zscore is not None and self.ou.is_mean_reverting():
            return zscore >= self.ou_exit_z
        else:
            # 폴백 → 기존 고정 임계값
            return premium >= self.exit_threshold

    def on_enter(self) -> None:
        """진입 확정 후 상태 갱신"""
        self.state["ticks_in_position"] = 0

    def on_exit(self) -> None:
        """청산 확정 후 상태 갱신"""
        self.state["ticks_in_position"] = 0
        self.state["cooldown_remaining"] = self.cooldown_ticks

    def position_size(self) -> float:
        return self.position_limit
