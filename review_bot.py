#!/usr/bin/env python3
"""
AI Code Review Bot — 自动审查 GitHub PR
当有新的 Pull Request 时，AI 自动审查代码并留下评论
"""

import os
import sys
import json
import time
import hmac
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# ====== 配置 ======
PORT = int(os.environ.get("REVIEW_PORT", "8900"))
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
AI_MODEL = "deepseek-chat"

# 从环境变量读取
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "lizhi-review-secret-2026")


def call_ai(prompt, max_tokens=2000):
    """调用 AI 审查代码"""
    import requests
    
    # 优先用 OpenRouter
    auth_file = os.path.expanduser("~/.openclaw/agents/main/agent/auth-profiles.json")
    key = ""
    if os.path.exists(auth_file):
        with open(auth_file) as f:
            profiles = json.load(f).get("profiles", {})
        for name, p in profiles.items():
            if "openrouter" in name.lower():
                key = p.get("key", "")
                break
    
    if key:
        try:
            body = json.dumps({
                "model": "nvidia/nemotron-3-super-120b-a12b:free",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.2
            }, ensure_ascii=False).encode('utf-8')
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json; charset=utf-8",
                    "X-Title": "CodeReviewBot"
                },
                data=body,
                timeout=60
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except:
            pass
    
    return "[AI 审查失败]"


class ReviewBotHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/")
        if path == "/health":
            self._json({"status": "ok", "bot": "ai-code-review"})
        elif path == "/" or path == "/webhook":
            self._html_response("""
            <!DOCTYPE html>
            <html><head><meta charset="utf-8"><title>AI Code Review Bot</title>
            <style>
            body{font-family:-apple-system,sans-serif;background:#0d1117;color:#c9d1d9;max-width:700px;margin:60px auto;padding:0 20px}
            h1{color:#58a6ff}code{background:#21262d;padding:3px 8px;border-radius:4px}
            .step{margin:20px 0;padding:16px;background:#161b22;border-radius:8px;border:1px solid #30363d}
            </style></head><body>
            <h1>🔍 AI Code Review Bot</h1>
            <p>自动审查 GitHub Pull Request 的 AI 助手</p>
            <div class="step">
            <h3>📦 部署状态</h3>
            <p>服务运行中 ✅</p>
            </div>
            <div class="step">
            <h3>🔧 配置方法</h3>
            <p>在你的 GitHub 仓库中：</p>
            <p>1. 进入 <b>Settings → Webhooks → Add webhook</b></p>
            <p>2. Payload URL: <code>http://你的服务器地址:8900/webhook</code></p>
            <p>3. Content type: <code>application/json</code></p>
            <p>4. Secret: <code>你的密钥</code></p>
            <p>5. 勾选 <b>Pull requests</b></p>
            </div>
            </body></html>
            """)
        else:
            self._json({"error": "not found"}, 404)
    
    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        if path == "/webhook":
            self._handle_webhook()
        else:
            self._json({"error": "not found"}, 404)
    
    def _handle_webhook(self):
        """处理 GitHub Webhook"""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        # 验证签名
        signature = self.headers.get("X-Hub-Signature-256", "")
        if not self._verify_signature(body, signature):
            self._json({"error": "invalid signature"}, 403)
            return
        
        event = self.headers.get("X-GitHub-Event", "")
        
        if event == "ping":
            self._json({"msg": "pong"})
            return
        
        if event == "pull_request":
            data = json.loads(body)
            action = data.get("action", "")
            
            if action in ["opened", "synchronize"]:
                self._json({"status": "processing"})
                # 异步处理，不阻塞 webhook 响应
                import threading
                t = threading.Thread(target=self._review_pr, args=(data,))
                t.start()
                return
        
        self._json({"msg": f"event {event} received, no action taken"})
    
    def _review_pr(self, data):
        """审查 Pull Request"""
        pr = data.get("pull_request", {})
        repo = data.get("repository", {})
        
        pr_number = pr.get("number")
        repo_full = repo.get("full_name", "")
        pr_title = pr.get("title", "")
        pr_body = pr.get("body", "") or ""
        pr_url = pr.get("html_url", "")
        pr_diff_url = pr.get("diff_url", "")
        
        print(f"[Review] #{pr_number} {repo_full}: {pr_title}")
        
        try:
            # 获取 diff
            import requests
            headers = {
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3.diff",
                "User-Agent": "AI-Code-Review-Bot"
            }
            
            diff_resp = requests.get(pr_diff_url, headers=headers, timeout=30)
            diff_text = diff_resp.text if diff_resp.status_code == 200 else "(无法获取 diff)"
            
            # 截取太长 diff
            if len(diff_text) > 8000:
                diff_text = diff_text[:8000] + "\n\n...[diff 过长已截断]"
            
            # AI 审查
            prompt = f"""你是专业的代码审查员。请审查以下 Pull Request：

仓库：{repo_full}
PR #{pr_number}：{pr_title}
描述：{pr_body}

代码变更（diff）：
```diff
{diff_text}
```

请检查以下方面：
1. **代码质量**：是否有 bug、性能问题、代码异味
2. **安全性**：是否有安全漏洞（SQL注入、XSS、密钥泄露等）
3. **最佳实践**：是否符合语言/框架的最佳实践
4. **可维护性**：命名、注释、代码结构是否清晰

输出格式：
- 每个问题一行，用「⚠️」或「🔴」（严重问题）
- 如果没问题，输出「✅ LGTM」（Looks Good To Me）
- 不要输出无关信息"""
            
            review = call_ai(prompt)
            
            # 提交评论到 PR
            comment_url = f"https://api.github.com/repos/{repo_full}/issues/{pr_number}/comments"
            comment_data = {
                "body": f"## 🤖 AI Code Review\n\n{review}\n\n---\n*由 AI Code Review Bot 自动生成*"
            }
            
            comment_resp = requests.post(
                comment_url,
                headers={
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "AI-Code-Review-Bot"
                },
                json=comment_data,
                timeout=30
            )
            
            if comment_resp.status_code == 201:
                print(f"  ✅ 评论已提交到 PR #{pr_number}")
            else:
                print(f"  ❌ 提交评论失败: {comment_resp.status_code}")
                
        except Exception as e:
            print(f"  ❌ 审查失败: {e}")
    
    def _verify_signature(self, body, signature):
        """验证 webhook 签名"""
        if not signature or not WEBHOOK_SECRET:
            return True  # 开发模式跳过验证
        expected = "sha256=" + hmac.new(
            WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    
    def _json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    
    def _html_response(self, html, status=200):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    
    def log_message(self, fmt, *args):
        print(f"[ReviewBot] {args[0]} {args[1]} {args[2]}")


def main():
    # 从 GitHub token 文件读取
    global GITHUB_TOKEN
    if not GITHUB_TOKEN:
        # 从 gh 的凭据存储读取
        import subprocess
        result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            GITHUB_TOKEN = result.stdout.strip()
    
    if not GITHUB_TOKEN:
        print("❌ 请设置 GITHUB_TOKEN 环境变量，或用 gh auth login 登录")
        sys.exit(1)
    
    print(f"""
╔══════════════════════════════════════╗
║     🤖 AI Code Review Bot           ║
║                                      ║
║   监听端口: {PORT}                      ║
║   GitHub: @xiaozhuanfeng-lang        ║
║                                      ║
║   配置 webhook 到你的仓库即可使用     ║
╚══════════════════════════════════════╝
""")
    
    server = HTTPServer(("0.0.0.0", PORT), ReviewBotHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n停止服务")


if __name__ == "__main__":
    main()
