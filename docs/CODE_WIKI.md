# AI Trade Alarm - Code Wiki

> 本地运行式链上 AI 捡漏闹钟（自动条件交易机器人）

---

## 目录

1. [项目概述](#1-项目概述)
2. [整体架构](#2-整体架构)
3. [目录结构](#3-目录结构)
4. [核心模块详解](#4-核心模块详解)
   - 4.1 [core 核心层](#41-core-核心层)
   - 4.2 [ai 自然语言解析层](#42-ai-自然语言解析层)
   - 4.3 [market 行情层](#43-market-行情层)
   - 4.4 [scheduler 调度层](#44-scheduler-调度层)
   - 4.5 [web3 链上交易层](#45-web3-链上交易层)
5. [数据库设计](#5-数据库设计)
6. [智能合约说明](#6-智能合约说明)
7. [配置说明](#7-配置说明)
8. [运行方式](#8-运行方式)
9. [依赖关系](#9-依赖关系)
10. [扩展指南](#10-扩展指南)

---

## 1. 项目概述

### 1.1 项目简介

**AI Trade Alarm** 是一套完全本地运行的链上条件交易机器人。用户通过自然语言（大白话）输入交易计划，本地 AI（Ollama + deepseek-r1）自动解析并创建定时监控任务，到达设定条件后自动触发链上兑换交易。

### 1.2 核心特性

- ✅ **AI 自然语言创建** - 不用手动填复杂参数，一句话创建交易闹钟
- ✅ **纯本地运行** - 全部程序、大模型运行在用户自己电脑，不上传私钥、资金
- ✅ **延时定时监控** - 支持等待几小时/几天后再开始盯盘（市面普通条件单大多只能立刻监控）
- ✅ **成交抽成模式** - 用户免费使用，成交才扣 0.2% 手续费

### 1.3 盈利模式

每一笔成功链上成交，智能合约自动抽取 **0.2%** 手续费打入运营方加密钱包。

### 1.4 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| 编程语言 | Python 3.9+ | 主程序逻辑 |
| 本地大模型 | Ollama + deepseek-r1 | 自然语言指令解析 |
| 数据库 | SQLite | 任务存储、价格历史 |
| 行情源 | Binance / CoinGecko API | 加密货币价格 |
| 链上交互 | Web3.py | 以太坊/ EVM 链交易 |
| 智能合约 | Solidity ^0.8.20 | 手续费自动分账 |
| IDE | VS Code | 开发运行环境 |

---

## 2. 整体架构

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户 CLI 交互层                       │
│                       (main.py / app.py)                     │
└────────────────┬────────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┬──────────────┐
    ▼            ▼            ▼              ▼
┌─────────┐ ┌────────┐ ┌───────────┐ ┌──────────┐
│  AI 解析 │ │ 行情   │ │ 调度引擎   │ │ 链上交易  │
│  模块   │ │ 模块   │ │           │ │  模块    │
│ (ai/)   │ │(market)│ │(scheduler)│ │  (web3)  │
└────┬────┘ └───┬────┘ └─────┬─────┘ └─────┬────┘
     │          │            │             │
     └──────────┴──────┬─────┴─────────────┘
                       ▼
                ┌──────────────┐
                │   core 核心   │
                │ 配置/数据库/  │
                │ 日志/模型定义  │
                └───────┬──────┘
                        │
                    ┌───┴───┐
                    │ SQLite │
                    │  数据库 │
                    └───────┘

┌──────────────────────────────────────────────────────┐
│                    区块链层 (EVM)                      │
│  FeeSplitter 合约 ── 0.2% 手续费自动转运营钱包        │
│  Uniswap V2 Router ── DEX 兑换执行                    │
│  ERC20 Tokens ── USDT/USDC/WETH 等                   │
└──────────────────────────────────────────────────────┘
```

### 2.2 业务工作流

```
用户输入自然语言指令
        │
        ▼
  AI 解析模块 (Ollama/deepseek-r1)
        │
        ├─→ 币种、方向、触发价、数量、延迟
        │
        ▼
  写入 SQLite 任务表 (status: waiting/pending)
        │
        ▼
  调度引擎后台轮询
        │
        ├─→ 等待 delay_seconds → 转为 monitoring
        │
        ▼
  持续轮询行情价格
        │
        ├─→ 价格满足触发条件 → 转为 triggered
        │
        ▼
  调用 Web3 模块执行链上兑换
        │
        ├─→ 授权 → 兑换 → 合约扣 0.2% 手续费
        │
        ▼
  任务标记为 executed，记录 tx_hash
```

### 2.3 任务状态机

```
   pending
      │
      ▼
   waiting ←──(有延迟时间，等待开始)
      │
      ▼
  monitoring ←──(监控行情中)
      │
      ├─→ 触发 → triggered → executed
      │           │
      │           └─→ 失败 → failed
      │
      └─→ 用户取消 → cancelled
```

| 状态 | 说明 |
|------|------|
| `pending` | 任务刚创建，等待进入等待队列 |
| `waiting` | 有延迟，等待到达 start_time |
| `monitoring` | 正在监控行情价格 |
| `triggered` | 价格条件已触发，准备执行 |
| `executed` | 链上交易执行成功 |
| `failed` | 执行失败 |
| `cancelled` | 用户手动取消 |

---

## 3. 目录结构

```
ai-trade-alarm/
├── main.py                  # CLI 主入口
├── deploy.py                # 合约一键部署脚本（编译+部署+回写配置）
├── setup.py                 # 首次配置向导（交互式引导）
├── install.bat              # 一键安装依赖（Windows 双击）
├── setup.bat                # 一键配置（Windows 双击）
├── deploy.bat               # 一键部署合约（Windows 双击）
├── start.bat                # 一键启动监控（Windows 双击）
├── create.bat               # 一键创建任务（Windows 双击）
├── requirements.txt         # Python 依赖
├── config.json              # 配置文件（含收款钱包地址，自动生成）
├── config.example.json      # 配置模板
├── .env                     # 环境变量（含私钥，setup.py 自动生成）
├── .env.example             # 环境变量模板
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── app.py               # 应用主类 TradeAlarmApp
│   ├── core/                # 核心基础模块
│   │   ├── __init__.py
│   │   ├── config.py        # 配置管理 Config 单例
│   │   ├── database.py      # SQLite 数据库操作 Database 单例
│   │   ├── logger.py        # 日志配置
│   │   └── models.py        # 数据模型/枚举定义
│   ├── ai/                  # AI 自然语言解析
│   │   ├── __init__.py
│   │   └── parser.py        # OllamaClient + TradeCommandParser
│   ├── market/              # 行情数据
│   │   ├── __init__.py
│   │   └── provider.py      # Binance/CoinGecko 行情提供者
│   ├── scheduler/           # 任务调度与监控
│   │   ├── __init__.py
│   │   └── monitor.py       # TaskMonitor 监控引擎
│   └── web3/                # 链上交易
│       ├── __init__.py
│       └── service.py       # WalletManager + Web3Service + 手续费扣除
├── contracts/               # 智能合约
│   └── FeeSplitter.sol      # 手续费分账合约（0.2% 自动抽成，硬编码收款地址）
├── data/                    # 运行时数据（自动生成）
│   ├── tasks.db             # SQLite 数据库
│   └── logs/                # 日志文件
└── docs/                    # 文档目录
    └── CODE_WIKI.md         # 本文档
```

---

## 4. 核心模块详解

### 4.1 core 核心层

#### 4.1.1 config.py - 配置管理

**文件**：[src/core/config.py](file:///C:/Users/Thunderobot/AppData/Roaming/TRAE%20SOLO%20CN/ModularData/ai-agent/work-mode-projects/6a65eef83a2af248b4f73f8e/src/core/config.py)

**类**：`Config`（单例模式）

**职责**：
- 管理全局配置，支持 JSON 文件持久化
- 提供深度合并（默认配置 + 用户配置）
- 支持点号路径访问（如 `config.get("ollama.model")`）

**核心方法**：

| 方法 | 说明 |
|------|------|
| `get(key, default)` | 获取配置值，支持点号路径 |
| `set(key, value)` | 设置配置值并保存到文件 |
| `save()` | 保存当前配置到 `config.json` |

**默认配置结构**：
```python
{
    "ollama": {       # Ollama 服务配置
        "base_url": "http://localhost:11434",
        "model": "deepseek-r1",
        "timeout": 120,
    },
    "market": {       # 行情配置
        "provider": "binance",
        "poll_interval_seconds": 10,
        "base_url": "https://api.binance.com",
    },
    "web3": {         # 链上配置
        "chain_id": 1,
        "rpc_url": "https://eth.llamarpc.com",
        "fee_wallet_address": "",
        "fee_percent": 0.002,
        "slippage_tolerance": 0.005,
        "dex_router_address": "",
    },
    "database": {     # 数据库配置
        "path": "./data/tasks.db",
    },
    "scheduler": {    # 调度配置
        "check_interval_seconds": 5,
    },
}
```

---

#### 4.1.2 database.py - 数据库层

**文件**：[src/core/database.py](file:///C:/Users/Thunderobot/AppData/Roaming/TRAE%20SOLO%20CN/ModularData/ai-agent/work-mode-projects/6a65eef83a2af248b4f73f8e/src/core/database.py)

**类**：`Database`（单例模式）

**职责**：
- SQLite 数据库连接与管理
- 任务 CRUD 操作
- 价格历史存储

**核心方法**：

| 方法 | 说明 |
|------|------|
| `create_task(task_data)` | 创建新任务，返回任务 ID |
| `get_task(task_id)` | 获取单个任务详情 |
| `list_tasks(status, limit)` | 列出任务，可按状态筛选 |
| `update_task_status(task_id, status, **kwargs)` | 更新任务状态及附加字段 |
| `get_pending_tasks_to_start(current_time)` | 获取到达启动时间的待启动任务 |
| `get_monitoring_tasks()` | 获取所有监控中的任务 |
| `save_price(symbol, price)` | 保存价格快照到历史表 |
| `get_recent_prices(symbol, limit)` | 获取最近价格历史 |

---

#### 4.1.3 logger.py - 日志模块

**文件**：[src/core/logger.py](file:///C:/Users/Thunderobot/AppData/Roaming/TRAE%20SOLO%20CN/ModularData/ai-agent/work-mode-projects/6a65eef83a2af248b4f73f8e/src/core/logger.py)

**函数**：`setup_logger()`

**职责**：
- 配置控制台 + 文件双通道日志
- 日志文件按日期命名，存放于 `data/logs/`
- 默认 logger 实例：`logger`

---

#### 4.1.4 models.py - 数据模型

**文件**：[src/core/models.py](file:///C:/Users/Thunderobot/AppData/Roaming/TRAE%20SOLO%20CN/ModularData/ai-agent/work-mode-projects/6a65eef83a2af248b4f73f8e/src/core/models.py)

**枚举类**：

| 枚举 | 值 | 说明 |
|------|-----|------|
| `TaskStatus` | pending/waiting/monitoring/triggered/executed/failed/cancelled | 任务状态 |
| `TaskSide` | buy/sell | 买卖方向 |
| `TriggerDirection` | above/below | 触发方向（高于/低于） |
| `AmountType` | quote/base | 数量类型（计价币/标的币） |

**数据类**：

- **`ParsedTradeCommand`** - AI 解析后的结构化交易指令
  - 字段：`symbol`, `side`, `trigger_price`, `trigger_direction`, `amount`, `amount_type`, `delay_seconds`, `raw_input`, `extra`
  - 方法：`to_task_dict(user_input)` → 转换为数据库可写入的字典

- **`PriceTick`** - 价格快照
  - 字段：`symbol`, `price`, `timestamp`
  - 方法：`check_trigger(trigger_price, direction)` → 判断是否满足触发条件

---

### 4.2 ai 自然语言解析层

**文件**：[src/ai/parser.py](file:///C:/Users/Thunderobot/AppData/Roaming/TRAE%20SOLO%20CN/ModularData/ai-agent/work-mode-projects/6a65eef83a2af248b4f73f8e/src/ai/parser.py)

#### 4.2.1 OllamaClient 类

**职责**：封装 Ollama HTTP API 调用

**核心方法**：

| 方法 | 说明 |
|------|------|
| `is_available()` | 检测 Ollama 服务是否可用 |
| `generate(prompt, system)` | 调用生成补全接口 |
| `chat(messages)` | 调用对话接口 |

**API 端点**：
- 健康检查：`GET /api/tags`
- 生成：`POST /api/generate`（stream=False）

---

#### 4.2.2 TradeCommandParser 类

**职责**：将用户自然语言指令解析为结构化交易参数

**解析流程**：

```
用户输入
   │
   ├─→ 优先走 Ollama AI 解析（deepseek-r1）
   │       │
   │       ├─→ 构建 SYSTEM_PROMPT + 用户输入
   │       ├─→ 调用 Ollama API
   │       ├─→ 提取 JSON 响应
   │       └─→ 构建 ParsedTradeCommand
   │
   └─→ AI 不可用时 fallback 到规则解析
           │
           └─→ 正则匹配提取：币种、价格、方向、数量、延迟
```

**系统提示词关键设计**：
- 强制输出纯 JSON，禁止 markdown/解释
- 明确定义字段含义和取值范围
- 内置时间单位换算规则
- 内置方向判断规则（逢低买/逢高卖默认值）

**规则解析（fallback）关键函数**：

| 函数 | 说明 |
|------|------|
| `_extract_symbol(text)` | 提取币种对（支持 BTC/ETH/SOL 等常见币种） |
| `_extract_price(text)` | 提取触发价格 |
| `_extract_direction(text, side, price)` | 判断触发方向（高于/低于） |
| `_extract_amount(text)` | 提取交易数量 |
| `_extract_amount_type(text)` | 判断数量类型（按标的币/计价币） |
| `_extract_delay(text)` | 提取延迟时间（时/分/天/秒） |

---

### 4.3 market 行情层

**文件**：[src/market/provider.py](file:///C:/Users/Thunderobot/AppData/Roaming/TRAE%20SOLO%20CN/ModularData/ai-agent/work-mode-projects/6a65eef83a2af248b4f73f8e/src/market/provider.py)

#### 4.3.1 抽象基类 MarketProvider

定义统一接口：
- `get_price(symbol) -> PriceTick`
- `normalize_symbol(symbol)` - 标准化交易对格式

---

#### 4.3.2 BinanceProvider（币安行情）

- 数据源：Binance Spot API
- 接口：`GET /api/v3/ticker/price`
- 交易对格式：`BTCUSDT`（自动从 `BTC/USDT` 转换）

---

#### 4.3.3 CoinGeckoProvider

- 数据源：CoinGecko API
- 接口：`GET /simple/price`
- 内置常用币种映射表（BTC → bitcoin 等）

---

#### 4.3.4 MarketService 类（单例）

**职责**：行情服务统一入口，带缓存

**特性**：
- 配置驱动切换行情源（`market.provider`）
- 内置 TTL 缓存（默认 10 秒），减少 API 调用
- 每次拉取自动写入价格历史表

**核心方法**：
- `get_price(symbol, use_cache=True)` - 获取当前价格
- `get_current_price_str(symbol)` - 格式化价格字符串

---

### 4.4 scheduler 调度层

**文件**：[src/scheduler/monitor.py](file:///C:/Users/Thunderobot/AppData/Roaming/TRAE%20SOLO%20CN/ModularData/ai-agent/work-mode-projects/6a65eef83a2af248b4f73f8e/src/scheduler/monitor.py)

#### 4.4.1 TaskMonitor 类

**职责**：后台任务调度与监控引擎

**核心机制**：
- 后台线程轮询模式（默认 5 秒一次）
- 双阶段检查：激活等待任务 + 检查监控中任务
- 回调机制：触发时调用所有注册的回调函数

**核心方法**：

| 方法 | 说明 |
|------|------|
| `start()` | 启动监控线程 |
| `stop()` | 停止监控线程 |
| `on_trigger(callback)` | 注册触发回调 |
| `_tick()` | 单次检查循环（内部） |

**每次 tick 的流程**：

```
tick()
  │
  ├─→ _activate_waiting_tasks()
  │     │
  │     └─→ 查询 start_time <= now 的 waiting 任务
  │          → 全部转为 monitoring
  │
  └─→ _check_monitoring_tasks()
        │
        ├─→ 汇总所有监控中的交易对，批量拉取价格
        ├─→ 逐个检查触发条件
        └─→ 满足条件 → 触发回调 → 状态转 triggered
```

**设计亮点**：
- 批量拉取价格（按 symbol 去重），避免重复 API 调用
- 异常隔离：单个任务失败不影响整体调度
- 回调解耦：调度器只管触发，交易执行由回调处理

---

### 4.5 web3 链上交易层

**文件**：[src/web3/service.py](file:///C:/Users/Thunderobot/AppData/Roaming/TRAE%20SOLO%20CN/ModularData/ai-agent/work-mode-projects/6a65eef83a2af248b4f73f8e/src/web3/service.py)

#### 4.5.1 WalletManager 类（单例）

**职责**：钱包私钥管理

**核心方法**：

| 方法 | 说明 |
|------|------|
| `load_from_env()` | 从 `PRIVATE_KEY` 环境变量加载钱包 |
| `set_wallet(private_key, address)` | 手动设置私钥 |
| `is_ready()` | 钱包是否已配置 |

**安全设计**：
- 私钥仅存内存，不落盘
- 支持环境变量注入，避免硬编码
- 地址从私钥派生验证

---

#### 4.5.2 Web3Service 类（单例）

**职责**：链上交易执行

**核心能力**：
- 链连接检测
- ERC20 余额查询
- Uniswap V2 风格 DEX 兑换
- 滑点保护
- 模拟报价（getAmountsOut）

**核心方法**：

| 方法 | 说明 |
|------|------|
| `is_available()` | Web3 连接是否可用 |
| `get_balance(address, token_address)` | 查询代币/ETH 余额 |
| `simulate_swap(amount_in, token_in, token_out)` | 模拟兑换，估算输出量 |
| `execute_trade(symbol, side, amount, amount_type, price)` | 执行交易 + 扣手续费，返回 tx_hash/fee |
| `_collect_fee(fee_token, fee_amount, ...)` | 调用 FeeSplitter 合约扣除 0.2% 手续费 |
| `_transfer_fee_direct(fee_token, fee_amount)` | 降级方案：直接 ERC20 转账到运营钱包 |
| `_swap_tokens(token_in, token_out, amount_in, side)` | 执行 DEX 兑换 |

**交易执行流程**（含手续费扣除）：

```
execute_trade()
  │
  ├─→ 校验钱包、Web3 连接
  ├─→ 计算手续费（amount * 0.2%）
  ├─→ 解析交易对、确定输入输出代币
  │
  ├─→ _swap_tokens()  ← 全额执行兑换（不扣手续费）
  │     │
  │     ├─→ 检查/执行 ERC20 授权（approve）
  │     ├─→ 查询输出量、计算滑点保护
  │     ├─→ 构建 swapExactTokensForTokens
  │     └─→ 签名并发送交易 → tx_hash
  │
  └─→ _collect_fee()  ← 交易成功后扣手续费
        │
        ├─→ 已配置 FeeSplitter 合约？
        │     ├─ 是 → 授权合约 → 调用 splitFee() → 手续费进合约
        │     └─→ 否 → _transfer_fee_direct() → 直接转运营钱包
        │
        └─→ 返回 fee_tx_hash
```

**内置 ABI**：
- `UNISWAP_V2_ROUTER_ABI` - Uniswap V2 路由合约 ABI
- `ERC20_ABI` - ERC20 标准接口 ABI
- `FEE_SPLITTER_ABI` - 手续费分账合约 ABI

**内置代币地址表**：
- Ethereum 主网：WETH, USDT, USDC, DAI, WBTC, UNI, LINK
- Arbitrum：WETH, USDT, USDC, ARB
- BSC：WBNB, USDT, USDC, BUSD

---

### 4.6 app.py - 应用主类

**文件**：[src/app.py](file:///C:/Users/Thunderobot/AppData/Roaming/TRAE%20SOLO%20CN/ModularData/ai-agent/work-mode-projects/6a65eef83a2af248b4f73f8e/src/app.py)

#### TradeAlarmApp 类

**职责**：协调整个应用的业务逻辑，连接各模块

**核心方法**：

| 方法 | 说明 |
|------|------|
| `create_task(user_input)` | 创建交易任务（AI 解析 + 入库） |
| `list_tasks(status, limit)` | 列出任务并格式化输出 |
| `show_task(task_id)` | 显示任务详情 |
| `cancel_task(task_id)` | 取消任务 |
| `get_price(symbol)` | 查询价格 |
| `start_monitor()` | 启动监控引擎（阻塞运行） |
| `check_status()` | 检查系统各组件状态 |
| `_on_task_triggered(task, tick)` | 触发回调 → 调用 Web3 执行交易 |

---

## 5. 数据库设计

**数据库**：SQLite（文件：`data/tasks.db`）

### 5.1 tasks 表 - 任务表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | 任务 ID（自增） |
| `user_input` | TEXT | 用户原始输入 |
| `symbol` | TEXT | 交易对（如 BTC/USDT） |
| `side` | TEXT | 方向：buy/sell |
| `trigger_price` | REAL | 触发价格 |
| `trigger_direction` | TEXT | 触发方向：above/below |
| `amount` | REAL | 交易数量 |
| `amount_type` | TEXT | 数量类型：quote/base |
| `delay_seconds` | INTEGER | 延迟秒数 |
| `start_time` | TEXT | 开始监控时间（ISO 格式） |
| `trigger_time` | TEXT | 实际触发时间 |
| `status` | TEXT | 任务状态（见状态机） |
| `created_at` | TEXT | 创建时间 |
| `updated_at` | TEXT | 更新时间 |
| `error_message` | TEXT | 错误信息 |
| `tx_hash` | TEXT | 链上交易哈希 |
| `fee_amount` | REAL | 手续费金额 |
| `params_json` | TEXT | 扩展参数（JSON 字符串） |

**索引**：
- `idx_tasks_status` - 按状态查询优化
- `idx_tasks_start_time` - 按启动时间查询优化

---

### 5.2 price_history 表 - 价格历史

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | 自增 ID |
| `symbol` | TEXT | 交易对 |
| `price` | REAL | 价格 |
| `timestamp` | TEXT | 时间戳（ISO 格式） |

**索引**：
- `idx_price_history_symbol_time` - 按交易对+时间查询优化

---

## 6. 智能合约说明

**文件**：[contracts/FeeSplitter.sol](file:///C:/Users/Thunderobot/AppData/Roaming/TRAE%20SOLO%20CN/ModularData/ai-agent/work-mode-projects/6a65eef83a2af248b4f73f8e/contracts/FeeSplitter.sol)

### 6.1 FeeSplitter 合约

**Solidity 版本**：^0.8.20

**功能**：自动抽取 0.2% 手续费并转入运营钱包

**收款钱包地址（硬编码）**：`0xB4b9a2DcdcCf91713E8bCE68BD436Fa8062Db6A6`

> 合约部署后收款地址不可更改，0.2% 手续费将自动转入此地址。

**常量**：

| 常量 | 值 | 说明 |
|------|-----|------|
| `FEE_WALLET` | `0xB4b9...b6A6` | 运营方收款钱包地址（硬编码 constant） |
| `FEE_PERCENT` | 20 | 手续费分子（0.2% = 20/10000） |
| `FEE_DENOMINATOR` | 10000 | 手续费分母 |

**构造函数**：无参数，内部直接将 `feeWallet` 设为硬编码的 `FEE_WALLET`。

**核心方法**：

| 方法 | 说明 |
|------|------|
| `splitFee(token, totalAmount)` | ERC20 代币手续费拆分：从调用者 transferFrom 0.2% 到合约 |
| `splitFeeNative()` | ETH 原生币手续费拆分（payable），扣 0.2% 退回剩余 |
| `withdrawFees(token)` | 提取合约中累积的手续费到 feeWallet（任何人可调用） |
| `getFeeAmount(totalAmount)` | 只读：计算手续费金额 |
| `getUserAmountAfterFee(totalAmount)` | 只读：计算扣手续费后金额 |
| `feeWallet()` | 只读：返回收款钱包地址 |

**事件**：
- `FeeCollected` - 手续费收取事件
- `FeesWithdrawn` - 手续费提取事件

**手续费扣除流程**（用户交易触发时）：
1. 用户链上交易成功后，Python 调用 `splitFee(token, amount)`
2. 合约从用户钱包 `transferFrom` 0.2% 手续费到合约地址
3. 累积的手续费可通过 `withdrawFees()` 提取到运营钱包
4. 若未配置合约地址，自动降级为直接 ERC20 转账到运营钱包

**部署方式**：

方式一：一键部署脚本（推荐）
```bash
python deploy.py
# 或双击 deploy.bat
```
脚本自动完成：编译合约 → 部署到公链 → 验证收款地址 → 回写合约地址到 config.json

方式二：Remix IDE 手动部署
1. 打开 https://remix.ethereum.org
2. 创建 FeeSplitter.sol，粘贴合约代码
3. 编译（Solidity 0.8.20）
4. 构造函数无参数，直接部署
5. 复制合约地址，填入 config.json 的 `web3.fee_splitter_address`

---

## 7. 配置说明

### 7.1 config.json 配置项

从 [config.example.json](file:///C:/Users/Thunderobot/AppData/Roaming/TRAE%20SOLO%20CN/ModularData/ai-agent/work-mode-projects/6a65eef83a2af248b4f73f8e/config.example.json) 复制为 `config.json` 后修改：

| 配置路径 | 说明 | 默认值 |
|----------|------|--------|
| `ollama.base_url` | Ollama 服务地址 | `http://localhost:11434` |
| `ollama.model` | 使用的模型名 | `deepseek-r1` |
| `ollama.timeout` | API 超时秒数 | `120` |
| `market.provider` | 行情源：`binance` / `coingecko` | `binance` |
| `market.poll_interval_seconds` | 价格缓存 TTL | `10` |
| `market.base_url` | 行情 API 地址 | 币安主网 |
| `web3.chain_id` | 链 ID | `1`（以太坊） |
| `web3.rpc_url` | RPC 节点地址 | `https://eth.llamarpc.com` |
| `web3.fee_wallet_address` | 运营方收款钱包地址 | `0xB4b9a2DcdcCf91713E8bCE68BD436Fa8062Db6A6` |
| `web3.fee_splitter_address` | FeeSplitter 合约地址（部署后自动填入） | 空（部署后填入） |
| `web3.fee_percent` | 手续费比例 | `0.002`（0.2%） |
| `web3.slippage_tolerance` | 滑点容忍 | `0.005`（0.5%） |
| `web3.dex_router_address` | DEX Router 合约地址 | `0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D`（Uniswap V2） |
| `database.path` | 数据库文件路径 | `./data/tasks.db` |
| `scheduler.check_interval_seconds` | 调度检查间隔 | `5` |

### 7.2 环境变量

从 [.env.example](file:///C:/Users/Thunderobot/AppData/Roaming/TRAE%20SOLO%20CN/ModularData/ai-agent/work-mode-projects/6a65eef83a2af248b4f73f8e/.env.example) 复制为 `.env`：

| 变量 | 说明 |
|------|------|
| `PRIVATE_KEY` | 用户钱包私钥（仅本地使用，不上传） |

---

## 8. 运行方式

### 8.1 一键快速开始（Windows 用户）

**最简单的方式：双击运行批处理文件**

| 文件 | 功能 |
|------|------|
| `install.bat` | 安装 Python 依赖 |
| `setup.bat` | 首次配置向导（引导设置 RPC、钱包、部署合约） |
| `deploy.bat` | 部署 FeeSplitter 合约到公链 |
| `create.bat` | 创建交易任务 |
| `start.bat` | 启动监控引擎（持续运行） |

**首次使用流程**：
```
1. 双击 install.bat  → 安装依赖
2. 双击 setup.bat    → 配置向导（含合约部署）
3. 双击 create.bat   → 创建交易任务
4. 双击 start.bat    → 启动监控
```

### 8.2 命令行方式

**1. 安装 Ollama + deepseek-r1**
```bash
# 下载安装 Ollama: https://ollama.ai/
ollama pull deepseek-r1
ollama serve   # 启动服务
```

**2. 安装 Python 依赖**
```bash
pip install -r requirements.txt
```

**3. 首次配置（交互式向导）**
```bash
python setup.py
# 向导自动完成：检查依赖 → 检查 Ollama → 配置链 → 配置钱包 → 部署合约
```

**4. 部署手续费合约**
```bash
python deploy.py
# 自动编译合约 → 部署到公链 → 验证 → 回写 config.json
# 部署后 0.2% 手续费将自动转入 0xB4b9a2DcdcCf91713E8bCE68BD436Fa8062Db6A6
```

### 8.3 常用命令

```bash
# 首次配置向导
python main.py setup

# 部署合约
python main.py deploy

# 查看系统状态
python main.py status

# 创建交易任务（推荐交互输入）
python main.py create
# 或直接传参
python main.py create "6小时后 BTC 跌到 58000 美元自动买入"

# 查看任务列表
python main.py list
python main.py list --status monitoring

# 查看任务详情
python main.py show 1

# 取消任务
python main.py cancel 1

# 查询当前价格
python main.py price BTC/USDT

# 钱包管理
python main.py wallet set --key 你的私钥
python main.py wallet show

# 启动监控引擎（持续运行）
python main.py monitor
```

### 8.4 完整运行流程

```bash
# 1. 启动 Ollama
ollama serve

# 2. 首次配置（另开终端）
python setup.py

# 3. 部署合约（只需一次）
python deploy.py

# 4. 检查系统状态
python main.py status

# 5. 创建交易任务
python main.py create
# 输入：6小时后 BTC 跌到 58000 美元花 1000 USDT 买入

# 6. 启动监控引擎
python main.py monitor
```

---

## 9. 依赖关系

### 9.1 Python 依赖

见 [requirements.txt](file:///C:/Users/Thunderobot/AppData/Roaming/TRAE%20SOLO%20CN/ModularData/ai-agent/work-mode-projects/6a65eef83a2af248b4f73f8e/requirements.txt)：

| 包 | 版本要求 | 用途 |
|----|---------|------|
| `requests` | >= 2.31.0 | HTTP 请求（Ollama/行情 API） |
| `web3` | >= 6.10.0 | 以太坊链上交互 |
| `py-solc-x` | >= 2.0.3 | Solidity 合约编译（部署用） |

### 9.2 模块依赖图

```
main.py ──→ setup.py / deploy.py（独立脚本）
  └─→ src/app.py
        ├─→ src/core/config.py
        ├─→ src/core/database.py
        ├─→ src/core/logger.py
        ├─→ src/core/models.py
        ├─→ src/ai/parser.py
        │     └─→ src/core/*
        ├─→ src/market/provider.py
        │     └─→ src/core/*
        ├─→ src/scheduler/monitor.py
        │     └─→ src/core/*
        │     └─→ src/market/provider.py
        └─→ src/web3/service.py
              └─→ src/core/*
              └─→ FeeSplitter 合约（链上手续费扣除）
```

**依赖原则**：
- 所有模块依赖 core 层（配置/数据库/模型）
- 上层模块依赖下层，不反向依赖
- scheduler 依赖 market（拉取价格）
- app.py 作为编排层，依赖所有模块

---

## 10. 扩展指南

### 10.1 添加新的行情源

1. 在 `src/market/provider.py` 中继承 `MarketProvider` 抽象类
2. 实现 `get_price(symbol)` 方法
3. 在 `MarketService._init()` 中添加 provider 判断分支
4. 在 `config.json` 的 `market.provider` 中配置新名称

### 10.2 添加新的 DEX 支持

1. 在 `src/web3/service.py` 中新增 DEX ABI 常量
2. 实现对应 `_swap_xxx` 私有方法
3. 在 `execute_trade` 中根据配置选择 DEX

### 10.3 自定义 AI 提示词

编辑 `src/ai/parser.py` 中的 `SYSTEM_PROMPT` 常量：
- 增加更多字段（如止损、止盈）
- 支持更复杂的指令格式
- 调整输出 JSON 结构
- 同步修改 `_build_parsed_command` 和 `ParsedTradeCommand`

### 10.4 支持更多任务类型

在 `src/core/models.py` 中扩展：
- 新增 `TaskType` 枚举（普通条件单/定投/网格等）
- 扩展 `ParsedTradeCommand` 字段
- 在 `TaskMonitor._check_monitoring_tasks` 中增加对应触发逻辑

### 10.5 更换数据库

当前使用 SQLite（零配置，适合本地）。如需更换：
1. 抽象 `Database` 类的接口（参考 Repository 模式）
2. 新建 PostgreSQL/MySQL 等实现类
3. 修改 `config.py` 和工厂方法

---

*文档生成时间：2026-07-26*
*项目版本：v1.0.0*
