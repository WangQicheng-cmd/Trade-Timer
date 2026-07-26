import json
import re
import time
from typing import Any, Dict, Optional

import requests

from ..core.config import config
from ..core.logger import logger
from ..core.models import (
    AmountType,
    ParsedTradeCommand,
    TaskSide,
    TriggerDirection,
)


SYSTEM_PROMPT = """你是一个加密货币交易指令解析助手。用户会用自然语言描述一个交易计划，你需要把它解析成结构化的 JSON 数据。

必须返回纯 JSON，不要有任何额外的解释、思考或 markdown 代码块。

输出字段说明：
- symbol: 交易对，格式为 BASE/QUOTE，如 BTC/USDT、ETH/USDC
- side: 买或卖，取值 "buy" 或 "sell"
- trigger_price: 触发价格（数字），如果没有明确触发价格则为 null
- trigger_direction: 触发方向，"above"（价格涨到某值以上触发）或 "below"（价格跌到某值以下触发），如果没有触发价格则为 null
- amount: 交易数量（数字），如果没有明确数量则为 null
- amount_type: 数量类型，"quote"（按计价币数量，如多少 USDT）或 "base"（按标的币数量，如多少 BTC）
- delay_seconds: 延迟多少秒后开始监控（数字），如果立即开始则为 0
- confidence: 解析置信度 0-1

时间单位换算：
- 1 小时 = 3600 秒
- 1 分钟 = 60 秒
- 1 天 = 86400 秒

方向判断规则：
- "涨到...买入" → trigger_direction: "above"
- "跌到...买入" → trigger_direction: "below"
- "涨到...卖出" → trigger_direction: "above"
- "跌到...卖出" → trigger_direction: "below"
- 只说"价格到 X 买入"，默认方向根据 side 判断：buy 默认 "below"（逢低买），sell 默认 "above"（逢高卖）

数量类型判断：
- "花 1000 USDT 买" → amount_type: "quote"
- "买 0.1 个 BTC" → amount_type: "base"
- 只说"全仓买入" → amount: null, amount_type: "quote"

只输出 JSON，不要任何其他文字。"""


class OllamaClient:
    def __init__(self) -> None:
        self.base_url = config.get("ollama.base_url", "http://localhost:11434")
        self.model = config.get("ollama.model", "deepseek-r1")
        self.timeout = config.get("ollama.timeout", 120)
        self._available: Optional[bool] = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            self._available = resp.status_code == 200
            return self._available
        except Exception as e:
            logger.warning(f"Ollama 服务不可用: {e}")
            self._available = False
            return False

    def generate(self, prompt: str, system: Optional[str] = None) -> str:
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system

        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")
        except Exception as e:
            logger.error(f"Ollama 生成失败: {e}")
            raise

    def chat(self, messages: list) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Ollama chat 失败: {e}")
            raise


