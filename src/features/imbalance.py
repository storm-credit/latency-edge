def calculate_imbalance(bids: list, asks: list, levels: int = 5) -> float:
    """호가 잔량 불균형 계산 (Bids - Asks) / (Bids + Asks)"""
    if not bids or not asks:
        return 0.0
    
    bid_vol = sum(b[1] for b in bids[:levels])
    ask_vol = sum(a[1] for a in asks[:levels])
    
    total_vol = bid_vol + ask_vol
    if total_vol == 0:
        return 0.0
        
    return (bid_vol - ask_vol) / total_vol

def calculate_premium(local_price: float, global_price: float, fx_rate: float = 1.0) -> float:
    """프리미엄(예: 김치 프리미엄) 계산"""
    if global_price == 0:
        return 0.0
    adjusted_global = global_price * fx_rate
    return (local_price - adjusted_global) / adjusted_global
