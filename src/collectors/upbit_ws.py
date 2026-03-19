import json
import asyncio
import uuid
import websockets


class UpbitCollector:
    MAX_RETRY_DELAY = 60

    def __init__(self, symbols, channels):
        self.symbols = symbols
        self.channels = channels
        self.uri = "wss://api.upbit.com/websocket/v1"

    async def connect(self, queue: asyncio.Queue):
        """업비트 WebSocket 연결 (자동 재연결 + 지수 백오프)"""
        subscribe_fmt = [
            {"ticket": f"latency-edge-{uuid.uuid4().hex[:8]}"},
            {"type": "ticker", "codes": self.symbols}
        ]
        retry_delay = 1
        while True:
            try:
                async with websockets.connect(self.uri) as websocket:
                    await websocket.send(json.dumps(subscribe_fmt))
                    print(f"[Upbit] Connected: {self.symbols}")
                    retry_delay = 1

                    async for message in websocket:
                        parsed_data = self.on_message(message)
                        if parsed_data:
                            await queue.put({"exchange": "upbit", "data": parsed_data})

            except (websockets.ConnectionClosed, ConnectionError, OSError) as e:
                print(f"[Upbit] Connection lost: {e}. Retry in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, self.MAX_RETRY_DELAY)
            except Exception as e:
                print(f"[Upbit] Unexpected error: {e}. Retry in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, self.MAX_RETRY_DELAY)

    def on_message(self, message) -> dict:
        """메시지 파싱, 호가 및 체결 데이터 처리"""
        try:
            data = json.loads(message)
            if data.get("type") == "ticker":
                price = float(data.get("trade_price", 0))
                if price <= 0:
                    return {}
                return {
                    "symbol": data.get("code"),
                    "price": price,
                    "volume": float(data.get("acc_trade_volume_24h", 0))
                }
            return {}
        except Exception as e:
            print(f"[Upbit] Parse error: {e}")
            return {}
