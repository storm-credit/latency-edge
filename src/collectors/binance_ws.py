import json
import asyncio
import logging
import websockets

logger = logging.getLogger(__name__)


class BinanceCollector:
    MAX_RETRY_DELAY = 60

    def __init__(self, symbols, stream_types):
        self.symbols = [s.lower() for s in symbols]
        self.stream_types = stream_types
        streams = "/".join([f"{s}@{st}" for s in self.symbols for st in self.stream_types])
        self.uri = f"wss://stream.binance.com:9443/ws/{streams}"

    async def connect(self, queue: asyncio.Queue):
        """WebSocket 연결 (자동 재연결 + 지수 백오프)"""
        retry_delay = 1
        while True:
            try:
                async with websockets.connect(self.uri) as websocket:
                    logger.info(f"[Binance] Connected: {self.uri}")
                    retry_delay = 1

                    async for message in websocket:
                        parsed_data = self.on_message(message)
                        if parsed_data:
                            await queue.put({"exchange": "binance", "data": parsed_data})

            except (websockets.ConnectionClosed, ConnectionError, OSError) as e:
                logger.warning(f"[Binance] Connection lost: {e}. Retry in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, self.MAX_RETRY_DELAY)
            except Exception as e:
                logger.error(f"[Binance] Unexpected error: {e}. Retry in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, self.MAX_RETRY_DELAY)

    def on_message(self, message: str) -> dict:
        """메시지 파싱 및 정규화"""
        try:
            data = json.loads(message)
            if "e" in data and data["e"] == "24hrTicker":
                price = float(data.get("c", 0.0))
                if price <= 0:
                    return {}
                return {
                    "symbol": data.get("s"),
                    "price": price,
                    "volume": float(data.get("v", 0.0))
                }
            return {}
        except Exception as e:
            logger.warning(f"[Binance] Parse error: {e}")
            return {}
