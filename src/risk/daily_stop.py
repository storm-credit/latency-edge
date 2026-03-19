class DailyRiskManager:
    def __init__(self, max_daily_loss: float, max_consecutive_losses: int):
        self.max_daily_loss = max_daily_loss
        self.max_consecutive_losses = max_consecutive_losses
        self.current_loss = 0.0
        self.consecutive_losses = 0

    def check_trade_allowed(self) -> bool:
        """누적 손실 및 연속 손실 횟수에 따른 매매 허용 여부 판별"""
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
