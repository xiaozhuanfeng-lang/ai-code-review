"""配置 - 所有可调节参数集中管理"""

import os
import json

# ========== 核心配置 ==========

# Telegram Bot Token — 从环境变量读取，你自己去 @BotFather 注册
BOT_TOKEN = os.environ.get("SUMMARY_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# OpenRouter API Key — 自动从 OpenClaw 配置读取
OPENROUTER_KEY = None

# 尝试从 OpenClaw 的 auth 配置里取 key
_auth_paths = [
    os.path.expanduser("~/.openclaw/agents/main/agent/auth-profiles.json"),
    os.path.expanduser("~/.openclaw/openclaw.json"),
]
for _p in _auth_paths:
    if os.path.exists(_p):
        try:
            with open(_p) as _f:
                _data = json.load(_f)
            # 从 auth-profiles.json 取
            _profiles = _data.get("profiles", {})
            for _name, _profile in _profiles.items():
                if "openrouter" in _name:
                    OPENROUTER_KEY = _profile.get("key")
                    break
        except:
            pass

# 如果 OpenClaw 配置里没有，从环境变量取
if not OPENROUTER_KEY:
    OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# ========== 免费模型配置 ==========

# 摘要用模型 — 优先用免费模型
# 按质量从高到低排列，自动降级
SUMMARY_MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",  # 限流最少，稳定
    "qwen/qwen3-coder:free",                    # 代码理解强
    "google/gemma-4-31b-it:free",               # 质量高但限流多
    "google/gemma-4-26b-a4b-it:free",           # 轻量版
    "minimax/minimax-m2.5:free",                # 备用
]

# 语音转录模型
WHISPER_MODEL = "large-v3"  # 本地 whisper 模型大小

# ========== 商业模式配置 ==========

# 免费额度
FREE_DAILY_LIMIT = 10  # 每天免费 10 次

# 订阅价格（人民币）
SUBSCRIPTION_PRICE = 19.9  # 月费 ¥19.9
PAY_PER_USE_PRICE = 0.5   # 按次 ¥0.5

# ========== 数据库 ==========
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "bot.db")

# ========== 开发者模式 ==========
DEBUG = True
