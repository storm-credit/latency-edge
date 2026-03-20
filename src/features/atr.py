"""
ATR (Average True Range) 계산기

틱 데이터에서 변동성을 실시간으로 추정.
OHLC 대신 틱 간 가격 변화의 절대값 이동평균 사용.

논문 근거:
- "Volatility-Adaptive Trend-Following Models in Cryptocurrency Markets" (2025)
- ATR 기반 동적 스탑이 고정 % 대비 MDD 50%+ 개선
"""
from collections import deque
from typing import Optional


class ATRCalculator:
    """틱 기반 ATR (Average True Range) 계산기"""

    def __init__(self, period: int = 14):
        self.period = period
        self._price_changes: deque = deque(maxlen=period)
        self._last_price: Optional[float] = None
        self._atr: Optional[float] = None

    def update(self, price: float) -> None:
        """새 가격으로 ATR 갱신"""
        if price <= 0:
            return

        if self._last_price is not None and self._last_price > 0:
            change = abs(price - self._last_price)
            self._price_changes.append(change)

            if len(self._price_changes) >= self.period:
                self._atr = sum(self._price_changes) / len(self._price_changes)

        self._last_price = price

    def get_atr(self) -> Optional[float]:
        """현재 ATR 값 반환 (데이터 부족 시 None)"""
        return self._atr

    def get_atr_pct(self, current_price: float) -> Optional[float]:
        """현재 가격 대비 ATR 비율 반환 (예: 0.01 = 1%)"""
        if self._atr is None or current_price <= 0:
            return None
        return self._atr / current_price
