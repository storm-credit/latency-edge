"""
다중 코인 프리미엄 추적 + 빗각 전략

여러 코인의 바이낸스-업비트 프리미엄을 동시 추적하고,
역프리미엄이 가장 큰 코인에 진입하는 전략.

기존 LeadLag(BTC 단일)을 다중 코인으로 확장.
OU 캘리브레이터를 코인별로 독립 운영.
"""
from typing import Dict, Any, List, Optional
from collections import deque
from src.features.ou_calibration import OUCalibrator
from src.features.imbalance import calculate_premium
from src.config import Config


class CoinPremiumState:
    """개별 코인의 프리미엄 추적 상태"""

    def __init__(self, symbol: str, fx_rate: float, ou_lookback: int = 60):
        self.symbol = symbol
        self.fx_rate = fx_rate
        self.ou = OUCalibrator(lookback=ou_lookback)

        self.upbit_price: float = 0.0
        self.binance_price: float = 0.0
        self.premium: float = 0.0
        self.zscore: Optional[float] = None
        self.volume: float = 0.0

    def update_upbit(self, price: float, volume: float = 0.0) -> None:
        if price > 0:
            self.upbit_price = price
            self.volume = volume
            self._recalc()

    def update_binance(self, price: float) -> None:
        if price > 0:
            self.binance_price = price
            self._recalc()

    def _recalc(self) -> None:
        if self.upbit_price > 0 and self.binance_price > 0:
            self.premium = calculate_premium(
                self.upbit_price, self.binance_price, self.fx_rate
            )
            self.ou.update(self.premium)
            self.zscore = self.ou.get_zscore(self.premium)


class MultiPremiumStrategy:
    """
    다중 코인 프리미엄 차익 전략 (빗각)

    모든 추적 코인의 프리미엄을 동시 모니터링하고,
    역프리미엄(z-score 기준) 상위 코인에 진입.
    """

    def __init__(self, symbols: List[str], config: Dict[str, Any] | None = None):
        config = config or {}
        self.fx_rate = config.get("fx_rate", Config.FX_RATE)
        self.ou_lookback = config.get("ou_lookback", Config.OU_LOOKBACK)
        self.entry_zscore = config.get("ou_entry_zscore", Config.OU_ENTRY_ZSCORE)
        self.exit_zscore = config.get("ou_exit_zscore", Config.OU_EXIT_ZSCORE)
        self.entry_threshold = config.get("entry_threshold", Config.LL_ENTRY_THRESHOLD)
        self.exit_threshold = config.get("exit_threshold", Config.LL_EXIT_THRESHOLD)
        self.max_positions = config.get("max_positions", 3)  # 동시 최대 포지션

        # 코인별 상태
        self.coins: Dict[str, CoinPremiumState] = {
            sym: CoinPremiumState(sym, self.fx_rate, self.ou_lookback)
            for sym in symbols
        }

        # 포지션 추적
        self.positions: Dict[str, Dict[str, Any]] = {}  # symbol → {entry_price, entry_premium, ...}

    def on_tick(self, symbol: str, exchange: str, price: float, volume: float = 0.0) -> None:
        """개별 코인 틱 업데이트"""
        if symbol not in self.coins:
            return
        coin = self.coins[symbol]
        if exchange == "upbit":
            coin.update_upbit(price, volume)
        elif exchange == "binance":
            coin.update_binance(price)

    def get_entry_candidates(self) -> List[str]:
        """진입 후보 코인 목록 (z-score 기준 역프리미엄 상위)"""
        if len(self.positions) >= self.max_positions:
            return []

        candidates = []
        for sym, coin in self.coins.items():
            if sym in self.positions:
                continue  # 이미 보유 중
            if coin.upbit_price <= 0 or coin.binance_price <= 0:
                continue  # 데이터 미수신

            # OU z-score 기반 또는 폴백
            if coin.zscore is not None and coin.ou.is_mean_reverting():
                if coin.zscore <= self.entry_zscore:
                    candidates.append((sym, coin.zscore))
            else:
                if coin.premium <= self.entry_threshold:
                    candidates.append((sym, coin.premium * 100))  # 비교용 스케일

        # z-score(또는 프리미엄)가 가장 낮은 순서로 정렬
        candidates.sort(key=lambda x: x[1])
        available_slots = self.max_positions - len(self.positions)
        return [sym for sym, _ in candidates[:available_slots]]

    def get_exit_candidates(self) -> List[str]:
        """청산 후보 코인 목록"""
        exits = []
        for sym in list(self.positions.keys()):
            if sym not in self.coins:
                continue
            coin = self.coins[sym]

            # OU z-score 기반 또는 폴백
            if coin.zscore is not None and coin.ou.is_mean_reverting():
                if coin.zscore >= self.exit_zscore:
                    exits.append(sym)
            else:
                if coin.premium >= self.exit_threshold:
                    exits.append(sym)

        return exits

    def enter(self, symbol: str) -> None:
        """포지션 진입 기록"""
        coin = self.coins.get(symbol)
        if coin:
            self.positions[symbol] = {
                "entry_price": coin.upbit_price,
                "entry_premium": coin.premium,
                "entry_zscore": coin.zscore,
            }

    def exit(self, symbol: str) -> Optional[Dict[str, Any]]:
        """포지션 청산 → 진입 정보 반환"""
        return self.positions.pop(symbol, None)

    def get_dashboard_data(self) -> List[Dict[str, Any]]:
        """대시보드용 전체 코인 프리미엄 현황"""
        result = []
        for sym, coin in self.coins.items():
            result.append({
                "symbol": sym,
                "upbit_price": coin.upbit_price,
                "binance_price": coin.binance_price,
                "premium": round(coin.premium * 100, 3),  # %
                "zscore": round(coin.zscore, 2) if coin.zscore is not None else None,
                "in_position": sym in self.positions,
                "mean_reverting": coin.ou.is_mean_reverting(),
            })
        result.sort(key=lambda x: x["premium"])
        return result
