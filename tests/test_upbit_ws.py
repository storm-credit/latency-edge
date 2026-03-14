import pytest
import websockets
import json

@pytest.mark.asyncio
async def test_upbit_ws_message_parsing():
    from src.collectors.upbit_ws import UpbitCollector
    # Dummy collector instance
    collector = UpbitCollector(["KRW-BTC"], ["ticker"])
    
    # Mock message
    mock_msg = json.dumps({"type": "ticker", "code": "KRW-BTC", "trade_price": 60000000})
    result = collector.on_message(mock_msg)
    
    # Expected structured output
    assert result['symbol'] == 'KRW-BTC'
    assert result['price'] == 60000000