class TradeCommandParser:
    def __init__(self) -> None:
        self.ollama = OllamaClient()

    def parse(self, user_input: str) -> ParsedTradeCommand:
        logger.info(f"开始解析用户指令: {user_input}")

        if not self.ollama.is_available():
            logger.warning("Ollama 不可用，使用规则解析作为 fallback")
            return self._rule_based_parse(user_input)

        try:
            result = self._ai_parse(user_input)
            return self._build_parsed_command(result, user_input)
        except Exception as e:
            logger.warning(f"AI 解析失败，使用规则解析: {e}")
            return self._rule_based_parse(user_input)

    def _ai_parse(self, user_input: str) -> Dict[str, Any]:
        prompt = f"用户指令：{user_input}\n\n请输出结构化 JSON："
        response = self.ollama.generate(prompt, system=SYSTEM_PROMPT)
        return self._extract_json(response)

    def _extract_json(self, text: str) -> Dict[str, Any]:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError("AI 响应中未找到 JSON")

        json_str = match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.debug(f"首次 JSON 解析失败: {e}, 尝试修复...")
            json_str = self._fix_json(json_str)
            return json.loads(json_str)

    def _fix_json(self, text: str) -> str:
        text = re.sub(r",\s*}", "}", text)
        text = re.sub(r",\s*]", "]", text)
        text = re.sub(r"//.*$", "", text, flags=re.MULTILINE)
        return text

    def _build_parsed_command(self, data: Dict[str, Any], user_input: str) -> ParsedTradeCommand:
        symbol = data.get("symbol", "BTC/USDT").upper().replace("_", "/")
        side = TaskSide.BUY if str(data.get("side", "buy")).lower() == "buy" else TaskSide.SELL

        trigger_price = data.get("trigger_price")
        if trigger_price is not None:
            try:
                trigger_price = float(trigger_price)
            except (ValueError, TypeError):
                trigger_price = None

        trigger_direction = None
        direction_str = str(data.get("trigger_direction", "")).lower()
        if direction_str == "above":
            trigger_direction = TriggerDirection.ABOVE
        elif direction_str == "below":
            trigger_direction = TriggerDirection.BELOW

        amount = data.get("amount")
        if amount is not None:
            try:
                amount = float(amount)
            except (ValueError, TypeError):
                amount = None

        amount_type = AmountType.QUOTE
        if str(data.get("amount_type", "")).lower() == "base":
            amount_type = AmountType.BASE

        delay_seconds = 0
        if data.get("delay_seconds") is not None:
            try:
                delay_seconds = int(float(data["delay_seconds"]))
            except (ValueError, TypeError):
                delay_seconds = 0

        return ParsedTradeCommand(
            symbol=symbol,
            side=side,
            trigger_price=trigger_price,
            trigger_direction=trigger_direction,
            amount=amount,
            amount_type=amount_type,
            delay_seconds=delay_seconds,
            raw_input=user_input,
            extra={"ai_raw": data, "confidence": data.get("confidence")},
        )

    def _rule_based_parse(self, user_input: str) -> ParsedTradeCommand:
        text = user_input.lower()

        symbol = self._extract_symbol(text)
        side = TaskSide.BUY if any(w in text for w in ["买", "买入", "做多", "buy"]) else TaskSide.SELL
        trigger_price = self._extract_price(text)
        trigger_direction = self._extract_direction(text, side, trigger_price)
        amount = self._extract_amount(text)
        amount_type = self._extract_amount_type(text)
        delay_seconds = self._extract_delay(text)

        return ParsedTradeCommand(
            symbol=symbol,
            side=side,
            trigger_price=trigger_price,
            trigger_direction=trigger_direction,
            amount=amount,
            amount_type=amount_type,
            delay_seconds=delay_seconds,
            raw_input=user_input,
            extra={"parsed_by": "rule"},
        )

    def _extract_symbol(self, text: str) -> str:
        common_pairs = [
            ("btc", "BTC/USDT"),
            ("eth", "ETH/USDT"),
            ("sol", "SOL/USDT"),
            ("bnb", "BNB/USDT"),
            ("xrp", "XRP/USDT"),
            ("doge", "DOGE/USDT"),
            ("ada", "ADA/USDT"),
            ("avalanche", "AVAX/USDT"),
            ("avax", "AVAX/USDT"),
        ]
        for keyword, pair in common_pairs:
            if keyword in text:
                return pair
        return "BTC/USDT"

    def _extract_price(self, text: str) -> Optional[float]:
        patterns = [
            r"(\d[\d,]*\.?\d*)\s*(?:美元|usdt|usdc|刀|u)",
            r"价格?\s*(?:到|至|是|为)?\s*(\d[\d,]*\.?\d*)",
            r"(\d[\d,]*\.?\d*)\s*(?:买入|卖出|触发)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1).replace(",", ""))
                except ValueError:
                    continue
        return None

    def _extract_direction(self, text: str, side: TaskSide, price: Optional[float]) -> Optional[TriggerDirection]:
        if price is None:
            return None

        above_keywords = ["涨", "突破", "超过", "高于", "升到", "涨到", "升破"]
        below_keywords = ["跌", "跌破", "低于", "降到", "跌到", "下破"]

        has_above = any(w in text for w in above_keywords)
        has_below = any(w in text for w in below_keywords)

        if has_above and not has_below:
            return TriggerDirection.ABOVE
        if has_below and not has_above:
            return TriggerDirection.BELOW

        if side == TaskSide.BUY:
            return TriggerDirection.BELOW
        else:
            return TriggerDirection.ABOVE

    def _extract_amount(self, text: str) -> Optional[float]:
        patterns = [
            r"(\d[\d,]*\.?\d*)\s*(?:个|枚|颗)",
            r"买\s*(\d[\d,]*\.?\d*)",
            r"(\d[\d,]*\.?\d*)\s*(?:u|usdt|usdc|美元)",
            r"花\s*(\d[\d,]*\.?\d*)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return float(match.group(1).replace(",", ""))
                except ValueError:
                    continue
        return None

    def _extract_amount_type(self, text: str) -> AmountType:
        base_keywords = ["个", "枚", "颗", "btc", "eth", "sol"]
        if any(w in text for w in base_keywords):
            return AmountType.BASE
        return AmountType.QUOTE

    def _extract_delay(self, text: str) -> int:
        total_seconds = 0

        hour_match = re.search(r"(\d+)\s*(?:小时|时|h|hour)", text)
        if hour_match:
            total_seconds += int(hour_match.group(1)) * 3600

        minute_match = re.search(r"(\d+)\s*(?:分钟|分|m|min)", text)
        if minute_match:
            total_seconds += int(minute_match.group(1)) * 60

        day_match = re.search(r"(\d+)\s*(?:天|日|d|day)", text)
        if day_match:
            total_seconds += int(day_match.group(1)) * 86400

        second_match = re.search(r"(\d+)\s*(?:秒|s|sec)", text)
        if second_match:
            total_seconds += int(second_match.group(1))

        return total_seconds


parser = TradeCommandParser()
