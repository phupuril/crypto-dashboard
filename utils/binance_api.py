import requests
from typing import Any, Dict, List, Optional


class BinanceRESTClient:
    def __init__(self, base_url: str = "https://api.binance.com", timeout: int = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}{path}"
        r = requests.get(url, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def get_price(self, symbol: str) -> Dict[str, Any]:
        return self._get("/api/v3/ticker/price", {"symbol": symbol})

    def get_24hr_stats(self, symbol: str) -> Dict[str, Any]:
        return self._get("/api/v3/ticker/24hr", {"symbol": symbol})

    def get_orderbook(self, symbol: str, limit: int = 10) -> Dict[str, Any]:
        return self._get("/api/v3/depth", {"symbol": symbol, "limit": limit})

    def get_trades(self, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        return self._get("/api/v3/trades", {"symbol": symbol, "limit": limit})

    def get_klines(self, symbol: str, interval: str, limit: int = 60) -> List[List[Any]]:
        return self._get("/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": limit})
