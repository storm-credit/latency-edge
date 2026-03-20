"""
Trade Flow Imbalance (TFI)

틱 데이터에서 매수/매도 압력을 추정.
Tick Rule: 가격 상승 = 매수 주도, 가격 하락 = 매도 주도.

논문:
- "Order flow analysis of cryptocurrency markets" (2019)
- "Order Flow and Cryptocurrency Returns" (2025)

활용:
- LeadLag: TFI < 0 (매도 압력) 시 진입 보조 → 가격 회복 가능성 ↑
- Momentum: TFI > 0 (매수 압력) 시 돌파 확인 → 허위 돌파 필터링
"""
from collections import deque
from typing import Optional


class TradeFlowImbalance:
    """틱 기반 매수/매도 흐름 불균형 측정"""

    def __init__(self, window: int = 20):
        self.window = window
        self._buyer_vol: deque = deque(maxlen=window)
        self._seller_vol: deque = deque(maxlen=window)
        self._last_price: Optional[float] = None

    def update(self, price: float, volume: float) -> None:
        """틱 업데이트 → Tick Rule로 매수/매도 분류"""
        if price <= 0 or volume <= 0:
            return

        if self._last_price is not None:
            if price > self._last_price:
                # 가격 상승 → 매수 주도
                self._buyer_vol.append(volume)
                self._seller_vol.append(0.0)
            elif price < self._last_price:
                # 가격 하락 → 매도 주도
                self._buyer_vol.append(0.0)
                self._seller_vol.append(volume)
            else:
                # 가격 동일 → 이전 방향 유지 (반반 분배)
                half = volume / 2
                self._buyer_vol.append(half)
                self._seller_vol.append(half)

        self._last_price = price

    @property
    def ready(self) -> bool:
        return len(self._buyer_vol) >= self.window

    def get_tfi(self) -> Optional[float]:
        """
        Trade Flow Imbalance 반환
        범위: -1.0 (전부 매도) ~ +1.0 (전부 매수)
        """
        if not self.ready:
            return None
        total_buy = sum(self._buyer_vol)
        total_sell = sum(self._seller_vol)
        total = total_buy + total_sell
        if total == 0:
            return 0.0
        return (total_buy - total_sell) / total

    def is_buying_pressure(self, threshold: float = 0.3) -> bool:
        """매수 압력 확인 (TFI > threshold)"""
        tfi = self.get_tfi()
        return tfi is not None and tfi > threshold

    def is_selling_pressure(self, threshold: float = -0.3) -> bool:
        """매도 압력 확인 (TFI < threshold)"""
        tfi = self.get_tfi()
        return tfi is not None and tfi < threshold
