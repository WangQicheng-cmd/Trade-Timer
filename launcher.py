#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradeTimer - 一键启动器
双击 run.bat 或运行 python launcher.py 即可使用
"""
import os
import sys
import subprocess
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

CONFIG_FILE = BASE_DIR / "config.json"
ENV_FILE = BASE_DIR / ".env"
LANG_FILE = BASE_DIR / ".lang"


def auto_install_deps():
    """首次运行自动检测并安装依赖"""
    try:
        import requests  # noqa
        import web3  # noqa
        return
    except ImportError:
        pass
    from src.core.i18n import i18n
    print(f"  [INFO] {i18n.t('dep_installing')}")
    req_file = BASE_DIR / "requirements.txt"
    if req_file.exists():
        subprocess.call(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
        )
        print(f"  [OK] {i18n.t('dep_installed')}\n")
    else:
        print(f"  [WARN] {i18n.t('dep_not_found')}")


def load_env():
    """从 .env 文件加载环境变量"""
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())


def load_lang():
    """加载上次选择的语言"""
    from src.core.i18n import i18n
    if LANG_FILE.exists():
        lang = LANG_FILE.read_text(encoding="utf-8").strip()
        if lang in ("zh", "en"):
            i18n.set_lang(lang)


def save_lang(lang: str):
    LANG_FILE.write_text(lang, encoding="utf-8")


auto_install_deps()
load_env()
load_lang()

from src.core.i18n import i18n


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input(f"\n  {i18n.t('press_enter')}")


def run_cmd(args, **kwargs):
    cmd = [sys.executable, str(BASE_DIR / "main.py")] + args
    subprocess.call(cmd, **kwargs)


def run_script(script_name):
    script = BASE_DIR / script_name
    if not script.exists():
        print(f"  {script_name} not found")
        return
    subprocess.call([sys.executable, str(script)])


def is_first_time():
    if not CONFIG_FILE.exists():
        return True
    if not ENV_FILE.exists():
        return True
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        if not cfg.get("web3", {}).get("fee_splitter_address"):
            return True
        if not os.environ.get("PRIVATE_KEY"):
            return True
    except Exception:
        return True
    return False


def show_banner():
    clear()
    print(r"""
