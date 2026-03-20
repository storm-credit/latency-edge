"""
다중 코인 동시 수집기

바이낸스/업비트에서 여러 코인의 실시간 가격을 동시 수집.
커플링 전략(빗각)을 위한 다중 심볼 WebSocket 관리.
"""
import json
import asyncio
import logging
import uuid
import websockets
from typing import Dict, List

logger = logging.getLogger(__name__)


# 업비트-바이낸스 공통 유동성 상위 코인 (일 30억+ 기준)
DEFAULT_SYMBOLS = [
    "BTC", "ETH", "XRP", "SOL", "DOGE",
    "TRX", "SHIB", "ADA", "SUI", "WLD",
    "APT", "ONDO", "RENDER", "PEPE", "NEAR",
]


class MultiUpbitCollector:
    """업비트 다중 코인 WebSocket 수집기"""
    MAX_RETRY_DELAY = 60

    def __init__(self, symbols: List[str] | None = None):
        self.symbols = symbols or DEFAULT_SYMBOLS
        self.codes = [f"KRW-{s}" for s in self.symbols]
        self.uri = "wss://api.upbit.com/websocket/v1"

    async def connect(self, queue: asyncio.Queue) -> None:
        subscribe_fmt = [
            {"ticket": f"latency-edge-multi-{uuid.uuid4().hex[:8]}"},
            {"type": "ticker", "codes": self.codes}
        ]
        retry_delay = 1
        while True:
            try:
                async with websockets.connect(self.uri) as ws:
                    await ws.send(json.dumps(subscribe_fmt))
                    logger.info(f"[Upbit-Multi] Connected: {len(self.codes)} coins")
                    retry_delay = 1
                    async for message in ws:
                        parsed = self._parse(message)
                        if parsed:
                            await queue.put(parsed)
            except (websockets.ConnectionClosed, ConnectionError, OSError) as e:
                logger.warning(f"[Upbit-Multi] Connection lost: {e}. Retry in {retry_delay}s")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, self.MAX_RETRY_DELAY)
            except Exception as e:
                logger.error(f"[Upbit-Multi] Unexpected: {e}. Retry in {retry_delay}s")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, self.MAX_RETRY_DELAY)

    def _parse(self, message) -> Dict | None:
        try:
            data = json.loads(message)
            if data.get("type") != "ticker":
                return None
            code = data.get("code", "")  # "KRW-BTC"
            symbol = code.replace("KRW-", "")
            price = float(data.get("trade_price", 0))
            if price <= 0:
                return None
            return {
                "exchange": "upbit",
                "symbol": symbol,
                "data": {
                    "symbol": symbol,
                    "price": price,
                    "volume": float(data.get("acc_trade_volume_24h", 0)),
                }
            }
        except Exception as e:
            logger.warning(f"[Upbit-Multi] Parse error: {e}")
            return None


class MultiBinanceCollector:
    """바이낸스 다중 코인 WebSocket 수집기"""
    MAX_RETRY_DELAY = 60

    def __init__(self, symbols: List[str] | None = None):
        self.symbols = symbols or DEFAULT_SYMBOLS
        streams = "/".join([f"{s.lower()}usdt@ticker" for s in self.symbols])
        self.uri = f"wss://stream.binance.com:9443/ws/{streams}"

    async def connect(self, queue: asyncio.Queue) -> None:
        retry_delay = 1
        while True:
            try:
                async with websockets.connect(self.uri) as ws:
                    logger.info(f"[Binance-Multi] Connected: {len(self.symbols)} coins")
                    retry_delay = 1
                    async for message in ws:
                        parsed = self._parse(message)
                        if parsed:
                            await queue.put(parsed)
            except (websockets.ConnectionClosed, ConnectionError, OSError) as e:
                logger.warning(f"[Binance-Multi] Connection lost: {e}. Retry in {retry_delay}s")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, self.MAX_RETRY_DELAY)
            except Exception as e:
                logger.error(f"[Binance-Multi] Unexpected: {e}. Retry in {retry_delay}s")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, self.MAX_RETRY_DELAY)

    def _parse(self, message: str) -> Dict | None:
        try:
            data = json.loads(message)
            if data.get("e") != "24hrTicker":
                return None
            raw_symbol = data.get("s", "")  # "BTCUSDT"
            symbol = raw_symbol.replace("USDT", "")
            price = float(data.get("c", 0))
            if price <= 0:
                return None
            return {
                "exchange": "binance",
                "symbol": symbol,
                "data": {
                    "symbol": symbol,
                    "price": price,
                    "volume": float(data.get("v", 0)),
                }
            }
        except Exception as e:
            logger.warning(f"[Binance-Multi] Parse error: {e}")
            return None
