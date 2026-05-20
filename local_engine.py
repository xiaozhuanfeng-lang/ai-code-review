"""
本地摘要引擎（Ollama Qwen2.5:3B）
用于快速响应短文本，OpenRouter 降级时使用
"""

import json
import time
import requests
import re

OLLAMA_BASE = "http://127.0.0.1:11434"
LOCAL_MODEL = "qwen2.5:3b"

LOCAL_PROMPTS = {
    "bullet": "你是专业的摘要助手。请用要点式输出总结以下内容。要求：中文，每点一句话，保留关键数据，结构清晰。不超过6个要点。",
    "one": "你是专业的摘要助手。请用一句话概括以下内容的中心思想。要求：中文，简洁有力。",
    "pros": "你是专业的产品分析助手。请分析以下内容的优缺点，按【优点】和【缺点】两部分输出。最后给出结论。要求：中文，每点一句话。",
    "deep": "你是深度分析师。请分析以下内容：1) 核心结论 2) 关键洞察 3) 未提及但重要的角度。要求：中文，条理清晰。",
    "story": "你是文案改写助手。请把以下内容改写成一个小故事。要求：中文，生动有趣，保留关键事实，300字以内。",
    "action": "你是执行顾问。请分析以下内容并给出可操作的建议。输出格式：先说结论，然后列出3-5条具体行动。每条标注难度。",
    "translate": "你是翻译和摘要专家。请将以下英文内容先翻译成中文，再给出摘要。要求：先放中文译文，再放摘要要点。",
}

def summarize_local(content: str, style: str = "bullet", system_extra: str = "") -> dict:
    """使用本地模型生成摘要"""
    
    system_prompt = LOCAL_PROMPTS.get(style, LOCAL_PROMPTS["bullet"])
    if system_extra:
        system_prompt += "\n" + system_extra
    
    # 短文本限制
    max_chars = 4000
    if len(content) > max_chars:
        content = content[:max_chars] + f"\n\n...[原文过长，截取前{max_chars}字]"
    
    payload = {
        "model": LOCAL_MODEL,
        "prompt": f"{system_prompt}\n\n内容：{content}\n\n摘要：",
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 800,
        }
    }
    
    start = time.time()
    
    try:
        resp = requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        
        result = data.get("response", "").strip()
        elapsed = time.time() - start
        tokens = data.get("eval_count", 0)
        
        # 清理结果
        result = re.sub(r'^(好的|好的，|让我|根据|以.*?：|以下是).{0,20}?\n', '', result).strip()
        
        return {
            "result": result,
            "tokens": tokens,
            "model": f"local-{LOCAL_MODEL}",
            "time": round(elapsed, 2),
            "style": style,
            "success": True,
            "local": True
        }
        
    except Exception as e:
        return {
            "result": f"⚠️ 本地模型出错：{str(e)}",
            "tokens": 0,
            "model": f"local-{LOCAL_MODEL}",
            "time": round(time.time() - start, 2),
            "style": style,
            "success": False,
            "local": True
        }


def detect_url(text: str) -> bool:
    return bool(re.match(r'https?://', text.strip()))