╔══════════════════════════════════════════════════════╗
║                                                      ║
║    TradeTimer                                        ║
║    """ + i18n.t("app_tagline") + r"""                ║
║                                                      ║
║    """ + i18n.t("app_desc") + r"""                   ║
║    """ + i18n.t("app_fee") + r"""                    ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
""")


def show_main_menu():
    show_banner()

    first = is_first_time()
    if first:
        print(f"  ⚠ {i18n.t('first_run')}\n")
    else:
        try:
            from src.core.config import config
            splitter = config.get("web3.fee_splitter_address", "")
            if splitter:
                print(f"  {i18n.t('contract_deployed')}: {splitter[:12]}...{splitter[-6:]}")
            else:
                print(f"  {i18n.t('contract_not_deployed')}")
            print(f"  {i18n.t('fee_wallet')}: 0xB4b9...b6A6")
        except Exception:
            pass
        print()

    t = i18n.t
    print("  ┌─────────────────────────────────────────┐")
    print(f"  │  {t('menu_title'):<37}│")
    print("  ├─────────────────────────────────────────┤")
    print(f"  │  1. {t('menu_setup'):<37}│")
    print(f"  │  2. {t('menu_deploy'):<37}│")
    print(f"  │  3. {t('menu_create'):<37}│")
    print(f"  │  4. {t('menu_monitor'):<37}│")
    print(f"  │  5. {t('menu_list'):<37}│")
    print(f"  │  6. {t('menu_price'):<37}│")
    print(f"  │  7. {t('menu_status'):<37}│")
    print(f"  │  8. {t('menu_wallet'):<37}│")
    print(f"  │  9. {t('menu_lang'):<37}│")
    print(f"  │  0. {t('menu_exit'):<37}│")
    print("  └─────────────────────────────────────────┘")
    print()
    return input(f"  {t('menu_prompt')} (0-9): ").strip()


def action_setup():
    show_banner()
    t = i18n.t
    print(f"  【{t('setup_title')}】\n")
    print(f"  {t('setup_desc')}\n")
    run_script("setup.py")
    pause()


def action_deploy():
    show_banner()
    t = i18n.t
    print(f"  【{t('deploy_title')}】\n")
    print(f"  {t('deploy_desc')}")
    print(f"  {t('deploy_fee_addr')}: 0xB4b9a2DcdcCf91713E8bCE68BD436Fa8062Db6A6\n")
    print(f"  {t('deploy_gas_warn')}\n")
    run_script("deploy.py")
    pause()


def action_create():
    show_banner()
    t = i18n.t
    print(f"  【{t('create_title')}】\n")
    print(f"  {t('create_desc')}\n")
    if i18n.lang == "zh":
        print("  示例:")
        print("    · 6小时后 BTC 跌到 58000 买入")
        print("    · ETH 涨到 4000 卖出 2 个")
        print("    · 1天后 SOL 低于 100 花 500 USDT 买入")
        print("    · BTC 跌破 55000 买入 0.5 个\n")
    else:
        print("  Examples:")
        print("    · Buy BTC when it drops to 58000 in 6 hours")
        print("    · Sell 2 ETH when price reaches 4000")
        print("    · Spend 500 USDT on SOL when below 100, after 1 day\n")
    user_input = input(f"  {t('create_prompt')}: ").strip()
    if not user_input:
        print(f"  {t('create_empty')}")
        pause()
        return
    print()
    run_cmd(["create", user_input])
    pause()


def action_monitor():
    show_banner()
    t = i18n.t
    print(f"  【{t('monitor_title')}】\n")
    print(f"  {t('monitor_desc')}:")
    print(f"    · {t('monitor_reach')}")
    print(f"    · {t('monitor_trigger')}")
    print(f"    · {t('monitor_fee')}\n")
    print(f"  {t('monitor_stop')}\n")
    print("  " + "-" * 45)
    run_cmd(["monitor"])


def action_list():
    show_banner()
    t = i18n.t
    print(f"  【{t('list_title')}】\n")
    run_cmd(["list"])
    pause()


def action_price():
    show_banner()
    t = i18n.t
    print(f"  【{t('price_title')}】\n")
    symbol = input(f"  {t('price_prompt')}: ").strip()
    if not symbol:
        symbol = "BTC/USDT"
    print()
    run_cmd(["price", symbol])
    pause()


def action_status():
    show_banner()
    t = i18n.t
    print(f"  【{t('status_title')}】\n")
    run_cmd(["status"])
    pause()


def action_wallet():
    show_banner()
    t = i18n.t
    print(f"  【{t('wallet_title')}】\n")
    print(f"  1. {t('wallet_show')}")
    print(f"  2. {t('wallet_set')}")
    print(f"  3. {t('wallet_load')}")
    print(f"  0. {t('wallet_back')}\n")
    sub = input(f"  {t('wallet_prompt')}: ").strip()
    print()
    if sub == "1":
        run_cmd(["wallet", "show"])
    elif sub == "2":
        key = input(f"  {t('wallet_key_prompt')}: ").strip()
        if key:
            run_cmd(["wallet", "set", "--key", key])
        else:
            print(f"  {t('wallet_key_empty')}")
    elif sub == "3":
        run_cmd(["wallet", "load"])
    pause()


def action_lang():
    new_lang = i18n.toggle()
    save_lang(new_lang)
    show_banner()
    print(f"  ✅ {i18n.t('lang_switched')}")
    print(f"  {i18n.t('lang_current')}: {'中文' if new_lang == 'zh' else 'English'}\n")
    pause()


def main():
    while True:
        choice = show_main_menu()
        if choice == "1":
            action_setup()
        elif choice == "2":
            action_deploy()
        elif choice == "3":
            action_create()
        elif choice == "4":
            action_monitor()
        elif choice == "5":
            action_list()
        elif choice == "6":
            action_price()
        elif choice == "7":
            action_status()
        elif choice == "8":
            action_wallet()
        elif choice == "9":
            action_lang()
        elif choice == "0":
            print(f"\n  {i18n.t('exit_msg')}\n")
            break
        else:
            print(f"\n  {i18n.t('invalid_choice')}")
            pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {i18n.t('exit_error')}\n")
    except Exception as e:
        print(f"\n  {i18n.t('launcher_error')}: {e}")
        input("  Press Enter to exit...")
