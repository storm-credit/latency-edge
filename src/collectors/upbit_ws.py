import json
import asyncio
import websockets

class UpbitCollector:
    def __init__(self, symbols, channels):
        self.symbols = symbols
        self.channels = channels
        self.uri = "wss://api.upbit.com/websocket/v1"

    async def connect(self, queue: asyncio.Queue):
        """업비트 전용 WebSocket 세션 시작 후 이벤트를 큐에 전달"""
        subscribe_fmt = [
            {"ticket": "latency-edge-bot"},
            {"type": "ticker", "codes": self.symbols}
        ]
        
        async with websockets.connect(self.uri) as websocket:
            await websocket.send(json.dumps(subscribe_fmt))
            print(f"[Upbit] Connected and listening to {self.symbols}")
            
            async for message in websocket:
                parsed_data = self.on_message(message)
                if parsed_data:
                    await queue.put({"exchange": "upbit", "data": parsed_data})

    def on_message(self, message) -> dict:
        """메시지 파싱, 호가 및 체결 데이터 처리"""
        try:
            data = json.loads(message)
            if data.get("type") == "ticker":
                return {
                    "symbol": data.get("code"),
                    "price": float(data.get("trade_price", 0)),
                    "volume": float(data.get("acc_trade_volume_24h", 0))
                }
            return data
        except Exception:
            return {}
