import time
import threading
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..core.config import config
from ..core.database import db
from ..core.logger import logger
from ..core.models import PriceTick, TaskStatus, TriggerDirection
from ..market.provider import market_service


class TaskMonitor:
    def __init__(self) -> None:
        self.check_interval = config.get("scheduler.check_interval_seconds", 5)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._trigger_callbacks: List[Callable] = []

    def on_trigger(self, callback: Callable) -> None:
        self._trigger_callbacks.append(callback)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="TaskMonitor")
        self._thread.start()
        logger.info("任务监控引擎已启动")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("任务监控引擎已停止")

    def _run(self) -> None:
        while self._running:
            try:
                self._tick()
            except Exception as e:
                logger.error(f"调度器 tick 异常: {e}")
            time.sleep(self.check_interval)

    def _tick(self) -> None:
        self._activate_waiting_tasks()
        self._check_monitoring_tasks()

    def _activate_waiting_tasks(self) -> None:
        now = datetime.utcnow().isoformat()
        tasks = db.get_pending_tasks_to_start(now)
        for task in tasks:
            task_id = task["id"]
            symbol = task["symbol"]
            logger.info(f"任务 #{task_id} ({symbol}) 到启动时间，进入监控状态")
            db.update_task_status(task_id, TaskStatus.MONITORING.value)

    def _check_monitoring_tasks(self) -> None:
        tasks = db.get_monitoring_tasks()
        if not tasks:
            return

        symbols = set(t["symbol"] for t in tasks)
        prices: Dict[str, PriceTick] = {}
        for symbol in symbols:
            try:
                prices[symbol] = market_service.get_price(symbol, use_cache=False)
            except Exception as e:
                logger.warning(f"获取 {symbol} 价格失败: {e}")

        for task in tasks:
            task_id = task["id"]
            symbol = task["symbol"]
            if symbol not in prices:
                continue

            tick = prices[symbol]
            trigger_price = task.get("trigger_price")
            direction_str = task.get("trigger_direction")

            if trigger_price is None or not direction_str:
                self._trigger_task(task, tick, "无价格条件，立即触发")
                continue

            try:
                direction = TriggerDirection(direction_str)
            except ValueError:
                continue

            if tick.check_trigger(trigger_price, direction):
                reason = f"价格 {tick.price:,.2f} {direction.value} 触发价 {trigger_price:,.2f}"
                self._trigger_task(task, tick, reason)

    def _trigger_task(self, task: Dict[str, Any], tick: PriceTick, reason: str) -> None:
        task_id = task["id"]
        logger.info(f"🔔 任务 #{task_id} 触发: {reason}")
        db.update_task_status(
            task_id,
            TaskStatus.TRIGGERED.value,
            trigger_time=datetime.utcnow().isoformat(),
        )

        for callback in self._trigger_callbacks:
            try:
                callback(task, tick)
            except Exception as e:
                logger.error(f"触发回调执行失败: {e}")


task_monitor = TaskMonitor()
