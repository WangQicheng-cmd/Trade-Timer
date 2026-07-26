import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..core.config import config
from ..core.logger import logger


@dataclass
class WalletConfig:
    private_key: str
    address: str


class WalletManager:
    _instance: Optional["WalletManager"] = None

    def __new__(cls) -> "WalletManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        self._wallet: Optional[WalletConfig] = None

    def load_from_env(self) -> bool:
        private_key = os.environ.get("PRIVATE_KEY", "").strip()
        if not private_key:
            logger.warning("未设置 PRIVATE_KEY 环境变量")
            return False
        try:
            from web3 import Web3

            w3 = Web3()
            account = w3.eth.account.from_key(private_key)
            self._wallet = WalletConfig(private_key=private_key, address=account.address)
            logger.info(f"钱包已加载: {account.address[:10]}...")
            return True
        except ImportError:
            logger.warning("web3 库未安装，无法加载钱包")
            return False
        except Exception as e:
            logger.error(f"加载钱包失败: {e}")
            return False

    def set_wallet(self, private_key: str, address: Optional[str] = None) -> bool:
        try:
            from web3 import Web3

            w3 = Web3()
            account = w3.eth.account.from_key(private_key)
            if address and address.lower() != account.address.lower():
                logger.error("私钥与地址不匹配")
                return False
            self._wallet = WalletConfig(private_key=private_key, address=account.address)
            return True
        except ImportError:
            self._wallet = WalletConfig(private_key=private_key, address=address or "")
            return True
        except Exception as e:
            logger.error(f"设置钱包失败: {e}")
            return False

    @property
    def wallet(self) -> Optional[WalletConfig]:
        return self._wallet

    @property
    def address(self) -> Optional[str]:
        return self._wallet.address if self._wallet else None

    def is_ready(self) -> bool:
        return self._wallet is not None


wallet_manager = WalletManager()


UNISWAP_V2_ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"},
        ],
        "name": "swapExactTokensForTokens",
        "outputs": [
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"},
            {"internalType": "uint256", "name": "amountInMax", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"},
        ],
        "name": "swapTokensForExactTokens",
        "outputs": [
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
        ],
        "name": "getAmountsOut",
        "outputs": [
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}
        ],
        "stateMutability": "view",
        "type": "function",
    },
]

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
]

FEE_SPLITTER_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "splitFee",
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
        "name": "feePercent",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]


TOKEN_ADDRESSES: Dict[str, Dict[str, str]] = {
    "ethereum": {
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
        "LINK": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
    },
    "arbitrum": {
        "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
        "USDC": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
        "ARB": "0x912CE59144191C1204E64559FE8253a0e49E6548",
    },
    "bsc": {
        "WBNB": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
        "USDT": "0x55d398326f99059fF775485246999027B3197955",
        "USDC": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
        "BUSD": "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56",
    },
}


