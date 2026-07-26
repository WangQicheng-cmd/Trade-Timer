import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests

from ..core.config import config
from ..core.logger import logger
from ..core.models import PriceTick


class MarketProvider(ABC):
    """行情数据源基类"""

    name: str = "base"

    @abstractmethod
    def get_price(self, symbol: str) -> PriceTick:
        pass

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.replace("/", "").replace("-", "").replace("_", "").upper()

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)


class BinanceProvider(MarketProvider):
    name = "binance"

    def __init__(self) -> None:
        self.base_url = config.get("market.binance_url", "https://api.binance.com")

    def get_price(self, symbol: str) -> PriceTick:
        pair = self.normalize_symbol(symbol)
        url = f"{self.base_url}/api/v3/ticker/price"
        resp = requests.get(url, params={"symbol": pair}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        price = float(data["price"])
        return PriceTick(symbol=symbol.upper(), price=price, timestamp=self._now())


class OKXProvider(MarketProvider):
    """OKX 行情源（国内可访问）"""

    name = "okx"

    def __init__(self) -> None:
        self.base_url = config.get("market.okx_url", "https://www.okx.com")

    def get_price(self, symbol: str) -> PriceTick:
        base, quote = self._split_pair(symbol)
        inst_id = f"{base}-{quote}"
        url = f"{self.base_url}/api/v5/market/ticker"
        resp = requests.get(url, params={"instId": inst_id}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "0" or not data.get("data"):
            raise ValueError(f"OKX 返回异常: {data.get('msg', 'unknown')}")
        price = float(data["data"][0]["last"])
        return PriceTick(symbol=symbol.upper(), price=price, timestamp=self._now())

    def _split_pair(self, symbol: str) -> tuple:
        for sep in ["/", "-", "_"]:
            if sep in symbol:
                parts = symbol.split(sep)
                return parts[0].upper(), parts[1].upper()
        return symbol.upper(), "USDT"


class CoinGeckoProvider(MarketProvider):
    name = "coingecko"

    def __init__(self) -> None:
        self.base_url = "https://api.coingecko.com/api/v3"
        self._symbol_map: Dict[str, str] = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "BNB": "binancecoin",
            "XRP": "ripple",
            "DOGE": "dogecoin",
            "ADA": "cardano",
            "AVAX": "avalanche-2",
            "MATIC": "matic-network",
            "POL": "matic-network",
            "LINK": "chainlink",
            "DOT": "polkadot",
            "LTC": "litecoin",
            "TRX": "tron",
            "ATOM": "cosmos",
            "NEAR": "near",
            "APT": "aptos",
            "ARB": "arbitrum",
            "OP": "optimism",
            "UNI": "uniswap",
            "AAVE": "aave",
        }

    def get_price(self, symbol: str) -> PriceTick:
        base, quote = self._parse_symbol(symbol)
        coin_id = self._symbol_map.get(base.upper(), base.lower())
        quote_currency = quote.lower()

        url = f"{self.base_url}/simple/price"
        resp = requests.get(
            url,
            params={"ids": coin_id, "vs_currencies": quote_currency},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        if coin_id not in data or quote_currency not in data[coin_id]:
            raise ValueError(f"CoinGecko 未找到 {symbol}")
        price = float(data[coin_id][quote_currency])
        return PriceTick(symbol=symbol.upper(), price=price, timestamp=self._now())

    def _parse_symbol(self, symbol: str) -> tuple:
        for sep in ["/", "-", "_"]:
            if sep in symbol:
                parts = symbol.split(sep)
                return parts[0], parts[1]
        return symbol, "usdt"


class HuobiProvider(MarketProvider):
    """火币行情源"""

    name = "huobi"

    def __init__(self) -> None:
        self.base_url = config.get("market.huobi_url", "https://api.huobi.pro")

    def get_price(self, symbol: str) -> PriceTick:
        base, quote = self._split_pair(symbol)
        pair = f"{base}{quote}".lower()
        url = f"{self.base_url}/market/detail/merged"
        resp = requests.get(url, params={"symbol": pair}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "ok":
            raise ValueError(f"火币返回异常: {data.get('err-msg', 'unknown')}")
        price = float(data["tick"]["close"])
        return PriceTick(symbol=symbol.upper(), price=price, timestamp=self._now())

    def _split_pair(self, symbol: str) -> tuple:
        for sep in ["/", "-", "_"]:
            if sep in symbol:
                parts = symbol.split(sep)
                return parts[0].upper(), parts[1].upper()
        return symbol.upper(), "USDT"


class GateProvider(MarketProvider):
    """Gate.io 行情源"""

    name = "gate"

    def __init__(self) -> None:
        self.base_url = "https://api.gateio.ws/api/v4"

    def get_price(self, symbol: str) -> PriceTick:
        base, quote = self._split_pair(symbol)
        pair = f"{base}_{quote}"
        url = f"{self.base_url}/spot/tickers"
        resp = requests.get(url, params={"currency_pair": pair}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            raise ValueError(f"Gate.io 未找到 {symbol}")
        price = float(data[0]["last"])
        return PriceTick(symbol=symbol.upper(), price=price, timestamp=self._now())

    def _split_pair(self, symbol: str) -> tuple:
        for sep in ["/", "-", "_"]:
            if sep in symbol:
                parts = symbol.split(sep)
                return parts[0].upper(), parts[1].upper()
        return symbol.upper(), "USDT"


class MarketService:
    """行情服务 - 自动多源切换"""

    _instance: Optional["MarketService"] = None

    def __new__(cls) -> "MarketService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        self._providers: List[MarketProvider] = [
            BinanceProvider(),
            OKXProvider(),
            HuobiProvider(),
            GateProvider(),
            CoinGeckoProvider(),
        ]
        self._active_idx: int = 0
        self._price_cache: Dict[str, tuple] = {}
        try:
            self._cache_ttl = int(config.get("market.poll_interval_seconds", 10))
        except (TypeError, ValueError):
            self._cache_ttl = 10

        proxy = config.get("market.proxy", "")
        if proxy:
            os.environ.setdefault("HTTP_PROXY", proxy)
            os.environ.setdefault("HTTPS_PROXY", proxy)

    def get_price(self, symbol: str, use_cache: bool = True) -> PriceTick:
        key = symbol.upper()
        now = time.time()

        if use_cache and key in self._price_cache:
            price, ts = self._price_cache[key]
            if now - ts < self._cache_ttl:
                return price

        tick = self._fetch_with_fallback(symbol)
        self._price_cache[key] = (tick, now)

        from ..core.database import db
        try:
            db.save_price(key, tick.price)
        except Exception as e:
            logger.debug(f"保存价格历史失败: {e}")

        return tick

    def _fetch_with_fallback(self, symbol: str) -> PriceTick:
        """依次尝试所有行情源，成功即返回"""
        errors = []
        for idx in range(len(self._providers)):
            provider_idx = (self._active_idx + idx) % len(self._providers)
            provider = self._providers[provider_idx]
            try:
                tick = provider.get_price(symbol)
                if provider_idx != self._active_idx:
                    logger.info(f"行情源切换至 {provider.name}")
                    self._active_idx = provider_idx
                return tick
            except Exception as e:
                errors.append(f"{provider.name}: {e}")
                logger.debug(f"行情源 {provider.name} 获取 {symbol} 失败: {e}")

        raise RuntimeError(
            f"所有行情源均失败 ({symbol}): " + "; ".join(errors)
        )

    def get_current_price_str(self, symbol: str) -> str:
        try:
            tick = self.get_price(symbol)
            return f"${tick.price:,.2f}"
        except Exception:
            return "N/A"


market_service = MarketService()
