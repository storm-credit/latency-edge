import pandas as pd
from typing import Any, Dict, List
from src.strategies.base import BaseStrategy
from src.backtest.slippage import SlippageModel

class BacktestEngine:
    def __init__(self, strategy: BaseStrategy, slippage_model: SlippageModel, initial_capital: float = 10000.0):
        self.strategy = strategy
        self.slippage_model = slippage_model
        self.capital = initial_capital
        self.trades: List[Dict[str, Any]] = []
        self.equity_curve: List[float] = []

    def run(self, data_feed: pd.DataFrame):
        """
        데이터 피드를 시간 역순(과거->현재)으로 순회하며 전략 검증
        data_feed: 'timestamp', 'price', 'volatility' 등을 포함하는 DataFrame
        """
        current_position = 0.0
        entry_price = 0.0

        for idx, row in data_feed.iterrows():
            market_state = row.to_dict()
            self.strategy.on_tick(market_state)
            
            # Simple wrapper for entry/exit execution logging
            if current_position == 0 and self.strategy.should_enter():
                current_position = self.strategy.position_size()
                slippage = self.slippage_model.calculate_slippage(
                    order_size=current_position, 
                    current_price=row['price'],
                    side='buy',
                    volatility=row.get('volatility', 0.0)
                )
                entry_price = row['price'] + slippage
            
            elif current_position > 0 and self.strategy.should_exit():
                slippage = self.slippage_model.calculate_slippage(
                    order_size=current_position, 
                    current_price=row['price'],
                    side='sell',
                    volatility=row.get('volatility', 0.0)
                )
                exit_price = row['price'] - slippage
                
                # Record trade
                pnl = (exit_price - entry_price) * current_position
                self.capital += pnl
                self.trades.append({
                    "entry_time": idx, # Simplified
                    "exit_time": idx,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "pnl": pnl
                })
                current_position = 0.0
            
            self.equity_curve.append(self.capital)

    def get_results(self) -> Dict[str, Any]:
        return {
            "final_capital": self.capital,
            "total_trades": len(self.trades),
            "trades": self.trades,
            "equity": self.equity_curve
        }
