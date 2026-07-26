from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional


class TaskStatus(str, Enum):
    PENDING = "pending"
    WAITING = "waiting"
    MONITORING = "monitoring"
    TRIGGERED = "triggered"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class TriggerDirection(str, Enum):
    ABOVE = "above"
    BELOW = "below"


class AmountType(str, Enum):
    QUOTE = "quote"
    BASE = "base"


@dataclass
class ParsedTradeCommand:
    symbol: str
    side: TaskSide
    trigger_price: Optional[float] = None
    trigger_direction: Optional[TriggerDirection] = None
    amount: Optional[float] = None
    amount_type: AmountType = AmountType.QUOTE
    delay_seconds: int = 0
    raw_input: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_task_dict(self, user_input: str) -> Dict[str, Any]:
        start_time = None
        if self.delay_seconds > 0:
            start_time = (datetime.utcnow() + timedelta(seconds=self.delay_seconds)).isoformat()

        status = TaskStatus.WAITING.value if self.delay_seconds > 0 else TaskStatus.PENDING.value
        if start_time and self.delay_seconds == 0:
            status = TaskStatus.MONITORING.value

        return {
            "user_input": user_input,
            "symbol": self.symbol.upper(),
            "side": self.side.value,
            "trigger_price": self.trigger_price,
            "trigger_direction": self.trigger_direction.value if self.trigger_direction else None,
            "amount": self.amount,
            "amount_type": self.amount_type.value,
            "delay_seconds": self.delay_seconds,
            "start_time": start_time,
            "status": status,
            "params": self.extra,
        }


@dataclass
class PriceTick:
    symbol: str
    price: float
    timestamp: datetime

    def check_trigger(self, trigger_price: float, direction: TriggerDirection) -> bool:
        if direction == TriggerDirection.ABOVE:
            return self.price >= trigger_price
        elif direction == TriggerDirection.BELOW:
            return self.price <= trigger_price
        return False