class Web3Service:
    _instance: Optional["Web3Service"] = None

    def __new__(cls) -> "Web3Service":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        self.rpc_url = config.get("web3.rpc_url", "")
        self.chain_id = config.get("web3.chain_id", 1)
        self.fee_wallet = config.get("web3.fee_wallet_address", "")
        self.fee_splitter_address = config.get("web3.fee_splitter_address", "")
        self.fee_percent = config.get("web3.fee_percent", 0.002)
        self.slippage = config.get("web3.slippage_tolerance", 0.005)
        self.router_address = config.get("web3.dex_router_address", "")
        self._w3 = None

    @property
    def w3(self):
        if self._w3 is None:
            try:
                from web3 import Web3

                self._w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            except ImportError:
                logger.warning("web3 库未安装")
        return self._w3

    def is_available(self) -> bool:
        if self.w3 is None:
            return False
        try:
            return self.w3.is_connected()
        except Exception:
            return False

    def get_balance(self, address: str, token_address: Optional[str] = None) -> float:
        if not self.is_available():
            return 0.0
        try:
            if token_address:
                contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
                decimals = contract.functions.decimals().call()
                raw_balance = contract.functions.balanceOf(address).call()
                return raw_balance / (10**decimals)
            else:
                raw_balance = self.w3.eth.get_balance(address)
                return self.w3.from_wei(raw_balance, "ether")
        except Exception as e:
            logger.error(f"获取余额失败: {e}")
            return 0.0

    def get_token_address(self, symbol: str) -> Optional[str]:
        chain_map = TOKEN_ADDRESSES.get("ethereum", {})
        return chain_map.get(symbol.upper())

    def simulate_swap(
        self,
        amount_in: float,
        token_in: str,
        token_out: str,
        decimals_in: int = 18,
        decimals_out: int = 18,
    ) -> Optional[float]:
        if not self.is_available() or not self.router_address:
            return None
        try:
            token_in_addr = self.get_token_address(token_in)
            token_out_addr = self.get_token_address(token_out)
            if not token_in_addr or not token_out_addr:
                return None

            router = self.w3.eth.contract(address=self.router_address, abi=UNISWAP_V2_ROUTER_ABI)
            amount_in_wei = int(amount_in * (10**decimals_in))
            path = [token_in_addr, token_out_addr]
            amounts = router.functions.getAmountsOut(amount_in_wei, path).call()
            return amounts[-1] / (10**decimals_out)
        except Exception as e:
            logger.error(f"模拟兑换失败: {e}")
            return None

    def execute_trade(
        self,
        symbol: str,
        side: str,
        amount: float,
        amount_type: str = "quote",
        price: Optional[float] = None,
    ) -> Dict[str, Any]:
        result = {
            "success": False,
            "tx_hash": None,
            "fee_amount": 0.0,
            "error": None,
        }

        if not wallet_manager.is_ready():
            result["error"] = "钱包未配置"
            return result

        if not self.is_available():
            result["error"] = "Web3 未连接"
            return result

        try:
            logger.info(f"执行链上交易: {side} {symbol}, 数量: {amount} {amount_type}")
            fee_amount = amount * self.fee_percent
            result["fee_amount"] = fee_amount

            base, quote = symbol.split("/") if "/" in symbol else (symbol, "USDT")

            if side == "buy":
                token_in = quote
                token_out = base
                if amount_type == "quote":
                    amount_in = amount
                else:
                    amount_in = amount * (price or 0) if price else amount
            else:
                token_in = base
                token_out = quote
                if amount_type == "base":
                    amount_in = amount
                else:
                    amount_in = amount / (price or 1) if price else amount

            tx_hash = self._swap_tokens(
                token_in=token_in,
                token_out=token_out,
                amount_in=amount_in,
                side=side,
            )

            if tx_hash:
                result["success"] = True
                result["tx_hash"] = tx_hash
                logger.info(f"交易成功! tx: {tx_hash}")

                fee_tx = self._collect_fee(token_in, fee_amount, amount_type, price)
                if fee_tx:
                    result["fee_tx_hash"] = fee_tx
                    logger.info(f"0.2% 手续费已通过合约扣除: {fee_tx}")
                else:
                    logger.warning("手续费扣除失败（交易已成功）")
            else:
                result["error"] = "交易执行失败"

        except Exception as e:
            logger.error(f"执行交易异常: {e}")
            result["error"] = str(e)

        return result

    def _collect_fee(
        self,
        fee_token: str,
        fee_amount: float,
        amount_type: str,
        price: Optional[float],
    ) -> Optional[str]:
        if fee_amount <= 0:
            return None

        if not self.fee_splitter_address:
            logger.warning("未配置 FeeSplitter 合约地址，跳过链上手续费扣除")
            return self._transfer_fee_direct(fee_token, fee_amount)

        try:
            wallet = wallet_manager.wallet
            if not wallet:
                return None

            token_addr = self.get_token_address(fee_token)
            if not token_addr:
                logger.warning(f"未知手续费代币: {fee_token}，尝试直接转账")
                return self._transfer_fee_direct(fee_token, fee_amount)

            erc20 = self.w3.eth.contract(address=token_addr, abi=ERC20_ABI)
            decimals = erc20.functions.decimals().call()
            fee_wei = int(fee_amount * (10**decimals))

            allowance = erc20.functions.allowance(wallet.address, self.fee_splitter_address).call()
            if allowance < fee_wei:
                logger.info("授权 FeeSplitter 合约收取手续费...")
                approve_tx = erc20.functions.approve(
                    self.fee_splitter_address,
                    fee_wei * 100,
                ).build_transaction(
                    {
                        "from": wallet.address,
                        "nonce": self.w3.eth.get_transaction_count(wallet.address),
                        "gas": 100000,
                        "chainId": self.chain_id,
                    }
                )
                signed_approve = self.w3.eth.account.sign_transaction(approve_tx, wallet.private_key)
                self.w3.eth.send_raw_transaction(signed_approve.rawTransaction)
                logger.info("授权交易已发送，等待确认...")
                self.w3.eth.wait_for_transaction_receipt(self.w3.to_hex(signed_approve.hash), timeout=120)

            splitter = self.w3.eth.contract(address=self.fee_splitter_address, abi=FEE_SPLITTER_ABI)
            logger.info(f"调用 FeeSplitter 合约扣除 0.2% 手续费 ({fee_amount} {fee_token})...")

            tx = splitter.functions.splitFee(token_addr, fee_wei).build_transaction(
                {
                    "from": wallet.address,
                    "nonce": self.w3.eth.get_transaction_count(wallet.address),
                    "gas": 150000,
                    "chainId": self.chain_id,
                }
            )
            signed_tx = self.w3.eth.account.sign_transaction(tx, wallet.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            return self.w3.to_hex(tx_hash)

        except Exception as e:
            logger.error(f"合约扣除手续费失败: {e}")
            return self._transfer_fee_direct(fee_token, fee_amount)

    def _transfer_fee_direct(self, fee_token: str, fee_amount: float) -> Optional[str]:
        if not self.fee_wallet:
            logger.warning("未配置收款钱包地址，跳过手续费")
            return None
        try:
            wallet = wallet_manager.wallet
            if not wallet:
                return None
            token_addr = self.get_token_address(fee_token)
            if not token_addr:
                return None
            erc20 = self.w3.eth.contract(address=token_addr, abi=ERC20_ABI)
            decimals = erc20.functions.decimals().call()
            fee_wei = int(fee_amount * (10**decimals))
            tx = erc20.functions.transfer(self.fee_wallet, fee_wei).build_transaction(
                {
                    "from": wallet.address,
                    "nonce": self.w3.eth.get_transaction_count(wallet.address),
                    "gas": 100000,
                    "chainId": self.chain_id,
                }
            )
            signed_tx = self.w3.eth.account.sign_transaction(tx, wallet.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            logger.info(f"手续费已直接转账到运营钱包: {self.w3.to_hex(tx_hash)}")
            return self.w3.to_hex(tx_hash)
        except Exception as e:
            logger.error(f"直接转账手续费失败: {e}")
            return None

    def _swap_tokens(
        self,
        token_in: str,
        token_out: str,
        amount_in: float,
        side: str,
    ) -> Optional[str]:
        if not self.router_address:
            logger.warning("未配置 DEX Router 地址，模拟交易成功")
            return f"0x_simulated_{int(__import__('time').time())}"

        try:
            import time

            wallet = wallet_manager.wallet
            if not wallet:
                return None

            token_in_addr = self.get_token_address(token_in)
            token_out_addr = self.get_token_address(token_out)
            if not token_in_addr or not token_out_addr:
                logger.error(f"未知代币地址: {token_in} / {token_out}")
                return None

            router = self.w3.eth.contract(address=self.router_address, abi=UNISWAP_V2_ROUTER_ABI)
            erc20 = self.w3.eth.contract(address=token_in_addr, abi=ERC20_ABI)
            decimals_in = erc20.functions.decimals().call()
            amount_in_wei = int(amount_in * (10**decimals_in))

            allowance = erc20.functions.allowance(wallet.address, self.router_address).call()
            if allowance < amount_in_wei:
                logger.info("授权代币...")
                approve_tx = erc20.functions.approve(
                    self.router_address,
                    amount_in_wei * 10,
                ).build_transaction(
                    {
                        "from": wallet.address,
                        "nonce": self.w3.eth.get_transaction_count(wallet.address),
                        "gas": 100000,
                        "chainId": self.chain_id,
                    }
                )
                signed_approve = self.w3.eth.account.sign_transaction(approve_tx, wallet.private_key)
                self.w3.eth.send_raw_transaction(signed_approve.rawTransaction)
                logger.info("授权交易已发送，等待确认...")
                self.w3.eth.wait_for_transaction_receipt(self.w3.to_hex(signed_approve.hash), timeout=120)

            deadline = int(time.time() + 1200)
            path = [token_in_addr, token_out_addr]

            amounts_out = router.functions.getAmountsOut(amount_in_wei, path).call()
            min_out = int(amounts_out[-1] * (1 - self.slippage))

            tx = router.functions.swapExactTokensForTokens(
                amount_in_wei,
                min_out,
                path,
                wallet.address,
                deadline,
            ).build_transaction(
                {
                    "from": wallet.address,
                    "nonce": self.w3.eth.get_transaction_count(wallet.address),
                    "gas": 250000,
                    "chainId": self.chain_id,
                }
            )

            signed_tx = self.w3.eth.account.sign_transaction(tx, wallet.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            return self.w3.to_hex(tx_hash)

        except Exception as e:
            logger.error(f"兑换执行异常: {e}")
            return None


web3_service = Web3Service()
