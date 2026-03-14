import numpy as np

class SlippageModel:
    def __init__(self, constant_slippage_bps: float = 2.0, latency_ms: int = 50):
        # Basis points e.g. 2.0 bps = 0.0002
        self.constant_slippage_bps = constant_slippage_bps
        self.latency_ms = latency_ms

    def calculate_slippage(self, order_size: float, current_price: float, side: str, volatility: float = 0.0) -> float:
        """
        슬리피지 비용 계산
        - 기본 고정 슬리피지 (스프레드 한계)
        - 변동성에 비례하는 추가 지연 페널티 (시장 급변 시 체결 미끄러짐)
        """
        base_slippage = current_price * (self.constant_slippage_bps / 10000)
        # 높은 변동성에서 체결될 경우 페널티 부여
        volatility_penalty = current_price * volatility * (self.latency_ms / 1000)
        
        return base_slippage + volatility_penalty
