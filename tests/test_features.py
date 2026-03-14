import pytest
import pandas as pd
import numpy as np
from src.features.returns import calculate_returns, calculate_volatility

def test_calculate_returns():
    prices = pd.Series([100, 105, 102, 110])
    returns = calculate_returns(prices)
    
    # Expected returns: NaN, 0.05, -0.028571, 0.078431
    assert np.isnan(returns[0])
    assert pytest.approx(returns[1], 0.0001) == 0.05
    assert pytest.approx(returns[2], 0.0001) == -0.028571
    assert pytest.approx(returns[3], 0.0001) == 0.078431

def test_calculate_volatility():
    prices = pd.Series([100, 105, 102, 110, 108])
    vol = calculate_volatility(prices, window=3)
    
    # Should be NaN for the first 3 elements (indices 0, 1, 2)
    # index 0: ret=NaN => vol=NaN
    # index 1: ret=0.05 => vol=NaN
    # index 2: ret=-0.028571 => vol=NaN
    # index 3: ret=0.078431 => std of [0.05, -0.028571, 0.078431]
    
    assert np.isnan(vol[0])
    assert np.isnan(vol[1])
    assert np.isnan(vol[2])
    
    # Calculate expected std
    rets = np.array([0.05, -0.028571, 0.078431])
    expected_vol = np.std(rets, ddof=1)
    
    assert pytest.approx(vol[3], 0.0001) == expected_vol

from src.features.imbalance import calculate_imbalance, calculate_premium

def test_calculate_imbalance():
    # bids/asks format: [price, size]
    bids = [[60000, 1.0], [59990, 2.0]]
    asks = [[60010, 1.5], [60020, 0.5]]
    
    # bid_vol = 3.0, ask_vol = 2.0
    # expected imbalance = (3.0 - 2.0) / (3.0 + 2.0) = 0.2
    
    imb = calculate_imbalance(bids, asks, levels=2)
    assert pytest.approx(imb, 0.0001) == 0.2
    assert calculate_imbalance([], []) == 0.0

def test_calculate_premium():
    # local = 65,000,000 KRW
    # global = 60,000 USD
    # fx = 1,000 KRW/USD => adjusted global = 60,000,000 KRW
    # premium = (65M - 60M) / 60M = 0.0833...
    
    premium = calculate_premium(65000000, 60000, fx_rate=1000)
    assert pytest.approx(premium, 0.0001) == 0.0833333

