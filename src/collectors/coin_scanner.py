"""
실시간 코인 스캐너

업비트-바이낸스 공통 코인 중 유동성(24h 거래대금) 기준으로
상위 N개를 자동 선정. 주기적으로 재스캔하여 핫코인 추적.
"""
import json
import logging
import urllib.request
from typing import List, Dict

logger = logging.getLogger(__name__)


class CoinScanner:
    """업비트-바이낸스 공통 유동성 상위 코인 자동 선정"""

    # 스테이블코인 제외 (김프 의미 없음)
    EXCLUDE = {"USDC", "USDT", "USDE", "USD1", "WLFI"}

    def __init__(self, min_volume_krw: float = 10_000_000_000,  # 일 100억
                 max_coins: int = 15):
        self.min_volume_krw = min_volume_krw
        self.max_coins = max_coins

    def scan(self) -> List[str]:
        """공통 코인 스캔 → 유동성 상위 N개 반환"""
        try:
            upbit_coins = self._get_upbit_krw_coins()
            binance_coins = self._get_binance_usdt_coins()
            common = set(upbit_coins.keys()) & binance_coins - self.EXCLUDE

            # 업비트 24h 거래대금 기준 정렬
            ranked = []
            for sym in common:
                vol = upbit_coins[sym].get("volume_krw", 0)
                if vol >= self.min_volume_krw:
                    ranked.append((sym, vol))

            ranked.sort(key=lambda x: x[1], reverse=True)
            result = [sym for sym, _ in ranked[:self.max_coins]]

            logger.info(f"[CoinScanner] Found {len(common)} common, "
                        f"{len(ranked)} above {self.min_volume_krw/1e8:.0f}억, "
                        f"selected top {len(result)}")
            return result

        except Exception as e:
            logger.error(f"[CoinScanner] Scan failed: {e}")
            # 폴백: 안전한 기본 목록
            return ["BTC", "ETH", "XRP", "SOL", "DOGE"]

    def _get_upbit_krw_coins(self) -> Dict[str, Dict]:
        """업비트 KRW 마켓 코인 + 24h 거래대금"""
        # 마켓 목록
        markets_data = json.loads(
            urllib.request.urlopen("https://api.upbit.com/v1/market/all").read()
        )
        krw_markets = [m["market"] for m in markets_data if m["market"].startswith("KRW-")]

        # 거래대금 조회 (최대 100개씩)
        result = {}
        for i in range(0, len(krw_markets), 100):
            batch = krw_markets[i:i+100]
            markets_str = ",".join(batch)
            ticker_data = json.loads(
                urllib.request.urlopen(f"https://api.upbit.com/v1/ticker?markets={markets_str}").read()
            )
            for t in ticker_data:
                sym = t["market"].replace("KRW-", "")
                result[sym] = {
                    "volume_krw": float(t.get("acc_trade_price_24h", 0)),
                    "price": float(t.get("trade_price", 0)),
                }

        return result

    def _get_binance_usdt_coins(self) -> set:
        """바이낸스 USDT 마켓 코인 목록"""
        data = json.loads(
            urllib.request.urlopen("https://api.binance.com/api/v3/exchangeInfo").read()
        )
        return {
            s["baseAsset"] for s in data["symbols"]
            if s["quoteAsset"] == "USDT" and s["status"] == "TRADING"
        }
