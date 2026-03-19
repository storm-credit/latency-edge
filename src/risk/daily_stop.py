from datetime import date


class DailyRiskManager:
    def __init__(self, max_daily_loss: float, max_consecutive_losses: int):
        self.max_daily_loss = max_daily_loss
        self.max_consecutive_losses = max_consecutive_losses
        self.current_loss = 0.0
        self.consecutive_losses = 0
        self._last_reset_date = date.today()

    def _auto_reset_if_new_day(self):
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

    def update_result(self, pnl: float):
        """거래 결과 수신 후 내부 상태 갱신"""
        if pnl < 0:
            self.current_loss += abs(pnl)
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

    def reset_daily(self):
        """일일 리셋 (매일 장 시작 시 호출)"""
        self.current_loss = 0.0
        self.consecutive_losses = 0
