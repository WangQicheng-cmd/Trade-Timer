# 发布到 GitHub 让别人一键安装

## 第 1 步：注册 GitHub 账号

如果还没有，去 https://github.com/signup 注册一个免费账号。

## 第 2 步：安装 Git

下载安装 Git：https://git-scm.com/download/win

## 第 3 步：创建仓库

1. 登录 GitHub，点击右上角 **+** → **New repository**
2. 仓库名填：`ai-trade-alarm`
3. 选择 **Public**（公开，别人才能克隆）
4. 勾选 **Add a README file**
5. 点击 **Create repository**

## 第 4 步：上传代码

在本项目文件夹打开终端（或 PowerShell），依次执行：

```bash
# 初始化 git 仓库
git init

# 关联你的远程仓库（替换 YOUR_USERNAME 为你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/ai-trade-alarm.git

# 添加所有文件（.gitignore 会自动排除私钥、数据库等敏感文件）
git add .

# 提交
git commit -m "Initial release: AI Trade Alarm"

# 推送到 GitHub
git branch -M main
git push -u origin main
```

> 首次推送时会要求登录 GitHub，按提示输入用户名和 Personal Access Token（在 GitHub Settings → Developer settings → Personal access tokens 生成）。

## 第 5 步：替换脚本中的用户名

上传后，把以下文件中的 `<你的用户名>` 或 `YOUR_USERNAME` 替换为你的真实 GitHub 用户名：

- `README.md`
- `install.ps1`
- `install.sh`

然后重新提交推送：
```bash
git add .
git commit -m "Update username in install scripts"
git push
```

## 第 6 步：分享给别人

现在别人只需一行命令就能安装：

**Windows 用户（PowerShell）：**
```powershell
irm https://raw.githubusercontent.com/YOUR_USERNAME/ai-trade-alarm/main/install.ps1 | iex
```

**Linux / macOS 用户：**
```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/ai-trade-alarm/main/install.sh | bash
```

**或手动克隆：**
```bash
git clone https://github.com/YOUR_USERNAME/ai-trade-alarm.git
cd ai-trade-alarm
python launcher.py
```

## 别人使用流程

1. 执行一行命令安装
2. 安装 Ollama 并拉取 deepseek-r1 模型
3. 双击桌面快捷方式或运行 `python launcher.py`
4. 菜单选 `1` 完成配置（设置他们自己的钱包、部署合约）
5. 菜单选 `3` 创建交易任务
6. 菜单选 `4` 启动监控

## 手续费如何自动到你的钱包

合约 `FeeSplitter.sol` 中已硬编码你的收款地址：
`0xB4b9a2DcdcCf91713E8bCE68BD436Fa8062Db6A6`

每个用户部署合约时，合约代码固定指向你的钱包。用户每次链上成交，0.2% 手续费自动累积在合约中，你可以调用 `withdrawFees()` 提取到你的钱包。

## 更新代码

以后修改代码后，推送更新：
```bash
git add .
git commit -m "描述改动"
git push
```

已安装的用户运行 `git pull` 或重新执行安装命令即可获取更新。

## 安全确认

上传前请确认 `.gitignore` 排除了以下敏感文件：
- `.env`（含私钥）✅ 已排除
- `config.json`（含本地配置）✅ 已排除
- `data/`（数据库、日志）✅ 已排除

代码仓库中只包含 `config.example.json` 和 `.env.example` 模板，不含任何真实私钥。
