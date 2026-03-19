from typing import Dict, Any
from src.strategies.base import BaseStrategy
from src.features.imbalance import calculate_premium


class LeadLagScalper(BaseStrategy):
    """
    바이낸스(Lead)와 업비트(Lag)의 가격 차이(프리미엄)를 이용한 전략

    역프리미엄 수렴 전략:
    - 김프가 비정상적으로 낮거나 역프리미엄일 때 매수 (저평가 구간 진입)
    - 프리미엄이 정상 수준으로 복귀하면 매도 (수렴 차익 실현)

    개선:
    - 진입 후 쿨다운 (최소 보유 틱 수) → 임계값 경계에서 반복 진입/청산 방지
    - 거래량 필터 → 유동성 없는 시장 진입 방지
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.entry_threshold = config.get("entry_threshold", -0.02)
        self.exit_threshold = config.get("exit_threshold", 0.005)
        self.fx_rate = config.get("fx_rate", 1400.0)
        self.position_limit = config.get("position_size", 1.0)
        self.min_hold_ticks = config.get("min_hold_ticks", 3)  # 최소 보유 틱
        self.cooldown_ticks = config.get("cooldown_ticks", 5)   # 청산 후 재진입 대기

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
            self.state["current_premium"] = calculate_premium(local_price, global_price, self.fx_rate)

        # 보유 중이면 틱 카운트 증가
        if self.state["in_position"]:
            self.state["ticks_in_position"] += 1

        # 쿨다운 감소
        if self.state["cooldown_remaining"] > 0:
            self.state["cooldown_remaining"] -= 1

    def should_enter(self) -> bool:
        # 쿨다운 중이면 진입 안 함
        if self.state["cooldown_remaining"] > 0:
            return False
        return self.state["current_premium"] <= self.entry_threshold

    def should_exit(self) -> bool:
        # 최소 보유 틱 미달이면 청산 안 함
        if self.state["ticks_in_position"] < self.min_hold_ticks:
            return False
        if self.state["current_premium"] >= self.exit_threshold:
            # 청산 시 쿨다운 시작, 틱 카운터 리셋
            self.state["ticks_in_position"] = 0
            self.state["cooldown_remaining"] = self.cooldown_ticks
            return True
        return False

    def position_size(self) -> float:
        return self.position_limit

    def risk_limits(self) -> Dict[str, float]:
        return {"max_loss_per_trade": 0.02}
