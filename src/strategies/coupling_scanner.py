"""
실시간 커플링 스캐너

업비트 전체 코인의 가격 수익률을 실시간 추적하고,
롤링 상관계수가 임계값을 넘는 쌍이 발견되면 이벤트 발생.
커플링 감지 → PairTrading 전략 자동 활성화.

흐름:
1. 모든 코인 틱 수신 → 수익률 deque 축적
2. 주기적으로 (N틱마다) 모든 쌍의 상관계수 계산
3. 상관 > 0.7 → 커플링 감지 → PairTrading에 쌍 등록
4. 상관 < 0.4 → 커플링 해제 → PairTrading에서 쌍 제거
"""
from collections import deque
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class CoinTracker:
    """개별 코인 수익률 추적"""

    def __init__(self, window: int = 60):
        self.returns: deque = deque(maxlen=window)
        self._last_price: float = 0.0
        self.price: float = 0.0

    def update(self, price: float) -> None:
        if price <= 0:
            return
        if self._last_price > 0:
            ret = (price - self._last_price) / self._last_price
            self.returns.append(ret)
        self._last_price = price
        self.price = price

    @property
    def ready(self) -> bool:
        return len(self.returns) >= 30  # 최소 30틱


def _correlation(a: list, b: list) -> float:
    """두 수익률 시계열의 상관계수"""
    n = min(len(a), len(b))
    if n < 20:
        return 0.0
    a, b = a[-n:], b[-n:]
    ma = sum(a) / n
    mb = sum(b) / n
    cov = sum((a[i] - ma) * (b[i] - mb) for i in range(n)) / n
    sa = (sum((x - ma) ** 2 for x in a) / n) ** 0.5
    sb = (sum((x - mb) ** 2 for x in b) / n) ** 0.5
    if sa > 0 and sb > 0:
        return cov / (sa * sb)
    return 0.0


class CouplingScanner:
    """
    실시간 커플링 스캐너

    모든 코인 쌍의 상관관계를 롤링으로 계산하고,
    커플링이 형성/해제되는 순간을 감지.
    """

    def __init__(self, symbols: List[str],
                 couple_threshold: float = 0.7,
                 decouple_threshold: float = 0.4,
                 window: int = 60,
                 scan_interval: int = 10):
        self.couple_threshold = couple_threshold
        self.decouple_threshold = decouple_threshold
        self.scan_interval = scan_interval  # N틱마다 스캔

        # 코인별 트래커
        self.trackers: Dict[str, CoinTracker] = {
            sym: CoinTracker(window=window) for sym in symbols
        }

        # 현재 커플링 중인 쌍: {("A","B"): correlation}
        self.coupled_pairs: Dict[Tuple[str, str], float] = {}

        # 이벤트 로그
        self._tick_count: int = 0
        self._events: List[Dict] = []

    def add_symbol(self, symbol: str) -> None:
        """동적으로 코인 추가"""
        if symbol not in self.trackers:
            self.trackers[symbol] = CoinTracker()

    def on_tick(self, symbol: str, price: float) -> List[Dict]:
        """
        틱 수신 → 스캔 주기마다 커플링 체크

        Returns: 새로 발생한 이벤트 목록
        [{"type": "COUPLED", "pair": ("A","B"), "correlation": 0.85}, ...]
        [{"type": "DECOUPLED", "pair": ("A","B"), "correlation": 0.35}, ...]
        """
        if symbol in self.trackers:
            self.trackers[symbol].update(price)

        self._tick_count += 1
        if self._tick_count % self.scan_interval != 0:
            return []

        return self._scan()

    def _scan(self) -> List[Dict]:
        """전체 쌍 스캔"""
        events = []
        ready_syms = [s for s, t in self.trackers.items() if t.ready]

        if len(ready_syms) < 2:
            return events

        # 모든 쌍 체크
        for i in range(len(ready_syms)):
            for j in range(i + 1, len(ready_syms)):
                a, b = ready_syms[i], ready_syms[j]
                pair = (a, b) if a < b else (b, a)  # 정렬된 키

                corr = _correlation(
                    list(self.trackers[a].returns),
                    list(self.trackers[b].returns),
                )

                was_coupled = pair in self.coupled_pairs

                if not was_coupled and corr >= self.couple_threshold:
                    # 새로 커플링 감지!
                    self.coupled_pairs[pair] = corr
                    event = {
                        "type": "COUPLED",
                        "pair": pair,
                        "coin_a": pair[0],
                        "coin_b": pair[1],
                        "correlation": round(corr, 3),
                        "price_a": self.trackers[pair[0]].price,
                        "price_b": self.trackers[pair[1]].price,
                    }
                    events.append(event)
                    logger.info(f"[CouplingScanner] COUPLED: {pair[0]}-{pair[1]} corr={corr:.3f}")

                elif was_coupled and corr < self.decouple_threshold:
                    # 커플링 해제
                    del self.coupled_pairs[pair]
                    event = {
                        "type": "DECOUPLED",
                        "pair": pair,
                        "coin_a": pair[0],
                        "coin_b": pair[1],
                        "correlation": round(corr, 3),
                    }
                    events.append(event)
                    logger.info(f"[CouplingScanner] DECOUPLED: {pair[0]}-{pair[1]} corr={corr:.3f}")

                elif was_coupled:
                    # 업데이트만
                    self.coupled_pairs[pair] = corr

        self._events.extend(events)
        return events

    def get_coupled_pairs(self) -> List[Dict]:
        """현재 커플링 중인 모든 쌍"""
        result = []
        for (a, b), corr in self.coupled_pairs.items():
            result.append({
                "coin_a": a,
                "coin_b": b,
                "correlation": round(corr, 3),
                "price_a": self.trackers[a].price if a in self.trackers else 0,
                "price_b": self.trackers[b].price if b in self.trackers else 0,
            })
        result.sort(key=lambda x: x["correlation"], reverse=True)
        return result

    def get_recent_events(self, limit: int = 20) -> List[Dict]:
        """최근 이벤트"""
        return self._events[-limit:]

    @property
    def stats(self) -> Dict:
        return {
            "tracking": len(self.trackers),
            "ready": sum(1 for t in self.trackers.values() if t.ready),
            "coupled_pairs": len(self.coupled_pairs),
            "total_possible_pairs": len(self.trackers) * (len(self.trackers) - 1) // 2,
            "ticks_processed": self._tick_count,
        }
