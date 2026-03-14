import json
import asyncio
import websockets

class BinanceCollector:
    def __init__(self, symbols, stream_types):
        self.symbols = [s.lower() for s in symbols]
        self.stream_types = stream_types
        # e.g., wss://stream.binance.com:9443/ws/btcusdt@ticker
        streams = "/".join([f"{s}@{st}" for s in self.symbols for st in self.stream_types])
        self.uri = f"wss://stream.binance.com:9443/ws/{streams}"

    async def connect(self, queue: asyncio.Queue):
        """WebSocket 연결 초기화 및 큐에 전달"""
        async with websockets.connect(self.uri) as websocket:
            print(f"[Binance] Connected to {self.uri}")
            
            async for message in websocket:
                parsed_data = self.on_message(message)
                if parsed_data:
                    await queue.put({"exchange": "binance", "data": parsed_data})

    def on_message(self, message: str) -> dict:
        """메시지 파싱 및 정규화 계층으로 전달"""
        try:
            data = json.loads(message)
            # Binance Ticker pattern: { 'e': '24hrTicker', 's': 'BTCUSDT', 'c': '60000.00' }
            if "e" in data and data["e"] == "24hrTicker":
                return {
                    "symbol": data.get("s"),
                    "price": float(data.get("c", 0.0)),
                    "volume": float(data.get("v", 0.0))
                }
            return data
        except json.JSONDecodeError:
            return {}
