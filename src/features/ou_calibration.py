"""
Ornstein-Uhlenbeck 프로세스 캘리브레이션

김치 프리미엄의 평균 회귀 특성을 OU 프로세스로 모델링:
  dS = theta * (mu - S) * dt + sigma * dW

논문 근거:
- "Nonlinear dynamics of Kimchi premium" (Economic Modelling, 2024)
- BTC 김프 반감기(half-life) ≈ 24분
"""
import numpy as np
from collections import deque
from typing import Dict, Optional


class OUCalibrator:
    """롤링 윈도우 기반 OU 프로세스 실시간 캘리브레이션"""

    def __init__(self, lookback: int = 60):
        self.lookback = lookback
        self.history: deque = deque(maxlen=lookback)
        self._params: Optional[Dict[str, float]] = None

    def update(self, premium: float) -> None:
        """프리미엄 값 추가 및 OU 파라미터 재추정"""
        self.history.append(premium)
        if len(self.history) >= 20:  # 최소 20틱으로 캘리브레이션
            self._calibrate()

    def _calibrate(self) -> None:
        """OLS 기반 OU 파라미터 추정: dS = a + b*S → theta=-b, mu=a/theta"""
        series = np.array(self.history)
        y = np.diff(series)
        x = series[:-1]

        n = len(x)
        if n < 10:
            return

        # OLS: y = a + b*x
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        ss_xx = np.sum((x - x_mean) ** 2)

        if ss_xx == 0:
            return

        b = np.sum((x - x_mean) * (y - y_mean)) / ss_xx
        a = y_mean - b * x_mean

        theta = -b  # 평균 회귀 속도
        if theta <= 0:
            # 평균 회귀 아님 → 랜덤워크 구간
            self._params = None
            return

        mu = a / theta  # 장기 평균
        residuals = y - (a + b * x)
        sigma = np.std(residuals)
        half_life = np.log(2) / theta if theta > 0 else float('inf')
        sigma_eq = sigma / np.sqrt(2 * theta)  # 균형 표준편차

        self._params = {
            "theta": theta,
            "mu": mu,
            "sigma": sigma,
            "half_life": half_life,
            "sigma_eq": sigma_eq,
        }

    def get_zscore(self, current_premium: float) -> Optional[float]:
        """현재 프리미엄의 z-score 반환 (OU 기준)"""
        if self._params is None or self._params["sigma_eq"] <= 0:
            return None
        return (current_premium - self._params["mu"]) / self._params["sigma_eq"]

    def is_mean_reverting(self) -> bool:
        """현재 구간이 평균 회귀 특성을 보이는지 판정"""
        if self._params is None:
            return False
        # 반감기가 너무 길면 (60틱 초과) 평균 회귀 아님
        return self._params["half_life"] < 60

    @property
    def params(self) -> Optional[Dict[str, float]]:
        return self._params
