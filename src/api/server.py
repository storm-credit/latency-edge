from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json

from src.collectors.binance_ws import BinanceCollector
from src.collectors.upbit_ws import UpbitCollector
from src.strategies.lead_lag_scalper import LeadLagScalper
from src.strategies.momentum_breakout import MomentumBreakout

app = FastAPI(title="Latency Edge API")

# Allow CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine state
class ApiEngine:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.upbit = UpbitCollector(["KRW-BTC"], ["ticker"])
        self.binance = BinanceCollector(["btcusdt"], ["ticker"])
        self.strategies = {
            "LeadLag(Kimchi)": LeadLagScalper({"entry_threshold": 0.03, "exit_threshold": 0.005, "fx_rate": 1400.0}),
            "Momentum": MomentumBreakout({"lookback": 5, "volume_multiplier": 1.5})
        }
        self.market_state = {
            "upbit_price": 0.0,
            "binance_price": 0.0,
            "price": 0.0,
            "volume": 0.0
        }
        self.portfolio = {"KRW": 10000000.0, "BTC": 0.0}
        self.subscribers = set()
        self.latest_signals = []

    async def broadcast(self, message: dict):
        for ws in set(self.subscribers):
            try:
                await ws.send_json(message)
            except WebSocketDisconnect:
                self.subscribers.remove(ws)

    async def run(self):
        asyncio.create_task(self.upbit.connect(self.queue))
        asyncio.create_task(self.binance.connect(self.queue))
        
        while True:
            msg = await self.queue.get()
            exchange = msg["exchange"]
            data = msg["data"]
            
            if exchange == "upbit":
                self.market_state["upbit_price"] = data.get("price", 0.0)
                self.market_state["price"] = data.get("price", 0.0)
                self.market_state["volume"] = data.get("volume", 0.0)
            elif exchange == "binance":
                self.market_state["binance_price"] = data.get("price", 0.0)

            # Broadcast market tick & portfolio
            equity = self.portfolio["KRW"] + (self.portfolio["BTC"] * self.market_state["upbit_price"])
            await self.broadcast({
                "type": "tick", 
                "state": self.market_state,
                "portfolio": {"KRW": self.portfolio["KRW"], "BTC": self.portfolio["BTC"], "Equity": equity}
            })

            # Check Strategies
            for name, strategy in self.strategies.items():
                strategy.on_tick(self.market_state)
                
                if not strategy.state.get("in_position", False) and strategy.should_enter():
                    strategy.state["in_position"] = True
                    # Simulate Buy (using up to 1,000,000 KRW per trade)
                    trade_krw = min(1000000.0, self.portfolio["KRW"])
                    if trade_krw > 0 and self.market_state["upbit_price"] > 0:
                        btc_qty = trade_krw / self.market_state["upbit_price"]
                        self.portfolio["KRW"] -= trade_krw
                        self.portfolio["BTC"] += btc_qty
                    
                    signal = {"type": "signal", "strategy": name, "action": "ENTRY", "local": self.market_state["upbit_price"], "global": self.market_state["binance_price"]}
                    self.latest_signals.append(signal)
                    await self.broadcast(signal)
                    
                elif strategy.state.get("in_position", False) and strategy.should_exit():
                    strategy.state["in_position"] = False
                    # Simulate Sell (all holding BTC)
                    if self.portfolio["BTC"] > 0 and self.market_state["upbit_price"] > 0:
                        krw_gained = self.portfolio["BTC"] * self.market_state["upbit_price"]
                        # Applying simple 0.05% Upbit maker fee simulation
                        krw_gained = krw_gained * 0.9995
                        self.portfolio["KRW"] += krw_gained
                        self.portfolio["BTC"] = 0.0
                    
                    signal = {"type": "signal", "strategy": name, "action": "EXIT", "local": self.market_state["upbit_price"], "global": self.market_state["binance_price"]}
                    self.latest_signals.append(signal)
                    await self.broadcast(signal)

engine = ApiEngine()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(engine.run())

@app.get("/api/state")
async def get_state():
    return {
        "market": engine.market_state, 
        "portfolio": engine.portfolio,
        "signals": engine.latest_signals[-10:]
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    engine.subscribers.add(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep alive
    except WebSocketDisconnect:
        engine.subscribers.remove(websocket)
