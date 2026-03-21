"""
페어 트레이딩 전략 — 커플링 이탈 차익

평소 커플링(높은 상관관계)된 코인 쌍의 스프레드를 OU 프로세스로 추적.
스프레드가 평균에서 크게 이탈(커플링 깨짐)하면 진입,
평균으로 수렴(커플링 복귀)하면 청산.

핵심 아이디어:
- 커플링 = 두 코인의 가격 비율이 일정 범위 내에서 유지
- 깨짐 = 비율이 ±2σ 이상 이탈 → 매매 기회
- 복귀 = 비율이 평균으로 돌아옴 → 수익 확정
"""
from typing import Dict, Any, List, Optional, Tuple
from collections import deque
from src.features.ou_calibration import OUCalibrator
from src.config import Config


class PairState:
    """개별 페어의 스프레드 추적 상태"""

    def __init__(self, coin_a: str, coin_b: str, ou_lookback: int = 60):
        self.coin_a = coin_a  # 기준 코인
        self.coin_b = coin_b  # 상대 코인
        self.ou = OUCalibrator(lookback=ou_lookback)

        self.price_a: float = 0.0
        self.price_b: float = 0.0
        self.spread: float = 0.0  # log(price_a / price_b) 또는 비율
        self.zscore: Optional[float] = None

        # 롤링 상관계수용
        self._returns_a: deque = deque(maxlen=120)
        self._returns_b: deque = deque(maxlen=120)
        self._prev_a: float = 0.0
        self._prev_b: float = 0.0

    def update(self, coin: str, price: float) -> None:
        """가격 업데이트"""
        if price <= 0:
            return

        if coin == self.coin_a:
            if self._prev_a > 0:
                self._returns_a.append((price - self._prev_a) / self._prev_a)
            self._prev_a = price
            self.price_a = price
        elif coin == self.coin_b:
            if self._prev_b > 0:
                self._returns_b.append((price - self._prev_b) / self._prev_b)
            self._prev_b = price
            self.price_b = price

        # 스프레드 재계산
        if self.price_a > 0 and self.price_b > 0:
            self.spread = self.price_a / self.price_b
            self.ou.update(self.spread)
            self.zscore = self.ou.get_zscore(self.spread)

    @property
    def correlation(self) -> Optional[float]:
        """롤링 상관계수"""
        if len(self._returns_a) < 30 or len(self._returns_b) < 30:
            return None
        n = min(len(self._returns_a), len(self._returns_b))
        a = list(self._returns_a)[-n:]
        b = list(self._returns_b)[-n:]
        ma = sum(a) / n
        mb = sum(b) / n
        cov = sum((a[i] - ma) * (b[i] - mb) for i in range(n)) / n
        sa = (sum((x - ma) ** 2 for x in a) / n) ** 0.5
        sb = (sum((x - mb) ** 2 for x in b) / n) ** 0.5
        if sa > 0 and sb > 0:
            return cov / (sa * sb)
        return None

    @property
    def is_coupled(self) -> bool:
        """현재 커플링 상태인지 (상관계수 0.6+)"""
        c = self.correlation
        return c is not None and c >= 0.6


class PairTradingStrategy:
    """
    다중 페어 트레이딩 전략

    - 여러 코인 쌍의 커플링을 동시 모니터링
    - 커플링이 깨지는 순간 (z-score ±2) 진입
    - 커플링 복귀 (z-score → 0) 시 청산
    """

    def __init__(self, pairs: List[Tuple[str, str]], config: Dict[str, Any] | None = None):
        config = config or {}
        ou_lookback = config.get("ou_lookback", Config.OU_LOOKBACK)
        self.entry_zscore = config.get("entry_zscore", 2.0)  # |z| > 2 진입
        self.exit_zscore = config.get("exit_zscore", 0.5)    # |z| < 0.5 청산
        self.min_correlation = config.get("min_correlation", 0.6)
        self.max_positions = config.get("max_positions", 2)

        # 페어별 상태
        self.pairs: Dict[str, PairState] = {}
        for a, b in pairs:
            key = f"{a}-{b}"
            self.pairs[key] = PairState(a, b, ou_lookback)

        # 포지션: key → {"direction": "long_a" or "long_b", ...}
        self.positions: Dict[str, Dict[str, Any]] = {}

    def on_tick(self, coin: str, price: float) -> None:
        """코인 가격 업데이트 → 모든 관련 페어 갱신"""
        for key, pair in self.pairs.items():
            if coin in (pair.coin_a, pair.coin_b):
                pair.update(coin, price)

    def get_signals(self) -> List[Dict[str, Any]]:
        """진입/청산 시그널 생성"""
        signals = []

        for key, pair in self.pairs.items():
            # 청산 체크 (보유 중인 포지션)
            if key in self.positions:
                if pair.zscore is not None and abs(pair.zscore) <= self.exit_zscore:
                    signals.append({
                        "pair": key,
                        "action": "EXIT",
                        "zscore": pair.zscore,
                        "spread": pair.spread,
                        "correlation": pair.correlation,
                    })
                continue

            # 진입 체크
            if len(self.positions) >= self.max_positions:
                continue

            if not pair.is_coupled:
                continue  # 커플링 안 된 쌍은 스킵

            if not pair.ou.is_mean_reverting():
                continue  # 평균 회귀 안 하면 스킵

            if pair.zscore is None:
                continue

            # 커플링 깨짐 감지!
            if pair.zscore >= self.entry_zscore:
                # A가 B 대비 비쌈 → A 매도, B 매수 방향
                signals.append({
                    "pair": key,
                    "action": "ENTRY",
                    "direction": "long_b",  # B 매수 (상대적 저평가)
                    "zscore": pair.zscore,
                    "spread": pair.spread,
                    "coin_buy": pair.coin_b,
                    "coin_sell": pair.coin_a,
                    "correlation": pair.correlation,
                })
            elif pair.zscore <= -self.entry_zscore:
                # A가 B 대비 쌈 → A 매수, B 매도 방향
                signals.append({
                    "pair": key,
                    "action": "ENTRY",
                    "direction": "long_a",  # A 매수 (상대적 저평가)
                    "zscore": pair.zscore,
                    "spread": pair.spread,
                    "coin_buy": pair.coin_a,
                    "coin_sell": pair.coin_b,
                    "correlation": pair.correlation,
                })

        return signals

    def enter(self, pair_key: str, direction: str) -> None:
        """포지션 진입 기록"""
        pair = self.pairs.get(pair_key)
        if pair:
            self.positions[pair_key] = {
                "direction": direction,
                "entry_spread": pair.spread,
                "entry_zscore": pair.zscore,
            }

    def exit(self, pair_key: str) -> Optional[Dict[str, Any]]:
        """포지션 청산 → 진입 정보 반환"""
        return self.positions.pop(pair_key, None)

    def get_dashboard_data(self) -> List[Dict[str, Any]]:
        """대시보드용 전체 페어 현황"""
        result = []
        for key, pair in self.pairs.items():
            result.append({
                "pair": key,
                "coin_a": pair.coin_a,
                "coin_b": pair.coin_b,
                "price_a": pair.price_a,
                "price_b": pair.price_b,
                "spread": round(pair.spread, 6) if pair.spread else 0,
                "zscore": round(pair.zscore, 2) if pair.zscore is not None else None,
                "correlation": round(pair.correlation, 3) if pair.correlation is not None else None,
                "coupled": pair.is_coupled,
                "mean_reverting": pair.ou.is_mean_reverting(),
                "in_position": key in self.positions,
            })
        return result
