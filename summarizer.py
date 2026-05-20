"""
扩充版摘要引擎
支持：智能摘要、多风格输出、本地+远程混合、优化提示工程
"""

import requests
import json
import re
import time
from config import OPENROUTER_KEY, SUMMARY_MODELS

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# ========== 多种风格提示词 ==========

PROMPTS = {
    "bullet": """你是专业内容摘要助手。输出要求：
1. 用中文，要点式输出，每点一句话
2. 保留关键数字、日期、人名、机构名
3. 如果原文有明确的观点或结论，单独列出
4. 字数控制在原文20-30%，最多800字
5. 不要添加原文没有的信息
6. 不输出"以上是..."之类的废话""",

    "one_sentence": """你是专业内容摘要助手。输出要求：
1. 用一句中文概括全文核心内容
2. 只保留最重要的信息，去掉所有细节
3. 语言精炼、有冲击力，像新闻标题""",

    "pros_cons": """你是专业的产品分析助手。输出要求：
1. 先一句话总结
2. 然后分「优点」和「缺点」两部分
3. 每点用一句话，保留关键数据
4. 最后给出「结论」——是否值得推荐""",

    "key_points": """你是专业商业分析师。输出要求：
1. 先一句话总结核心结论
2. 然后列出 3-5 个关键洞察，每点标注重要性（高/中/低）
3. 每个洞察写 1-2 句话，保留数据
4. 最后给出一个独特的「未见之处」——原文没提但值得关注的角度""",

    "story": """你是专业内容改写助手。输出要求：
1. 把原文改写成一个小故事/叙事
2. 保留所有关键事实和数据
3. 语言生动、有画面感，像在讲给人听
4. 结尾加一句个人点评（语气自然，不正式）
5. 控制在 300 字以内""",

    "actions": """你是专业的执行摘要助手。输出要求：
1. 先一句话总结
2. 然后列出「你可以做什么」——3-5条实际可操作的建议
3. 每条建议标注预计耗时和难度（简单/中等/困难）
4. 不谈理论，只讲行动""",
}

DEFAULT_STYLE = "bullet"


def call_openrouter(content: str, model: str = None, style: str = "bullet", system_extra: str = "") -> dict:
    """调用 OpenRouter API，支持多种风格
    
    Args:
        content: 要摘要的文本
        model: 模型名称，自动降级
        style: 摘要风格 (bullet/one_sentence/pros_cons/key_points/story/actions)
        system_extra: 额外的系统指令
    
    Returns:
        dict: {result, tokens, model, time, style}
    """
    if not model:
        model = SUMMARY_MODELS[0]
    
    if style not in PROMPTS:
        style = DEFAULT_STYLE
    
    system_prompt = PROMPTS[style]
    if system_extra:
        system_prompt += "\n\n额外要求：\n" + system_extra
    
    # 内容长度处理
    max_content_chars = 12000
    if len(content) > max_content_chars:
        original_len = len(content)
        content = content[:max_content_chars]
        content += f"\n\n...[原文共{original_len}字，已截取前{max_content_chars}字]"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json; charset=utf-8",
        "HTTP-Referer": "https://t.me/summary_ai_bot",
        "X-Title": "Summary Bot",
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请处理以下内容：\n\n{content}"}
        ],
        "max_tokens": 1500,
        "temperature": 0.3,
    }
    
    start = time.time()
    
    try:
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        resp = requests.post(
            f"{OPENROUTER_BASE}/chat/completions",
            headers=headers,
            data=body,
            timeout=60,
        )
        
        if resp.status_code == 429:
            current_idx = SUMMARY_MODELS.index(model) if model in SUMMARY_MODELS else 0
            if current_idx < len(SUMMARY_MODELS) - 1:
                return call_openrouter(content, SUMMARY_MODELS[current_idx + 1], style, system_extra)
            return {
                "result": "⚠️ 所有模型均被限流，请稍后再试",
                "tokens": 0,
                "model": model,
                "time": round(time.time() - start, 2),
                "style": style,
                "success": False
            }
        
        resp.raise_for_status()
        data = resp.json()
        
        result = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)
        
        return {
            "result": result,
            "tokens": tokens,
            "model": model.split(":")[0].split("/")[-1] if ":" in model else model,
            "time": round(time.time() - start, 2),
            "style": style,
            "success": True
        }
        
    except requests.exceptions.HTTPError as e:
        current_idx = SUMMARY_MODELS.index(model) if model in SUMMARY_MODELS else 0
        if current_idx < len(SUMMARY_MODELS) - 1:
            return call_openrouter(content, SUMMARY_MODELS[current_idx + 1], style, system_extra)
        return {
            "result": f"⚠️ API 调用失败：{e.response.status_code}",
            "tokens": 0,
            "model": model,
            "time": round(time.time() - start, 2),
            "style": style,
            "success": False
        }
    
    except Exception as e:
        return {
            "result": f"⚠️ 出错：{str(e)}",
            "tokens": 0,
            "model": model,
            "time": round(time.time() - start, 2),
            "style": style,
            "success": False
        }


def extract_text_from_url(url: str) -> str:
    """从 URL 提取文本内容"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = resp.apparent_encoding
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # 移除无用标签
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()
        
        # 提取正文
        text = soup.get_text(separator="\n", strip=True)
        
        # 清理多余空行
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = "\n".join(lines)
        
        if len(text) > 15000:
            text = text[:15000] + f"\n\n...[原文共{len(text)}字，已截取]"
        
        return text if len(text) > 100 else ""
    
    except Exception as e:
        return ""


def detect_content_type(text: str) -> str:
    """检测内容类型"""
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text)
    
    if urls:
        if any('youtube.com' in u or 'youtu.be' in u for u in urls):
            return "youtube"
        return "url"
    
    return "text"
