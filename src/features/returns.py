import pandas as pd
import numpy as np

def calculate_returns(prices: pd.Series, periods: int = 1) -> pd.Series:
    """단순 수익률 계산 (가격 변화율)"""
    return prices.pct_change(periods=periods)

def calculate_volatility(prices: pd.Series, window: int) -> pd.Series:
    """단순 이동 표준편차 기반의 변동성 계산"""
    returns = calculate_returns(prices)
    return returns.rolling(window=window).std()
