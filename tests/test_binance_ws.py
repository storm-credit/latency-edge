import pytest
import websockets
import json

@pytest.mark.asyncio
async def test_binance_ws_message_parsing():
    from src.collectors.binance_ws import BinanceCollector
    
    collector = BinanceCollector(["btcusdt"], ["ticker"])
    
    # Mock Binance Spot Ticker Event
    mock_msg = json.dumps({
        "e": "24hrTicker",
        "s": "BTCUSDT",
        "c": "60000.00"
    })
    
    result = collector.on_message(mock_msg)
    
    assert result['symbol'] == 'BTCUSDT'
    assert result['price'] == 60000.00
