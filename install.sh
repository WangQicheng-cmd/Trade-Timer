#!/usr/bin/env bash
# AI Trade Alarm - Linux/macOS 一键安装脚本
# 用法：
#   curl -fsSL https://raw.githubusercontent.com/<用户名>/ai-trade-alarm/main/install.sh | bash

set -e

APP_NAME="TradeTimer"
INSTALL_DIR="$HOME/$APP_NAME"
REPO_URL="https://github.com/WangQicheng-cmd/Trade-Timer.git"

echo ""
echo "======================================"
echo "  TradeTimer - Installer"
echo "======================================"
echo ""

# 检查 git
if ! command -v git &> /dev/null; then
    echo "[ERROR] Git not found. Please install Git first:"
    echo "  Ubuntu/Debian: sudo apt install git"
    echo "  macOS: brew install git"
    exit 1
fi
echo "[OK] Git found"

# 检查 python
PYTHON=""
if command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
else
    echo "[ERROR] Python not found. Please install Python 3.9+ first:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  macOS: brew install python"
    exit 1
fi
echo "[OK] Python found ($PYTHON)"

# 克隆或更新
if [ -d "$INSTALL_DIR" ]; then
    echo "[INFO] Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull
else
    echo "[INFO] Cloning repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# 安装依赖
echo "[INFO] Installing dependencies..."
$PYTHON -m pip install -r requirements.txt
echo "[OK] Dependencies installed"

# 创建启动别名
LAUNCHER="$HOME/.local/bin/tradetimer"
mkdir -p "$(dirname "$LAUNCHER")"
cat > "$LAUNCHER" << EOF
#!/usr/bin/env bash
cd "$INSTALL_DIR"
$PYTHON launcher.py
EOF
chmod +x "$LAUNCHER"

echo ""
echo "======================================"
echo "  Installation Complete!"
echo "======================================"
echo ""
echo "  Next steps:" | sed 's/^/  /'
echo "    1. Install Ollama: https://ollama.ai/"
echo "    2. Run: ollama pull deepseek-r1"
echo "    3. Run: ollama serve"
echo "    4. Start: ai-trade-alarm"
echo "       Or: cd $INSTALL_DIR && $PYTHON launcher.py"
echo ""
echo "  First time? Select option 1 in the menu to configure."
echo ""

echo "Starting TradeTimer now..."
$PYTHON launcher.py
