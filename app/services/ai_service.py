"""AI 解读：OpenAI 兼容接口，解读 / 实际场景分析两种。"""

from openai import OpenAI

from ..config import settings

_INTERPREPT_PROMPT = """你是医疗器械法规专家。请解读以下法规条款，用中文输出 markdown，包含四个小节：

## 本条要点
（一句话概括这条规定了什么）

## 关键角色与义务
（列出本条涉及的角色及其义务/责任，表格形式）

## 白话解读
（用通俗语言解释，让外行能懂）

## 记忆锚点
（帮助背诵的关键词串联）

---
法规：《{law_name}》
{label}

{content}"""

_SCENARIO_PROMPT = """你是医疗器械企业的资深法规顾问，服务对象是一名血管介入支架类产品的产品经理。
请针对以下法规条款做实际场景分析，用中文输出 markdown，包含三个小节：

## 落地场景
（这条规定在注册申报、生产、经营、使用、不良事件监测等哪些环节具体落到什么动作）

## 对产品经理意味着什么
（日常工作中哪里会遇到这条、需要产出什么证据/文件/流程）

## 风险提示
（不遵守会怎样，结合检查/飞检场景）

---
法规：《{law_name}》
{label}

{content}"""

KIND_PROMPTS = {"interpret": _INTERPREPT_PROMPT, "scenario": _SCENARIO_PROMPT}


def generate_reading(law_name: str, label: str, content: str, kind: str) -> str:
    """调用模型生成解读；kind ∈ interpret / scenario。未配置或调用失败抛异常。"""
    if kind not in KIND_PROMPTS:
        raise ValueError(f"未知的解读类型: {kind}")
    if not (settings.ai_base_url and settings.ai_api_key and settings.ai_model):
        raise RuntimeError("AI 未配置：请在 .env 中设置 AI_BASE_URL / AI_API_KEY / AI_MODEL")

    client = OpenAI(base_url=settings.ai_base_url, api_key=settings.ai_api_key, timeout=120)
    prompt = KIND_PROMPTS[kind].format(law_name=law_name, label=label, content=content)
    resp = client.chat.completions.create(
        model=settings.ai_model,
        messages=[{"role": "user", "content": prompt}],
    )
    return (resp.choices[0].message.content or "").strip()
