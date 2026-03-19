from datetime import date


class DailyRiskManager:
    """
    일일 리스크 관리자
    - 일일 누적 손실이 한도 초과 시 매매 차단
    - 연속 손실 횟수 초과 시 매매 차단
    - 날짜 변경 시 자동 리셋
    Note: current_loss는 단방향 누적 (수익으로 감소하지 않음 — 보수적 설계)
    """
    def __init__(self, max_daily_loss: float, max_consecutive_losses: int) -> None:
        self.max_daily_loss = max_daily_loss
        self.max_consecutive_losses = max_consecutive_losses
        self.current_loss: float = 0.0
        self.consecutive_losses: int = 0
        self._last_reset_date: date = date.today()

    def _auto_reset_if_new_day(self) -> None:
        """날짜가 바뀌면 자동으로 일일 카운터 리셋"""
        today = date.today()
        if today > self._last_reset_date:
            self.reset_daily()
            self._last_reset_date = today

    def check_trade_allowed(self) -> bool:
        """누적 손실 및 연속 손실 횟수에 따른 매매 허용 여부 판별"""
        self._auto_reset_if_new_day()
        if self.current_loss >= self.max_daily_loss:
            return False
        if self.consecutive_losses >= self.max_consecutive_losses:
            return False
        return True

    def update_result(self, pnl: float) -> None:
        """거래 결과 수신 후 내부 상태 갱신 (손실만 누적, 수익은 연속 손실 카운터만 리셋)"""
        if pnl < 0:
            self.current_loss += abs(pnl)
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

    def reset_daily(self) -> None:
        """일일 리셋 (매일 장 시작 시 또는 자동 호출)"""
        self.current_loss = 0.0
        self.consecutive_losses = 0
