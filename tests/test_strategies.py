import pytest
from src.strategies.lead_lag_scalper import LeadLagScalper
from src.strategies.momentum_breakout import MomentumBreakout

def test_lead_lag_scalper():
    config = {
        "entry_threshold": 0.05,
        "exit_threshold": 0.01,
        "fx_rate": 1000.0,
        "position_size": 1.0
    }
    strategy = LeadLagScalper(config)
    
    # tick 1: no premium -> local=60000, global=60
    strategy.on_tick({'upbit_price': 60000, 'binance_price': 60})
    assert not strategy.should_enter()
    
    # tick 2: 10% premium -> local=66000, global=60
    strategy.on_tick({'upbit_price': 66000, 'binance_price': 60})
    assert strategy.should_enter()
    
    # tick 3: 0% premium -> local=60000, global=60
    strategy.on_tick({'upbit_price': 60000, 'binance_price': 60})
    assert strategy.should_exit()

def test_momentum_breakout():
    config = {
        "lookback": 3,
        "volume_multiplier": 1.5
    }
    strategy = MomentumBreakout(config)
    
    # tick 1
    strategy.on_tick({'price': 100, 'volume': 10})
    assert not strategy.should_enter() # not enough history
    
    # tick 2
    strategy.on_tick({'price': 105, 'volume': 12})
    assert not strategy.should_enter() # not enough history
    
    # tick 3
    strategy.on_tick({'price': 102, 'volume': 11})
    assert not strategy.should_enter() # has 3 history now, but 102 is not > highest(105)
    
    # tick 4 - breakout!
    # avg volume of previous 3 was (10+12+11)/3 = 11
    # condition: px > 105, vol > 11 * 1.5 = 16.5
    strategy.on_tick({'price': 110, 'volume': 20})
    assert strategy.should_enter()
