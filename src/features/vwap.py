"""
VWAP (Volume Weighted Average Price) 계산기

롤링 VWAP 및 가격 이탈도 측정.
VWAP 이하 = 일시적 저평가 → LeadLag 진입 보조 확인.
VWAP 이상 = 매수 모멘텀 → Momentum 돌파 확인.

논문: "Deep Learning for VWAP Execution in Crypto Markets" (2025)
"""
from collections import deque
from typing import Optional


class VWAPCalculator:
    """롤링 VWAP 계산기"""

    def __init__(self, window: int = 50):
        self.window = window
        self._prices: deque = deque(maxlen=window)
        self._volumes: deque = deque(maxlen=window)

    def update(self, price: float, volume: float) -> None:
        """가격/거래량 쌍 추가"""
        if price > 0 and volume >= 0:
            self._prices.append(price)
            self._volumes.append(volume)

    @property
    def ready(self) -> bool:
        return len(self._prices) >= 10  # 최소 10틱

    def get_vwap(self) -> Optional[float]:
        """현재 VWAP 반환"""
        if not self.ready:
            return None
        total_vol = sum(self._volumes)
        if total_vol == 0:
            return None
        pv_sum = sum(p * v for p, v in zip(self._prices, self._volumes))
        return pv_sum / total_vol

    def get_deviation(self, current_price: float) -> Optional[float]:
        """
        현재 가격의 VWAP 대비 이탈도 반환
        양수 = VWAP 위 (매수 모멘텀), 음수 = VWAP 아래 (저평가)
        단위: 비율 (0.01 = 1%)
        """
        vwap = self.get_vwap()
        if vwap is None or vwap == 0:
            return None
        return (current_price - vwap) / vwap

    def is_below_vwap(self, current_price: float, threshold: float = -0.005) -> bool:
        """가격이 VWAP 대비 threshold 이하인지 (기본: -0.5%)"""
        dev = self.get_deviation(current_price)
        if dev is None:
            return False
        return dev <= threshold

    def is_above_vwap(self, current_price: float, threshold: float = 0.005) -> bool:
        """가격이 VWAP 대비 threshold 이상인지 (기본: +0.5%)"""
        dev = self.get_deviation(current_price)
        if dev is None:
            return False
        return dev >= threshold
