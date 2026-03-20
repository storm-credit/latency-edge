"""
Fractional Kelly 포지션 사이징

Half-Kelly 기준으로 승률과 손익비에 따라 최적 거래 크기 결정.
크립토 변동성을 고려해 Full Kelly의 50%만 사용 (보수적 접근).

논문 근거:
- Kelly (1956), "A New Interpretation of Information Rate"
- 크립토 시장에서는 10-25% Kelly 권장 (변동성 리스크)
"""
from collections import deque
from typing import Optional
from src.config import Config


class KellyPositionSizer:
    """Half-Kelly 기반 동적 포지션 사이징"""

    def __init__(self, max_fraction: float = 0.25, min_trades: int = 10,
                 history_size: int = 100):
        self.max_fraction = max_fraction  # 최대 배팅 비율
        self.min_trades = min_trades      # Kelly 활성화 최소 거래 수
        self._pnl_history: deque = deque(maxlen=history_size)

    def update(self, pnl: float) -> None:
        """거래 결과 기록"""
        self._pnl_history.append(pnl)

    def get_trade_size(self, available_capital: float) -> float:
        """최적 거래 크기 계산 (KRW)"""
        # 거래 이력 부족 → 고정 사이즈 폴백
        if len(self._pnl_history) < self.min_trades:
            return min(Config.TRADE_SIZE_KRW, available_capital)

        wins = [p for p in self._pnl_history if p > 0]
        losses = [p for p in self._pnl_history if p < 0]

        # 승리 또는 패배가 없으면 폴백
        if not wins or not losses:
            return min(Config.TRADE_SIZE_KRW, available_capital)

        win_rate = len(wins) / len(self._pnl_history)
        avg_win = sum(wins) / len(wins)
        avg_loss = abs(sum(losses) / len(losses))

        if avg_loss == 0:
            return min(Config.TRADE_SIZE_KRW, available_capital)

        # Kelly 공식: f* = p - (1-p)/b, where b = avg_win/avg_loss
        b = avg_win / avg_loss
        f_star = win_rate - (1 - win_rate) / b

        # Half-Kelly (보수적)
        half_kelly = max(0.0, f_star / 2)

        # 클램프: [5%, max_fraction] of available capital
        fraction = min(half_kelly, self.max_fraction)
        fraction = max(fraction, 0.05)  # 최소 5%

        trade_size = available_capital * fraction

        # 최소/최대 거래 크기 제한
        trade_size = max(trade_size, 100_000)   # 최소 10만원
        trade_size = min(trade_size, available_capital)  # 가용 자본 초과 불가

        return trade_size

    @property
    def stats(self) -> dict:
        """현재 Kelly 통계"""
        if len(self._pnl_history) < 2:
            return {"trades": len(self._pnl_history), "kelly_active": False}

        wins = [p for p in self._pnl_history if p > 0]
        losses = [p for p in self._pnl_history if p < 0]
        win_rate = len(wins) / len(self._pnl_history) if self._pnl_history else 0

        return {
            "trades": len(self._pnl_history),
            "win_rate": win_rate,
            "kelly_active": len(self._pnl_history) >= self.min_trades,
        }
