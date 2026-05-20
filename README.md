# 🤖 AI Code Review Bot

> **AI 驱动的 Pull Request 自动审查助手**

当你的团队提交 Pull Request 时，Bot 自动审查代码变更，检查代码质量、安全性、最佳实践，并在 PR 中直接留言。

## ✨ 功能

- ✅ 自动监听 Pull Request 事件
- ✅ 代码质量检查（bug、性能、代码异味）
- ✅ 安全检查（SQL注入、XSS、密钥泄露）
- ✅ 最佳实践检查
- ✅ PR 评论区直接反馈

## 🚀 快速使用

在你的 GitHub 仓库设置 Webhook：

| 配置项 | 值 |
|--------|-----|
| Payload URL | `http://你的服务器:8900/webhook` |
| Content type | `application/json` |
| Secret | 见 Webhook 密钥 |
| Events | 勾选 **Pull requests** |

提交一个新 PR 试试，Bot 会自动审查。

## 🛠️ 自部署

```bash
git clone https://github.com/xiaozhuanfeng-lang/ai-code-review.git
cd ai-code-review
export GITHUB_TOKEN="你的 GitHub Token"
python3 review_bot.py
```

## 📄 许可证

MIT
