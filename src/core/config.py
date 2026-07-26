import os
import json
from pathlib import Path
from typing import Any, Dict, Optional


BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_FILE = BASE_DIR / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "ollama": {
        "base_url": "http://localhost:11434",
        "model": "deepseek-r1",
        "timeout": 120,
    },
    "market": {
        "poll_interval_seconds": 10,
        "binance_url": "https://api.binance.com",
        "okx_url": "https://www.okx.com",
        "huobi_url": "https://api.huobi.pro",
        "proxy": "",
    },
    "web3": {
        "chain_id": 1,
        "rpc_url": "https://eth.llamarpc.com",
        "fee_wallet_address": "0xB4b9a2DcdcCf91713E8bCE68BD436Fa8062Db6A6",
        "fee_splitter_address": "",
        "fee_percent": 0.002,
        "slippage_tolerance": 0.005,
        "dex_router_address": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    },
    "database": {
        "path": str(DATA_DIR / "tasks.db"),
    },
    "scheduler": {
        "check_interval_seconds": 5,
    },
}


class Config:
    _instance: Optional["Config"] = None
    _data: Dict[str, Any]

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            self._data = self._deep_merge(DEFAULT_CONFIG, user_config)
        else:
            self._data = DEFAULT_CONFIG.copy()
            self.save()

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def save(self) -> None:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value: Any = self._data
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        keys = key.split(".")
        data = self._data
        for k in keys[:-1]:
            if k not in data or not isinstance(data[k], dict):
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value
        self.save()

    @property
    def all(self) -> Dict[str, Any]:
        return self._deep_merge({}, self._data)


config = Config()
