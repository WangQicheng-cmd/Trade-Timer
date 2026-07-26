import sys
from typing import Any, Dict

from .core.logger import logger
from .core.database import db
from .core.models import TaskStatus, TriggerDirection
from .ai.parser import parser
from .market.provider import market_service
from .scheduler.monitor import task_monitor
from .web3.service import web3_service, wallet_manager


class TradeAlarmApp:
    def __init__(self) -> None:
        self._setup_callbacks()

    def _setup_callbacks(self) -> None:
        task_monitor.on_trigger(self._on_task_triggered)

    def _on_task_triggered(self, task: Dict[str, Any], tick) -> None:
        task_id = task["id"]
        logger.info(f"⚡ 触发交易执行: 任务 #{task_id}")

        try:
            result = web3_service.execute_trade(
                symbol=task["symbol"],
                side=task["side"],
                amount=task.get("amount") or 0,
                amount_type=task.get("amount_type", "quote"),
                price=tick.price,
            )

            if result["success"]:
                db.update_task_status(
                    task_id,
                    TaskStatus.EXECUTED.value,
                    tx_hash=result["tx_hash"],
                    fee_amount=result["fee_amount"],
                )
                logger.info(f"✅ 任务 #{task_id} 执行成功! 手续费: {result['fee_amount']:.4f}")
            else:
                db.update_task_status(
                    task_id,
                    TaskStatus.FAILED.value,
                    error_message=result.get("error", "未知错误"),
                )
                logger.error(f"❌ 任务 #{task_id} 执行失败: {result.get('error')}")

        except Exception as e:
            db.update_task_status(task_id, TaskStatus.FAILED.value, error_message=str(e))
            logger.error(f"任务 #{task_id} 执行异常: {e}")

    def create_task(self, user_input: str) -> Dict[str, Any]:
        parsed = parser.parse(user_input)
        task_dict = parsed.to_task_dict(user_input)
        task_id = db.create_task(task_dict)

        task = db.get_task(task_id) or {}
        logger.info(f"✅ 任务 #{task_id} 已创建")
        logger.info(f"   交易对: {task.get('symbol')}")
        logger.info(f"   方向: {'买入' if task.get('side') == 'buy' else '卖出'}")
        if task.get("trigger_price"):
            direction = task.get("trigger_direction", "")
            dir_cn = "涨到" if direction == "above" else "跌到"
            logger.info(f"   触发条件: {dir_cn} ${task['trigger_price']:,.2f}")
        if task.get("delay_seconds", 0) > 0:
            delay = task["delay_seconds"]
            hours = delay // 3600
            minutes = (delay % 3600) // 60
            logger.info(f"   延迟: {hours}小时{minutes}分钟后开始监控")
        if task.get("amount"):
            logger.info(f"   数量: {task['amount']} {task.get('amount_type')}")

        return task

    def list_tasks(self, status: str = "", limit: int = 20) -> None:
        tasks = db.list_tasks(status=status or None, limit=limit)
        if not tasks:
            print("暂无任务")
            return

        status_map = {
            "pending": "⏳ 待启动",
            "waiting": "⏰ 等待中",
            "monitoring": "👀 监控中",
            "triggered": "🔔 已触发",
            "executed": "✅ 已执行",
            "failed": "❌ 失败",
            "cancelled": "🚫 已取消",
        }

        print(f"\n{'ID':<5} {'状态':<10} {'交易对':<12} {'方向':<6} {'触发价':<12} {'创建时间'}")
        print("-" * 80)
        for t in tasks:
            status_text = status_map.get(t["status"], t["status"])
            side_text = "买入" if t["side"] == "buy" else "卖出"
            price_text = f"${t['trigger_price']:,.2f}" if t.get("trigger_price") else "-"
            created = t["created_at"][:19].replace("T", " ")
            print(f"{t['id']:<5} {status_text:<10} {t['symbol']:<12} {side_text:<6} {price_text:<12} {created}")
        print()

    def show_task(self, task_id: int) -> None:
        task = db.get_task(task_id)
        if not task:
            print(f"任务 #{task_id} 不存在")
            return

        status_map = {
            "pending": "⏳ 待启动",
            "waiting": "⏰ 等待中",
            "monitoring": "👀 监控中",
            "triggered": "🔔 已触发",
            "executed": "✅ 已执行",
            "failed": "❌ 失败",
            "cancelled": "🚫 已取消",
        }

        print(f"\n{'='*50}")
        print(f"任务 #{task['id']}")
        print(f"{'='*50}")
        print(f"状态: {status_map.get(task['status'], task['status'])}")
        print(f"用户输入: {task['user_input']}")
        print(f"交易对: {task['symbol']}")
        print(f"方向: {'买入' if task['side'] == 'buy' else '卖出'}")
        if task.get("trigger_price"):
            direction = "高于" if task["trigger_direction"] == "above" else "低于"
            print(f"触发条件: 价格 {direction} ${task['trigger_price']:,.2f}")
        if task.get("amount"):
            print(f"数量: {task['amount']} {task.get('amount_type')}")
        if task.get("delay_seconds", 0) > 0:
            print(f"延迟: {task['delay_seconds']} 秒")
        print(f"创建时间: {task['created_at']}")
        print(f"更新时间: {task['updated_at']}")
        if task.get("start_time"):
            print(f"开始时间: {task['start_time']}")
        if task.get("trigger_time"):
            print(f"触发时间: {task['trigger_time']}")
        if task.get("tx_hash"):
            print(f"交易哈希: {task['tx_hash']}")
        if task.get("fee_amount"):
            print(f"手续费: {task['fee_amount']:.6f}")
        if task.get("error_message"):
            print(f"错误信息: {task['error_message']}")
        print(f"{'='*50}\n")

    def cancel_task(self, task_id: int) -> bool:
        task = db.get_task(task_id)
        if not task:
            print(f"任务 #{task_id} 不存在")
            return False

        if task["status"] in ("executed", "failed", "cancelled"):
            print(f"任务 #{task_id} 已是终态，无法取消")
            return False

        db.update_task_status(task_id, TaskStatus.CANCELLED.value)
        logger.info(f"任务 #{task_id} 已取消")
        return True

    def get_price(self, symbol: str) -> None:
        try:
            tick = market_service.get_price(symbol)
            print(f"\n💰 {tick.symbol} 当前价格: ${tick.price:,.2f}\n")
        except Exception as e:
            print(f"\n❌ 获取价格失败: {symbol}")
            print(f"   原因: {e}")
            print(f"   解决方法:")
            print(f"   1. 检查网络连接是否正常")
            print(f"   2. 在 config.json 中设置 market.proxy 配置代理")
            print(f"   3. 示例: \"proxy\": \"http://127.0.0.1:7890\"\n")

    def start_monitor(self) -> None:
        task_monitor.start()
        logger.info("监控引擎运行中，按 Ctrl+C 停止...")
        try:
            import time

            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("正在停止...")
            task_monitor.stop()

    def check_status(self) -> None:
        print("\n📊 系统状态检查")
        print("=" * 40)

        from .ai.parser import TradeCommandParser
        ai = TradeCommandParser()
        ollama_ok = ai.ollama.is_available()
        print(f"Ollama 服务: {'✅ 可用' if ollama_ok else '❌ 不可用'}")

        try:
            market_service.get_price("BTC/USDT", use_cache=False)
            print("行情服务: ✅ 可用")
        except Exception:
            print("行情服务: ❌ 不可用")

        web3_ok = web3_service.is_available()
        print(f"Web3 连接: {'✅ 可用' if web3_ok else '⚠️ 未配置'}")

        wallet_ok = wallet_manager.is_ready()
        print(f"钱包配置: {'✅ 已加载' if wallet_ok else '⚠️ 未配置'}")

        monitoring_count = len(db.get_monitoring_tasks())
        waiting_count = len(db.list_tasks(status="waiting"))
        print(f"监控中任务: {monitoring_count}")
        print(f"等待中任务: {waiting_count}")
        print("=" * 40 + "\n")


app = TradeAlarmApp()
