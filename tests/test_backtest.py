import pytest
import pandas as pd
from src.backtest.slippage import SlippageModel
from src.backtest.engine import BacktestEngine
from src.backtest.metrics import calculate_metrics
from src.strategies.base import BaseStrategy

class DummyStrategy(BaseStrategy):
    """Test purpose only strategy that enters on tick 0, exits on tick 1"""
    def __init__(self):
        super().__init__({})
        self.ticks = 0

    def on_tick(self, market_state):
        self.ticks += 1

    def should_enter(self) -> bool:
        return self.ticks == 1

    def should_exit(self) -> bool:
        return self.ticks == 2

    def position_size(self) -> float:
        return 1.0

def test_slippage_model():
    # impact_factor 기본값 0.0이므로 base slippage만 적용
    model = SlippageModel(constant_slippage_bps=2.0)
    slip = model.calculate_slippage(1.0, 10000, 'buy', 0.0)
    # 2 bps of 10000 is 2.0
    assert pytest.approx(slip, abs=0.01) == 2.0

    # With volatility penalty (impact_factor=0 → size_impact=0)
    model2 = SlippageModel(constant_slippage_bps=0.0, latency_ms=100)
    slip2 = model2.calculate_slippage(1.0, 10000, 'buy', volatility=0.05)
    # penalty = 10000 * 0.05 * (100 / 1000) = 50.0
    assert pytest.approx(slip2, abs=0.01) == 50.0

def test_backtest_engine_and_metrics():
    strategy = DummyStrategy()
    # No slippage, no fee for exact math
    slippage = SlippageModel(constant_slippage_bps=0.0, latency_ms=0)
    engine = BacktestEngine(strategy, slippage, initial_capital=1000.0, fee_rate=0.0)

    # Tick 1: price 100 -> enter
    # Tick 2: price 110 -> exit
    data = pd.DataFrame([
        {"price": 100, "volatility": 0.0},
        {"price": 110, "volatility": 0.0}
    ])

    engine.run(data)
    results = engine.get_results()

    assert results["total_trades"] == 1
    assert results["trades"][0]["pnl"] == 10.0
    assert results["final_capital"] == 1010.0

    metrics = calculate_metrics(results["trades"], results["equity"])
    assert metrics["win_rate"] == 1.0
    assert metrics["profit_factor"] == float('inf')
    assert metrics["mdd"] == 0.0  # capital never drops below running max
