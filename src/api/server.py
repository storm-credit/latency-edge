from contextlib import asynccontextmanager
from collections import deque
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from src.collectors.binance_ws import BinanceCollector
from src.collectors.upbit_ws import UpbitCollector
from src.strategies.lead_lag_scalper import LeadLagScalper
from src.strategies.momentum_breakout import MomentumBreakout
from src.risk.daily_stop import DailyRiskManager
from src.risk.position_sizer import KellyPositionSizer
from src.config import Config


class ApiEngine:
    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=500)
        self.upbit = UpbitCollector(["KRW-BTC"], ["ticker"])
        self.binance = BinanceCollector(["btcusdt"], ["ticker"])
        self.fx_rate = Config.FX_RATE
        self.strategies = {
            "LeadLag(Kimchi)": LeadLagScalper({
                "entry_threshold": Config.LL_ENTRY_THRESHOLD,
                "exit_threshold": Config.LL_EXIT_THRESHOLD,
                "fx_rate": self.fx_rate,
            }),
            "Momentum": MomentumBreakout({
                "lookback": Config.MOM_LOOKBACK,
                "volume_multiplier": Config.MOM_VOLUME_MULT,
                "trail_pct": Config.MOM_TRAIL_PCT,
                "stop_loss_pct": Config.MOM_STOP_LOSS_PCT,
            })
        }
        self.market_state = {
            "upbit_price": 0.0,
            "binance_price": 0.0,
            "price": 0.0,
            "volume": 0.0
        }
        self.portfolios = {
            name: {"KRW": Config.CAPITAL_PER_STRATEGY, "BTC": 0.0}
            for name in self.strategies
        }
        self.risk_manager = DailyRiskManager(
            max_daily_loss=Config.MAX_DAILY_LOSS,
            max_consecutive_losses=Config.MAX_CONSECUTIVE_LOSSES,
        )
        self.subscribers: set[WebSocket] = set()
        self.latest_signals: deque = deque(maxlen=Config.SIGNAL_HISTORY_SIZE)
        # Kelly 포지션 사이저 (전략 공유)
        self.position_sizer = KellyPositionSizer(
            max_fraction=Config.KELLY_MAX_FRACTION,
            min_trades=Config.KELLY_MIN_TRADES,
        ) if Config.KELLY_ENABLED else None

    async def broadcast(self, message: dict):
        # [P0-4] 레이스 컨디션 수정: discard 사용 + 모든 예외 처리
        dead: list[WebSocket] = []
        for ws in set(self.subscribers):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.subscribers.discard(ws)

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

            # Broadcast market tick & aggregated portfolio
            total_krw = sum(p["KRW"] for p in self.portfolios.values())
            total_btc = sum(p["BTC"] for p in self.portfolios.values())
            equity = total_krw + (total_btc * self.market_state["upbit_price"])
            await self.broadcast({
                "type": "tick",
                "state": self.market_state,
                "portfolio": {"KRW": total_krw, "BTC": total_btc, "Equity": equity},
                "portfolios": self.portfolios,
                # [P0-3] FX Rate를 프론트에 전달
                "fx_rate": self.fx_rate,
            })

            # Check Strategies (각 전략은 독립 포트폴리오 사용)
            for name, strategy in self.strategies.items():
                portfolio = self.portfolios[name]
                strategy.on_tick(self.market_state)

                if not strategy.state.get("in_position", False) and strategy.should_enter():
                    if not self.risk_manager.check_trade_allowed():
                        signal = {"type": "signal", "strategy": name, "action": "BLOCKED_BY_RISK", "local": self.market_state["upbit_price"], "global": self.market_state["binance_price"]}
                        self.latest_signals.append(signal)
                        await self.broadcast(signal)
                        continue

                    strategy.state["in_position"] = True
                    strategy.state["entry_price"] = self.market_state["upbit_price"]
                    strategy.on_enter()
                    # Kelly 사이저 또는 고정 사이즈 + 레짐 배수 적용
                    if self.position_sizer:
                        trade_krw = self.position_sizer.get_trade_size(portfolio["KRW"])
                    else:
                        trade_krw = min(Config.TRADE_SIZE_KRW, portfolio["KRW"])
                    # 레짐 기반 포지션 조절 (고변동성 → 축소)
                    if hasattr(strategy, 'regime'):
                        trade_krw *= strategy.regime.get_position_multiplier()
                    if trade_krw > 0 and self.market_state["upbit_price"] > 0:
                        trade_krw_after_fee = trade_krw * (1 - Config.FEE_RATE)
                        btc_qty = trade_krw_after_fee / self.market_state["upbit_price"]
                        portfolio["KRW"] -= trade_krw
                        portfolio["BTC"] += btc_qty
                        # 실제 투입 KRW 기록 (PnL 계산용)
                        strategy.state["trade_krw"] = trade_krw

                    signal = {"type": "signal", "strategy": name, "action": "ENTRY", "local": self.market_state["upbit_price"], "global": self.market_state["binance_price"]}
                    self.latest_signals.append(signal)
                    await self.broadcast(signal)

                elif strategy.state.get("in_position", False) and strategy.should_exit():
                    strategy.state["in_position"] = False
                    strategy.on_exit()
                    # [P0-1] PnL 계산 수정: 실제 KRW 기준 손익
                    krw_before = strategy.state.get("trade_krw", 0.0)
                    krw_after = 0.0

                    # Simulate Sell (해당 전략의 BTC만 청산, 0.05% fee)
                    if portfolio["BTC"] > 0 and self.market_state["upbit_price"] > 0:
                        krw_gained = portfolio["BTC"] * self.market_state["upbit_price"]
                        krw_gained = krw_gained * (1 - Config.FEE_RATE)
                        portfolio["KRW"] += krw_gained
                        krw_after = krw_gained
                        portfolio["BTC"] = 0.0

                    # 실제 KRW 손익 (투입금 대비 회수금)
                    pnl = krw_after - krw_before
                    self.risk_manager.update_result(pnl)
                    if self.position_sizer:
                        self.position_sizer.update(pnl)

                    signal = {"type": "signal", "strategy": name, "action": "EXIT", "local": self.market_state["upbit_price"], "global": self.market_state["binance_price"], "pnl": pnl}
                    self.latest_signals.append(signal)
                    await self.broadcast(signal)

engine = ApiEngine()

@asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(engine.run())
    yield
    task.cancel()

app = FastAPI(title="Latency Edge API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3100"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/state")
async def get_state():
    total_krw = sum(p["KRW"] for p in engine.portfolios.values())
    total_btc = sum(p["BTC"] for p in engine.portfolios.values())
    return {
        "market": engine.market_state,
        "portfolio": {"KRW": total_krw, "BTC": total_btc},
        "portfolios": engine.portfolios,
        "signals": list(engine.latest_signals)[-10:],
        "fx_rate": engine.fx_rate,
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    engine.subscribers.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        engine.subscribers.discard(websocket)
    except Exception:
        engine.subscribers.discard(websocket)
