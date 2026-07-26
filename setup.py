#!/usr/bin/env python3
"""
AI 交易闹钟 - 首次配置向导

引导用户完成：
1. 检查 Python 依赖
2. 检查 Ollama 服务
3. 配置 RPC 节点
4. 配置用户钱包
5. 部署 FeeSplitter 合约（可选）
6. 完成配置
"""
import json
import os
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"
CONFIG_EXAMPLE = BASE_DIR / "config.example.json"


BANNER = r"""
  ╔══════════════════════════════════════════════════╗
  ║       AI 交易闹钟 - 首次配置向导                 ║
  ║       本地运行 · 链上交易 · 自然语言创建         ║
  ╚══════════════════════════════════════════════════╝
"""


def step(n, title):
    print(f"\n{'='*55}")
    print(f"  第 {n} 步: {title}")
    print(f"{'='*55}\n")


def run(cmd):
    try:
        result = subprocess.run(
            [sys.executable] + cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0
    except Exception:
        return False


def check_module(name):
    try:
        __import__(name)
        return True
    except ImportError:
        return False


def main():
    print(BANNER)
    print("  本向导将引导你完成所有配置，大约需要 5 分钟。\n")

    step(1, "检查 Python 依赖")

    deps = {"requests": "HTTP 请求", "web3": "以太坊链上交互"}
    missing = []
    for mod, desc in deps.items():
        if check_module(mod):
            print(f"  ✅ {mod} ({desc})")
        else:
            print(f"  ❌ {mod} ({desc}) - 缺失")
            missing.append(mod)

    if missing:
        print(f"\n  正在安装缺失依赖: {', '.join(missing)}")
        ok = run(["-m", "pip", "install"] + missing)
        if ok:
            print("  ✅ 依赖安装成功")
        else:
            print("  ❌ 依赖安装失败，请手动运行: pip install -r requirements.txt")
            cont = input("  继续配置？(y/N): ").strip().lower()
            if cont != "y":
                return
    else:
        print("  ✅ 所有依赖已就绪")

    step(2, "检查 Ollama 服务")

    ollama_ok = False
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        ollama_ok = resp.status_code == 200
    except Exception:
        pass

    if ollama_ok:
        print("  ✅ Ollama 服务运行中")
        try:
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            if models:
                print(f"  已安装模型: {', '.join(models)}")
            else:
                print("  ⚠ 未发现已安装模型")
                print("  请运行: ollama pull deepseek-r1")
        except Exception:
            pass
    else:
        print("  ❌ Ollama 服务未运行")
        print("  请先安装并启动 Ollama:")
        print("    1. 下载: https://ollama.ai/")
        print("    2. 启动: ollama serve")
        print("    3. 拉取模型: ollama pull deepseek-r1")
        cont = input("\n  Ollama 不可用也继续配置？(y/N): ").strip().lower()
        if cont != "y":
            print("  请先启动 Ollama 后重新运行本向导")
            return

    step(3, "配置区块链节点")

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    else:
        with open(CONFIG_EXAMPLE, "r", encoding="utf-8") as f:
            cfg = json.load(f)

    if "web3" not in cfg:
        cfg["web3"] = {}

    print("  选择部署链:")
    chains = [
        (1, "以太坊主网", "https://eth.llamarpc.com"),
        (42161, "Arbitrum One", "https://arb1.arbitrum.io/rpc"),
        (56, "BSC 主网", "https://bsc-dataseed.binance.org"),
        (137, "Polygon", "https://polygon-rpc.com"),
        (10, "Optimism", "https://mainnet.optimism.io"),
        (8453, "Base", "https://mainnet.base.org"),
    ]
    for i, (cid, name, _) in enumerate(chains, 1):
        print(f"    {i}. {name}")

    choice = input(f"\n  选择 (1-{len(chains)}, 默认1): ").strip()
    try:
        idx = int(choice) - 1 if choice else 0
        chain_id, chain_name, default_rpc = chains[max(0, min(idx, len(chains) - 1))]
    except ValueError:
        chain_id, chain_name, default_rpc = chains[0]

    print(f"\n  已选: {chain_name}")
    rpc_url = input(f"  RPC URL (回车使用默认 {default_rpc}): ").strip()
    if not rpc_url:
        rpc_url = default_rpc

    cfg["web3"]["chain_id"] = chain_id
    cfg["web3"]["rpc_url"] = rpc_url

    print(f"\n  ✅ 收款钱包地址（运营方，已硬编码进合约）:")
    print(f"     {cfg['web3'].get('fee_wallet_address', '0xB4b9a2DcdcCf91713E8bCE68BD436Fa8062Db6A6')}")

    step(4, "配置用户钱包")

    print("  ⚠ 你的私钥仅存在本地内存，不会上传任何服务器")
    print("  ⚠ 请确保钱包有足够的代币和 gas 费\n")

    private_key = os.environ.get("PRIVATE_KEY", "").strip()
    if private_key:
        print(f"  已从 PRIVATE_KEY 环境变量读取")
        use_env = input("  使用此私钥？(Y/n): ").strip().lower()
        if use_env == "n":
            private_key = input("  请输入私钥 (0x...): ").strip()
    else:
        private_key = input("  请输入你的钱包私钥 (0x...): ").strip()

    if not private_key:
        print("  ⚠ 未配置私钥，可稍后通过 'python main.py wallet set' 配置")
    else:
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key
        try:
            from web3 import Web3
            w3 = Web3()
            account = w3.eth.account.from_key(private_key)
            print(f"\n  ✅ 钱包地址: {account.address}")

            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                if w3.is_connected():
                    balance = w3.eth.get_balance(account.address)
                    print(f"  余额: {w3.from_wei(balance, 'ether'):.6f}")
            except Exception:
                pass
        except Exception as e:
            print(f"  ❌ 私钥无效: {e}")
            private_key = ""

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

    if private_key:
        env_file = BASE_DIR / ".env"
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(f"PRIVATE_KEY={private_key}\n")
        print("  ✅ 私钥已写入 .env 文件")

    step(5, "部署 FeeSplitter 合约（可选）")

    has_splitter = bool(cfg["web3"].get("fee_splitter_address"))
    if has_splitter:
        print(f"  ✅ 已配置合约地址: {cfg['web3']['fee_splitter_address']}")
    else:
        print("  FeeSplitter 合约负责自动扣除 0.2% 手续费到运营钱包")
        print("  需要部署到公链才能生效\n")
        deploy_now = input("  现在部署合约？(Y/n): ").strip().lower()
        if deploy_now != "n":
            print("\n  启动部署脚本...\n")
            deploy_script = BASE_DIR / "deploy.py"
            if deploy_script.exists():
                os.system(f"{sys.executable} {deploy_script}")
            else:
                print("  ❌ 未找到 deploy.py")
        else:
            print("  ⚠ 跳过部署，可稍后运行: python deploy.py")

    step(6, "配置完成")

    print("  ✅ 配置已完成！")
    print(f"\n  配置文件: {CONFIG_FILE}")
    print(f"  收款钱包: {cfg['web3'].get('fee_wallet_address', 'N/A')}")
    print(f"  合约地址: {cfg['web3'].get('fee_splitter_address', '未部署')}")
    print(f"  DEX Router: {cfg['web3'].get('dex_router_address', 'N/A')}")
    print(f"\n  接下来你可以:")
    print(f"    1. 检查状态:  python main.py status")
    print(f"    2. 创建任务:  python main.py create")
    print(f"    3. 启动监控:  python main.py monitor")
    print(f"    4. 一键启动:  双击 start.bat\n")


if __name__ == "__main__":
    main()
