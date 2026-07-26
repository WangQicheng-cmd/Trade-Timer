#!/usr/bin/env python3
import argparse
import sys
import os
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)


def load_env():
    """从 .env 文件加载环境变量到 os.environ"""
    env_file = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())


load_env()

from src.app import app
from src.core.logger import logger
from src.web3.service import wallet_manager, web3_service
from src.core.config import config


BANNER = r"""
    _    _ _____ _______        _______ _    _  _____
   / \  | |_   _| ____\ \      / / ____| |  | |/ ____|
  / _ \ | | | |  _|  \ \ /\ / /|  _| | |  | | |  _
 / ___ \| | | | | |___  \ V  V / | |___| |__| | |_| |
/_/   \_\_| |_| |_____|  \_/\_/  |_____|\____/ \_____|

  TradeTimer - 本地运行 · 链上交易 · AI 自动盯盘
"""


def cmd_create(args):
    user_input = " ".join(args.text) if args.text else ""
    if not user_input:
        print("请输入交易指令，例如：6小时后 BTC 跌到 58000 买入")
        user_input = input("指令: ").strip()
        if not user_input:
            print("指令不能为空")
            return
    app.create_task(user_input)


def cmd_list(args):
    app.list_tasks(status=args.status, limit=args.limit)


def cmd_show(args):
    app.show_task(args.id)


def cmd_cancel(args):
    app.cancel_task(args.id)


def cmd_price(args):
    app.get_price(args.symbol)


def cmd_monitor(args):
    wallet_manager.load_from_env()
    app.start_monitor()


def cmd_status(args):
    wallet_manager.load_from_env()
    app.check_status()
    fee_splitter = config.get("web3.fee_splitter_address", "")
    fee_wallet = config.get("web3.fee_wallet_address", "")
    print(f"收款钱包: {fee_wallet or '未配置'}")
    print(f"分账合约: {fee_splitter or '未部署 (运行 python deploy.py)'}")
    print("=" * 40 + "\n")


def cmd_deploy(args):
    deploy_script = os.path.join(BASE_DIR, "deploy.py")
    if not os.path.exists(deploy_script):
        print("未找到 deploy.py")
        return
    subprocess.call([sys.executable, deploy_script])


def cmd_setup(args):
    setup_script = os.path.join(BASE_DIR, "setup.py")
    if not os.path.exists(setup_script):
        print("未找到 setup.py")
        return
    subprocess.call([sys.executable, setup_script])


def cmd_wallet(args):
    if args.action == "set":
        private_key = args.key or input("请输入私钥: ").strip()
        if wallet_manager.set_wallet(private_key):
            print(f"✅ 钱包已设置: {wallet_manager.address}")
        else:
            print("❌ 钱包设置失败")
    elif args.action == "show":
        if wallet_manager.is_ready():
            print(f"钱包地址: {wallet_manager.address}")
        else:
            print("未配置钱包")
    elif args.action == "load":
        if wallet_manager.load_from_env():
            print(f"✅ 从环境变量加载: {wallet_manager.address}")
        else:
            print("❌ 加载失败，请设置 PRIVATE_KEY 环境变量")


def main():
    parser = argparse.ArgumentParser(
        description="TradeTimer - 本地运行式链上 AI 交易闹钟",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="示例:\n"
        "  python main.py create \"6小时后 BTC 跌到 58000 买入\"\n"
        "  python main.py monitor\n"
        "  python main.py price BTC/USDT\n"
        "  python main.py status\n",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    create_parser = subparsers.add_parser("create", help="创建交易任务")
    create_parser.add_argument("text", nargs="*", help="交易指令")
    create_parser.set_defaults(func=cmd_create)

    list_parser = subparsers.add_parser("list", help="列出任务")
    list_parser.add_argument("--status", "-s", default="", help="按状态筛选")
    list_parser.add_argument("--limit", "-n", type=int, default=20, help="显示数量")
    list_parser.set_defaults(func=cmd_list)

    show_parser = subparsers.add_parser("show", help="查看任务详情")
    show_parser.add_argument("id", type=int, help="任务 ID")
    show_parser.set_defaults(func=cmd_show)

    cancel_parser = subparsers.add_parser("cancel", help="取消任务")
    cancel_parser.add_argument("id", type=int, help="任务 ID")
    cancel_parser.set_defaults(func=cmd_cancel)

    price_parser = subparsers.add_parser("price", help="查询当前价格")
    price_parser.add_argument("symbol", default="BTC/USDT", nargs="?", help="交易对")
    price_parser.set_defaults(func=cmd_price)

    monitor_parser = subparsers.add_parser("monitor", help="启动监控引擎")
    monitor_parser.set_defaults(func=cmd_monitor)

    status_parser = subparsers.add_parser("status", help="检查系统状态")
    status_parser.set_defaults(func=cmd_status)

    wallet_parser = subparsers.add_parser("wallet", help="钱包管理")
    wallet_parser.add_argument("action", choices=["set", "show", "load"], help="操作")
    wallet_parser.add_argument("--key", help="私钥（set 时使用）")
    wallet_parser.set_defaults(func=cmd_wallet)

    deploy_parser = subparsers.add_parser("deploy", help="部署 FeeSplitter 合约")
    deploy_parser.set_defaults(func=cmd_deploy)

    setup_parser = subparsers.add_parser("setup", help="首次配置向导")
    setup_parser.set_defaults(func=cmd_setup)

    args = parser.parse_args()

    if not args.command:
        print(BANNER)
        parser.print_help()
        return

    print(BANNER)
    args.func(args)


if __name__ == "__main__":
    main()
