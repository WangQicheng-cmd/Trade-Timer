#!/usr/bin/env python3
"""
FeeSplitter 合约一键部署脚本

功能：
1. 自动编译 Solidity 合约（需 py-solc-x）或手动输入 bytecode
2. 部署到公链
3. 验证合约
4. 自动把合约地址写入 config.json

使用：
    python deploy.py
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = Path(__file__).resolve().parent
CONTRACT_FILE = BASE_DIR / "contracts" / "FeeSplitter.sol"
CONFIG_FILE = BASE_DIR / "config.json"

CONTRACT_ABI = [
    {
        "inputs": [],
        "stateMutability": "nonpayable",
        "type": "constructor",
    },
    {
        "inputs": [{"internalType": "address", "name": "token", "type": "address"},
                   {"internalType": "uint256", "name": "totalAmount", "type": "uint256"}],
        "name": "splitFee",
        "outputs": [{"internalType": "uint256", "name": "feeAmount", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "splitFeeNative",
        "outputs": [{"internalType": "uint256", "name": "feeAmount", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "address", "name": "token", "type": "address"}],
        "name": "withdrawFees",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "feeWallet",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "FEE_WALLET",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalFeesCollected",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "totalAmount", "type": "uint256"}],
        "name": "getFeeAmount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "pure",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "totalAmount", "type": "uint256"}],
        "name": "getUserAmountAfterFee",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "pure",
        "type": "function",
    },
]

CHAIN_INFO = {
    1: ("以太坊主网 (Ethereum Mainnet)", "https://etherscan.io/tx/"),
    56: ("BSC 主网", "https://bscscan.com/tx/"),
    42161: ("Arbitrum One", "https://arbiscan.io/tx/"),
    137: ("Polygon", "https://polygonscan.com/tx/"),
    10: ("Optimism", "https://optimistic.etherscan.io/tx/"),
    8453: ("Base", "https://basescan.org/tx/"),
    43114: ("Avalanche C-Chain", "https://snowtrace.io/tx/"),
}


def print_banner():
    print(r"""
  ╔══════════════════════════════════════════════════╗
  ║       FeeSplitter 合约一键部署工具               ║
  ║       0.2% 手续费自动分账智能合约                ║
  ╚══════════════════════════════════════════════════╝
    """)


def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    with open(BASE_DIR / "config.example.json", "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def compile_contract():
    """使用 py-solc-x 编译合约"""
    try:
        from solcx import compile_source, install_solc, get_installed_solc_versions
    except ImportError:
        print("\n py-solc-x 未安装，正在安装...")
        os.system(f"{sys.executable} -m pip install py-solc-x")
        from solcx import compile_source, install_solc, get_installed_solc_versions

    source = CONTRACT_FILE.read_text(encoding="utf-8")

    installed = get_installed_solc_versions()
    if not installed:
        print(" 正在下载 Solidity 编译器 (0.8.20)...")
        install_solc("0.8.20")

    print(" 正在编译合约...")
    compiled = compile_source(
        source,
        output_values=["abi", "bin"],
        solc_version="0.8.20",
    )

    contract_key = "<stdin>:FeeSplitter"
    if contract_key not in compiled:
        for key in compiled:
            if "FeeSplitter" in key:
                contract_key = key
                break

    contract_data = compiled[contract_key]
    return contract_data["abi"], contract_data["bin"]


def main():
    print_banner()

    print("【第 1 步】检查环境\n")

    try:
        from web3 import Web3
    except ImportError:
        print(" web3 未安装，正在安装...")
        os.system(f"{sys.executable} -m pip install web3")
        from web3 import Web3

    cfg = load_config()
    rpc_url = cfg.get("web3", {}).get("rpc_url", "")
    chain_id = cfg.get("web3", {}).get("chain_id", 1)
    fee_wallet = cfg.get("web3", {}).get("fee_wallet_address", "")

    chain_name, explorer = CHAIN_INFO.get(chain_id, (f"Chain {chain_id}", ""))

    print(f"  目标链: {chain_name}")
    print(f"  RPC: {rpc_url}")
    print(f"  收款钱包: {fee_wallet}")
    print()

    if not rpc_url:
        rpc_url = input("  请输入 RPC URL: ").strip()
        if not rpc_url:
            print(" RPC URL 不能为空")
            return

    if not fee_wallet:
        print("  ⚠ 未配置收款钱包地址！")
        print(f"  本合约已硬编码收款地址: 0xB4b9a2DcdcCf91713E8bCE68BD436Fa8062Db6A6")
        fee_wallet = "0xB4b9a2DcdcCf91713E8bCE68BD436Fa8062Db6A6"

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print("  ❌ 无法连接 RPC 节点，请检查 RPC URL")
        return
    print("  ✅ RPC 连接成功")

    print(f"\n【第 2 步】输入部署钱包私钥\n")
    print("  ⚠ 私钥仅用于签名部署交易，不会上传任何服务器")
    print("  ⚠ 部署钱包需要有足够的 {0} 作为 gas 费\n".format("ETH" if chain_id == 1 else "BNB" if chain_id == 56 else "gas"))

    private_key = os.environ.get("PRIVATE_KEY", "").strip()
    if private_key:
        print("  已从 PRIVATE_KEY 环境变量读取")
        use_env = input("  使用此私钥？(Y/n): ").strip().lower()
        if use_env == "n":
            private_key = input("  请输入私钥: ").strip()
    else:
        private_key = input("  请输入私钥 (0x...): ").strip()

    if not private_key:
        print("  ❌ 私钥不能为空")
        return

    if not private_key.startswith("0x"):
        private_key = "0x" + private_key

    try:
        account = w3.eth.account.from_key(private_key)
    except Exception as e:
        print(f"  ❌ 私钥无效: {e}")
        return

    balance = w3.eth.get_balance(account.address)
    balance_eth = w3.from_wei(balance, "ether")
    print(f"\n  部署钱包: {account.address}")
    print(f"  余额: {balance_eth:.6f} ETH")

    if balance == 0:
        print("  ⚠ 余额为 0，无法支付 gas 费，请先给该钱包充值")
        proceed = input("  仍然继续？(y/N): ").strip().lower()
        if proceed != "y":
            return

    print(f"\n【第 3 步】编译合约\n")

    bytecode = None
    abi = CONTRACT_ABI

    try:
        abi, bytecode = compile_contract()
        print("  ✅ 合约编译成功（py-solc-x）")
    except Exception as e:
        print(f"  ⚠ 自动编译失败: {e}")
        print("\n  请使用 Remix IDE 部署获取 bytecode：")
        print("  1. 打开 https://remix.ethereum.org")
        print("  2. 创建 FeeSplitter.sol，粘贴 contracts/FeeSplitter.sol 内容")
        print("  3. 编译后复制 Bytecode（最下方按钮）")
        print()
        bytecode = input("  请粘贴 bytecode (0x...): ").strip()
        if not bytecode:
            print("  ❌ 未提供 bytecode，退出")
            return

    print(f"\n【第 4 步】部署合约到 {chain_name}\n")

    if not bytecode.startswith("0x"):
        bytecode = "0x" + bytecode

    try:
        FeeSplitter = w3.eth.contract(abi=abi, bytecode=bytecode)

        estimate = w3.eth.estimate_gas(
            {"from": account.address, "data": bytecode}
        )
        gas_price = w3.eth.gas_price
        total_cost = w3.from_wei(estimate * gas_price, "ether")
        print(f"  预估 gas: {estimate}")
        print(f"  当前 gas price: {w3.from_wei(gas_price, 'gwei'):.2f} Gwei")
        print(f"  预估费用: {total_cost:.6f} ETH")

        confirm = input(f"\n  确认部署到 {chain_name}？(Y/n): ").strip().lower()
        if confirm == "n":
            print("  已取消")
            return

        print("\n  正在发送部署交易...")
        tx = FeeSplitter.constructor().build_transaction(
            {
                "from": account.address,
                "nonce": w3.eth.get_transaction_count(account.address),
                "gas": estimate + 50000,
                "gasPrice": gas_price,
                "chainId": chain_id,
            }
        )

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_hex = w3.to_hex(tx_hash)

        print(f"  📤 部署交易已发送: {tx_hex}")
        if explorer:
            print(f"  🔍 查看交易: {explorer}{tx_hex}")

        print("\n  ⏳ 等待区块确认...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
        contract_address = receipt["contractAddress"]

        if receipt["status"] == 1:
            print(f"\n  ✅ 部署成功！")
            print(f"  📄 合约地址: {contract_address}")
            if explorer:
                base_explorer = explorer.replace("/tx/", "/address/")
                print(f"  🔍 查看合约: {base_explorer}{contract_address}")
        else:
            print(f"\n  ❌ 部署失败（交易回滚）")
            print(f"  交易哈希: {tx_hex}")
            return

    except Exception as e:
        print(f"\n  ❌ 部署异常: {e}")
        return

    print(f"\n【第 5 步】验证合约\n")

    try:
        contract = w3.eth.contract(address=contract_address, abi=abi)
        deployed_fee_wallet = contract.functions.feeWallet().call()
        print(f"  合约 feeWallet: {deployed_fee_wallet}")
        print(f"  预期 feeWallet: {fee_wallet}")

        if deployed_fee_wallet.lower() == fee_wallet.lower():
            print("  ✅ 收款地址验证通过！0.2% 手续费将自动转入此地址")
        else:
            print("  ⚠ 地址不匹配，请检查合约代码")

        fee_for_1000 = contract.functions.getFeeAmount(1000).call()
        print(f"  验证: 1000 代币手续费 = {fee_for_1000} (应为 2，即 0.2%)")

    except Exception as e:
        print(f"  ⚠ 验证失败: {e}")

    print(f"\n【第 6 步】写入配置\n")

    if "web3" not in cfg:
        cfg["web3"] = {}
    cfg["web3"]["fee_splitter_address"] = contract_address
    cfg["web3"]["fee_wallet_address"] = fee_wallet
    save_config(cfg)

    print(f"  ✅ 已写入 config.json:")
    print(f"     web3.fee_splitter_address = {contract_address}")
    print(f"     web3.fee_wallet_address = {fee_wallet}")

    print(f"\n{'='*55}")
    print(f"  🎉 部署完成！")
    print(f"{'='*55}")
    print(f"  合约地址: {contract_address}")
    print(f"  收款钱包: {fee_wallet}")
    print(f"  手续费率: 0.2% (每笔成交自动扣除)")
    print(f"{'='*55}")
    print(f"\n  现在可以运行: python main.py status  检查系统状态")
    print(f"  或运行:       python main.py monitor 启动监控\n")


if __name__ == "__main__":
    main()
