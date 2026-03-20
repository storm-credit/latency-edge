"""
Donchian Channel 앙상블

여러 lookback 기간의 Donchian Channel을 결합하여 더 안정적인 돌파 시그널 생성.
단일 lookback 대비 노이즈 필터링 효과.

논문: "Catching Crypto Trends" (Zarattini et al., 2025)
- 앙상블 Donchian: CAGR 30%, Sharpe 1.58, MDD 19%
"""
from collections import deque
from typing import List, Optional


class DonchianChannel:
    """단일 Donchian Channel"""

    def __init__(self, period: int):
        self.period = period
        self._prices: deque = deque(maxlen=period)

    def update(self, price: float) -> None:
        if price > 0:
            self._prices.append(price)

    @property
    def ready(self) -> bool:
        return len(self._prices) >= self.period

    @property
    def upper(self) -> Optional[float]:
        """상단 밴드 (N틱 최고가)"""
        if not self.ready:
            return None
        return max(self._prices)

    @property
    def lower(self) -> Optional[float]:
        """하단 밴드 (N틱 최저가)"""
        if not self.ready:
            return None
        return min(self._prices)

    @property
    def mid(self) -> Optional[float]:
        """중간선"""
        if not self.ready:
            return None
        return (max(self._prices) + min(self._prices)) / 2


class DonchianEnsemble:
    """
    다중 기간 Donchian Channel 앙상블

    여러 lookback(예: 5, 10, 20)의 돌파 시그널을 투표 방식으로 결합.
    과반수 이상 채널에서 돌파 시 진입 시그널 발생.
    """

    def __init__(self, periods: List[int] | None = None, min_votes: int | None = None):
        self.periods = periods or [5, 10, 20]
        self.channels = [DonchianChannel(p) for p in self.periods]
        # 과반수 이상 필요 (기본: ceil(n/2))
        self.min_votes = min_votes or (len(self.channels) // 2 + 1)

    def update(self, price: float) -> None:
        """모든 채널에 가격 피드"""
        for ch in self.channels:
            ch.update(price)

    def breakout_signal(self, current_price: float) -> bool:
        """상향 돌파 앙상블 시그널 (투표)"""
        votes = 0
        for ch in self.channels:
            if ch.ready and ch.upper is not None:
                # 현재 가격이 채널 상단 돌파
                if current_price > ch.upper:
                    votes += 1
        return votes >= self.min_votes

    def breakdown_signal(self, current_price: float) -> bool:
        """하향 이탈 시그널 (청산용 — 단기 채널 기준)"""
        # 가장 짧은 기간 채널의 하단 이탈 시 청산
        shortest = self.channels[0]
        if shortest.ready and shortest.lower is not None:
            return current_price < shortest.lower
        return False

    @property
    def ready(self) -> bool:
        """최소 과반수 채널이 준비 완료"""
        ready_count = sum(1 for ch in self.channels if ch.ready)
        return ready_count >= self.min_votes
