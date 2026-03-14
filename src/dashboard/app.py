import asyncio
from typing import Dict, Any

from src.collectors.binance_ws import BinanceCollector
from src.collectors.upbit_ws import UpbitCollector
from src.strategies.lead_lag_scalper import LeadLagScalper
from src.strategies.momentum_breakout import MomentumBreakout

class LiveDryRunEngine:
    def __init__(self):
        self.queue = asyncio.Queue()
        
        # Initialize collectors
        self.upbit = UpbitCollector(["KRW-BTC"], ["ticker"])
        self.binance = BinanceCollector(["btcusdt"], ["ticker"])
        
        # Load Strategies with basic config
        self.strategies = {
            "LeadLag(Kimchi)": LeadLagScalper({"entry_threshold": 0.03, "exit_threshold": 0.005, "fx_rate": 1400.0}),
            "Momentum_Breakout": MomentumBreakout({"lookback": 5, "volume_multiplier": 1.5})
        }
        
        # Global Market State cross-referenced by exchanges
        self.market_state: Dict[str, Any] = {
            "upbit_price": 0.0,
            "binance_price": 0.0,
            "price": 0.0, # active single price for momentum
            "volume": 0.0
        }

    async def _process_messages(self):
        """수집된 이벤트를 큐에서 꺼내 전략 엔진에 주입"""
        print("\n[System] Live Dry-Run Engine Started... Waiting for signals \n")
        
        while True:
            msg = await self.queue.get()
            exchange = msg["exchange"]
            data = msg["data"]
            
            # Update unified market state
            if exchange == "upbit":
                self.market_state["upbit_price"] = data.get("price", 0.0)
                self.market_state["price"] = data.get("price", 0.0)
                self.market_state["volume"] = data.get("volume", 0.0)
            elif exchange == "binance":
                self.market_state["binance_price"] = data.get("price", 0.0)

            # Route state to all active strategies
            for name, strategy in self.strategies.items():
                strategy.on_tick(self.market_state)
                
                # Check Signals
                if not strategy.state.get("in_position", False) and strategy.should_enter():
                    print(f"[SIGNAL: {name}] ENTRY TRIGGERED! | Local: {self.market_state['upbit_price']} | Global: {self.market_state['binance_price']}")
                    strategy.state["in_position"] = True
                    
                elif strategy.state.get("in_position", False) and strategy.should_exit():
                    print(f"[SIGNAL: {name}] EXIT TRIGGERED! | Local: {self.market_state['upbit_price']} | Global: {self.market_state['binance_price']}")
                    strategy.state["in_position"] = False

    async def start(self):
        """비동기 수집기 및 처리기 동시 실행"""
        await asyncio.gather(
            self.upbit.connect(self.queue),
            self.binance.connect(self.queue),
            self._process_messages()
        )

if __name__ == "__main__":
    engine = LiveDryRunEngine()
    try:
        asyncio.run(engine.start())
    except KeyboardInterrupt:
        print("\n[System] Engine shutdown by user.")
