# TradeTimer

> Local-First On-Chain AI Trading Alarm · Create trades in plain language · Auto-execute when price hits target

Describe your trade plan in one sentence (e.g. "Buy 1000 USDT of BTC when it drops to 58000 in 6 hours"), and TradeTimer's local AI parses it, monitors the market, and auto-executes the on-chain trade when conditions are met.

## One-Line Install

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/WangQicheng-cmd/Trade-Timer/main/install.ps1 | iex
```

### Linux / macOS

```bash
curl -fsSL https://raw.githubusercontent.com/WangQicheng-cmd/Trade-Timer/main/install.sh | bash
```

### Manual (all platforms)

```bash
git clone https://github.com/WangQicheng-cmd/Trade-Timer.git
cd Trade-Timer
pip install -r requirements.txt
python launcher.py
```

## Quick Start

After installation, just 3 steps:

1. **Double-click `run.bat`** (Windows) or run `python launcher.py`
2. Select **`1. Setup`** (required first time — guides you through wallet setup and contract deployment)
3. Select **`3. Create Trade Task`** and enter your trade command

Then select **`4. Start Monitor`** — it auto-trades when the price hits your target.

## Command Examples

```
6 hours later BTC drops to 58000 spend 1000 USDT to buy
ETH rises to 4000 sell 2
1 day later SOL below 100 spend 500 USDT to buy
Monitor BTC break below 55000 immediately buy 0.5
```

## Requirements

- **Python 3.9+** — [Download](https://www.python.org/downloads/)
- **Ollama** — Local LLM runtime, [Download](https://ollama.ai/)
  - After install: `ollama pull deepseek-r1`
  - Start service: `ollama serve`

## Features

- **AI Natural Language** — Create trade tasks with one sentence
- **Fully Local** — App and LLM run on your machine, private key never uploaded
- **Delayed Monitoring** — Start monitoring hours/days later, not just immediately
- **Fee-on-Trade** — Free to use, 0.2% fee auto-deducted only on successful trades
- **Bilingual** — Switch between Chinese and English in the menu

## Menu

```
1. Setup (first time)
2. Deploy Fee Contract (once)
3. Create Trade Task
4. Start Monitor Engine
5. View My Tasks
6. Query Price
7. System Status
8. Wallet Management
9. Switch Language
0. Exit
```

## Documentation

Full architecture & code docs: [docs/CODE_WIKI.md](docs/CODE_WIKI.md)

## License

MIT
