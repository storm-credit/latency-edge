"""
EWMA 기반 변동성 레짐 감지

실시간 변동성을 EWMA로 추정하고, 고/저 변동성 레짐을 분류.
레짐에 따라 전략 파라미터를 자동 조절.

논문: "Volatility-Adaptive Trend-Following Models in Cryptocurrency Markets"
(Karassavidis et al., 2025)
"""
from collections import deque
from typing import Optional


class RegimeDetector:
    """
    EWMA 기반 변동성 레짐 감지

    - HIGH_VOL: 변동성이 장기 평균의 1.5배 이상 → 넓은 스탑, 작은 포지션
    - LOW_VOL: 변동성이 장기 평균의 0.7배 이하 → 좁은 스탑, 큰 포지션
    - NORMAL: 그 외
    """
    HIGH_VOL = "high"
    LOW_VOL = "low"
    NORMAL = "normal"

    def __init__(self, fast_span: int = 10, slow_span: int = 50,
                 high_threshold: float = 1.5, low_threshold: float = 0.7):
        self.fast_alpha = 2.0 / (fast_span + 1)
        self.slow_alpha = 2.0 / (slow_span + 1)
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold

        self._last_price: Optional[float] = None
        self._fast_ewma: Optional[float] = None  # 단기 변동성
        self._slow_ewma: Optional[float] = None  # 장기 변동성
        self._tick_count: int = 0

    def update(self, price: float) -> None:
        """가격 업데이트 → EWMA 변동성 갱신"""
        if price <= 0:
            return

        if self._last_price is not None and self._last_price > 0:
            ret = abs(price - self._last_price) / self._last_price  # 절대 수익률

            if self._fast_ewma is None:
                self._fast_ewma = ret
                self._slow_ewma = ret
            else:
                self._fast_ewma = self.fast_alpha * ret + (1 - self.fast_alpha) * self._fast_ewma
                self._slow_ewma = self.slow_alpha * ret + (1 - self.slow_alpha) * self._slow_ewma

            self._tick_count += 1

        self._last_price = price

    @property
    def regime(self) -> str:
        """현재 레짐 반환"""
        if self._fast_ewma is None or self._slow_ewma is None or self._slow_ewma == 0:
            return self.NORMAL
        if self._tick_count < 20:
            return self.NORMAL

        ratio = self._fast_ewma / self._slow_ewma
        if ratio >= self.high_threshold:
            return self.HIGH_VOL
        elif ratio <= self.low_threshold:
            return self.LOW_VOL
        return self.NORMAL

    def get_position_multiplier(self) -> float:
        """레짐별 포지션 크기 배수"""
        r = self.regime
        if r == self.HIGH_VOL:
            return 0.5   # 고변동성: 포지션 50% 축소
        elif r == self.LOW_VOL:
            return 1.3   # 저변동성: 포지션 30% 확대
        return 1.0       # 보통

    def get_stop_multiplier(self) -> float:
        """레짐별 스탑 배수"""
        r = self.regime
        if r == self.HIGH_VOL:
            return 1.5   # 고변동성: 스탑 50% 확대 (너무 빨리 손절 방지)
        elif r == self.LOW_VOL:
            return 0.8   # 저변동성: 스탑 20% 축소 (타이트한 관리)
        return 1.0

    @property
    def volatility_ratio(self) -> Optional[float]:
        """단기/장기 변동성 비율"""
        if self._fast_ewma is None or self._slow_ewma is None or self._slow_ewma == 0:
            return None
        return self._fast_ewma / self._slow_ewma
