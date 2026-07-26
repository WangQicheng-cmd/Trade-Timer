# -*- coding: utf-8 -*-
"""TradeTimer 多语言文案"""

LANGUAGES = {
    "zh": {
        # Banner
        "app_name": "TradeTimer",
        "app_tagline": "本地运行 · 链上交易 · AI 自动盯盘",
        "app_desc": "输入指令创建交易，价格到位自动链上成交",
        "app_fee": "每笔成交自动抽 0.2% 手续费到运营钱包",

        # 首次提示
        "first_run": "检测到首次使用，建议先完成【1.一键配置】",
        "contract_deployed": "合约地址",
        "contract_not_deployed": "合约: 未部署",
        "fee_wallet": "收款钱包",

        # 菜单
        "menu_title": "主功能菜单",
        "menu_setup": "一键配置（首次使用必做）",
        "menu_deploy": "部署手续费合约（仅需一次）",
        "menu_create": "创建交易任务",
        "menu_monitor": "启动监控引擎（自动盯盘交易）",
        "menu_list": "查看我的任务列表",
        "menu_price": "查询当前价格",
        "menu_status": "检查系统状态",
        "menu_wallet": "钱包管理",
        "menu_exit": "退出",
        "menu_prompt": "请输入数字选择 (0-8)",

        # 语言切换
        "menu_lang": "切换语言 / Switch Language",
        "lang_switched": "语言已切换为中文",
        "lang_current": "当前语言",

        # 操作
        "setup_title": "一键配置向导",
        "setup_desc": "将引导你完成：检查依赖 → 配置区块链 → 设置钱包",
        "deploy_title": "部署手续费合约",
        "deploy_desc": "合约将自动扣除每笔成交 0.2% 手续费到运营钱包",
        "deploy_fee_addr": "收款地址",
        "deploy_gas_warn": "需要部署钱包有少量 ETH 作为 gas 费",
        "create_title": "创建交易任务",
        "create_desc": "输入交易计划，AI 自动解析为结构化任务。",
        "create_examples": "示例",
        "create_prompt": "输入指令",
        "create_empty": "指令不能为空",
        "monitor_title": "启动监控引擎",
        "monitor_desc": "引擎将后台运行，自动盯盘",
        "monitor_reach": "到达设定时间 → 开始监控价格",
        "monitor_trigger": "价格满足条件 → 自动链上交易",
        "monitor_fee": "交易成功 → 自动扣 0.2% 手续费",
        "monitor_stop": "按 Ctrl+C 可停止监控",
        "list_title": "我的任务列表",
        "price_title": "查询当前价格",
        "price_prompt": "交易对 (回车默认 BTC/USDT)",
        "status_title": "系统状态检查",
        "wallet_title": "钱包管理",
        "wallet_show": "查看当前钱包",
        "wallet_set": "设置新钱包",
        "wallet_load": "从环境变量加载",
        "wallet_back": "返回主菜单",
        "wallet_prompt": "选择 (0-3)",
        "wallet_key_prompt": "请输入私钥 (0x...)",
        "wallet_key_empty": "私钥不能为空",

        # 通用
        "press_enter": "按回车键返回菜单...",
        "exit_msg": "感谢使用 TradeTimer，再见！",
        "invalid_choice": "无效选择，请重新输入",
        "exit_error": "已退出，再见！",
        "launcher_error": "启动器异常",

        # 依赖安装
        "dep_installing": "首次运行，正在安装依赖...",
        "dep_installed": "依赖安装完成",
        "dep_not_found": "未找到 requirements.txt",
    },

    "en": {
        "app_name": "TradeTimer",
        "app_tagline": "Local-First · On-Chain · AI Auto-Trading",
        "app_desc": "Create trades in plain English, auto-execute when price hits target",
        "app_fee": "0.2% fee auto-deducted from each successful trade",

        "first_run": "First run detected. Please complete [1. Setup] first",
        "contract_deployed": "Contract",
        "contract_not_deployed": "Contract: not deployed",
        "fee_wallet": "Fee Wallet",

        "menu_title": "Main Menu",
        "menu_setup": "Setup (required for first use)",
        "menu_deploy": "Deploy Fee Contract (once only)",
        "menu_create": "Create Trade Task",
        "menu_monitor": "Start Monitor Engine (auto-trade)",
        "menu_list": "View My Tasks",
        "menu_price": "Query Current Price",
        "menu_status": "Check System Status",
        "menu_wallet": "Wallet Management",
        "menu_exit": "Exit",
        "menu_prompt": "Enter number (0-8)",

        "menu_lang": "Switch Language / 切换语言",
        "lang_switched": "Language switched to English",
        "lang_current": "Language",

        "setup_title": "Setup Wizard",
        "setup_desc": "Guides you through: check deps → config chain → setup wallet",
        "deploy_title": "Deploy Fee Contract",
        "deploy_desc": "Contract auto-deducts 0.2% fee from each trade to operator wallet",
        "deploy_fee_addr": "Fee address",
        "deploy_gas_warn": "Deploy wallet needs some ETH for gas",
        "create_title": "Create Trade Task",
        "create_desc": "Enter your trade plan, AI parses it automatically.",
        "create_examples": "Examples",
        "create_prompt": "Enter trade command",
        "create_empty": "Command cannot be empty",
        "monitor_title": "Start Monitor Engine",
        "monitor_desc": "Engine runs in background, auto-monitoring",
        "monitor_reach": "Time reached → start price monitoring",
        "monitor_trigger": "Price condition met → auto on-chain trade",
        "monitor_fee": "Trade success → auto-deduct 0.2% fee",
        "monitor_stop": "Press Ctrl+C to stop monitoring",
        "list_title": "My Tasks",
        "price_title": "Query Current Price",
        "price_prompt": "Trading pair (Enter for BTC/USDT)",
        "status_title": "System Status Check",
        "wallet_title": "Wallet Management",
        "wallet_show": "Show current wallet",
        "wallet_set": "Set new wallet",
        "wallet_load": "Load from environment",
        "wallet_back": "Back to main menu",
        "wallet_prompt": "Select (0-3)",
        "wallet_key_prompt": "Enter private key (0x...)",
        "wallet_key_empty": "Private key cannot be empty",

        "press_enter": "Press Enter to return to menu...",
        "exit_msg": "Thank you for using TradeTimer. Goodbye!",
        "invalid_choice": "Invalid choice, please try again",
        "exit_error": "Exited. Goodbye!",
        "launcher_error": "Launcher error",

        "dep_installing": "First run, installing dependencies...",
        "dep_installed": "Dependencies installed",
        "dep_not_found": "requirements.txt not found",
    },
}


class I18n:
    _instance = None
    _lang = "zh"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def lang(self) -> str:
        return self._lang

    def set_lang(self, lang: str) -> None:
        if lang in LANGUAGES:
            self._lang = lang

    def toggle(self) -> str:
        self._lang = "en" if self._lang == "zh" else "zh"
        return self._lang

    def t(self, key: str) -> str:
        return LANGUAGES.get(self._lang, LANGUAGES["en"]).get(key, key)


i18n = I18n()
