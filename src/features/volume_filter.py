"""
거래량 퍼센타일 필터

고정 배수(avg * 1.5x) 대신 롤링 퍼센타일 기반 거래량 필터.
변동하는 거래량 레짐에 자동 적응.
"""
from collections import deque
from typing import Optional


class VolumePercentileFilter:
    """롤링 윈도우 기반 거래량 퍼센타일 판정"""

    def __init__(self, window: int = 50, threshold_pct: float = 90.0):
        self.window = window
        self.threshold_pct = threshold_pct
        self._volumes: deque = deque(maxlen=window)

    def update(self, volume: float) -> None:
        """거래량 추가"""
        if volume >= 0:
            self._volumes.append(volume)

    @property
    def ready(self) -> bool:
        return len(self._volumes) >= self.window

    def is_surge(self, current_volume: float) -> bool:
        """현재 거래량이 퍼센타일 임계값 초과인지 판정"""
        if not self.ready:
            return False  # 데이터 부족 시 판정 불가 → 호출자가 폴백 사용
        sorted_vols = sorted(self._volumes)
        idx = int(len(sorted_vols) * self.threshold_pct / 100)
        idx = min(idx, len(sorted_vols) - 1)
        return current_volume > sorted_vols[idx]

    def get_percentile(self, current_volume: float) -> Optional[float]:
        """현재 거래량의 퍼센타일 위치 반환 (0-100)"""
        if not self.ready:
            return None
        count_below = sum(1 for v in self._volumes if v < current_volume)
        return (count_below / len(self._volumes)) * 100
