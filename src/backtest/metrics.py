import pandas as pd
import numpy as np
from typing import List, Dict, Any

def calculate_metrics(trades: List[Dict[str, Any]], equity_curve: List[float]) -> Dict[str, float]:
    """백테스트 결과 분석기"""
    if not trades:
        return {"win_rate": 0.0, "profit_factor": 0.0, "mdd": 0.0}

    df_trades = pd.DataFrame(trades)
    wins = df_trades[df_trades['pnl'] > 0]
    losses = df_trades[df_trades['pnl'] <= 0]
    
    win_rate = len(wins) / len(trades) if len(trades) > 0 else 0.0
    
    gross_profit = wins['pnl'].sum() if not wins.empty else 0.0
    gross_loss = abs(losses['pnl'].sum()) if not losses.empty else 0.0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')
    
    # MDD Calculation
    equity_series = pd.Series(equity_curve)
    rolling_max = equity_series.cummax()
    drawdowns = (rolling_max - equity_series) / rolling_max
    mdd = drawdowns.max()

    return {
        "win_rate": round(win_rate, 4),
        "profit_factor": round(profit_factor, 4),
        "mdd": round(mdd, 4)
    }
