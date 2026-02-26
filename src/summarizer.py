"""AI 聚合摘要：调用 OpenRouter API（OpenAI 兼容格式）"""
import json
import urllib.error
import urllib.request
from typing import Dict, List, Optional

from .crawler import Article

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

SUMMARIZE_PROMPT = """你是一名专业的 AI 产业分析师兼内容编辑。请对以下来自多个微信公众号的文章进行主题聚合和要点提炼，输出一份简洁的周报摘要。

要求：
1. 分两大板块输出：「技术动态」和「投融资动态」
2. 每个板块下按主题分小节（如：大模型进展、产品发布、行业动态、融资事件、IPO/上市等）
3. 每条要点一行，突出数字和关键事件
4. 语言简洁直接，避免模糊表述
5. 最后输出「本周关键信号」1-3条（影响最大的判断）
6. 输出格式为 Markdown

---

{articles_text}

---

请输出周报摘要："""


def _build_articles_text(articles_by_account: Dict[str, List[Article]]) -> str:
    lines = []
    # 按 group 分组展示，让 AI 更好地区分内容类型
    by_group: dict = {}
    for account, articles in articles_by_account.items():
        g = articles[0].group if articles else "其他"
        by_group.setdefault(g, {})[account] = articles

    for group_name, group_accounts in by_group.items():
        lines.append(f"# 板块：{group_name}")
        for account, articles in group_accounts.items():
            lines.append(f"## 来源：{account}")
            for a in articles[:12]:
                lines.append(f"- [{a.date}] {a.title}")
                if a.summary:
                    lines.append(f"  摘要：{a.summary[:80]}")
        lines.append("")
    return "\n".join(lines)


def summarize(
    articles_by_account: Dict[str, List[Article]],
    api_key: str,
    model: str = "step/step-3-5-flash-preview",
) -> Optional[str]:
    """
    调用 OpenRouter AI 生成聚合摘要。
    失败时返回 None（不影响主流程）。
    """
    if not api_key:
        return None

    total = sum(len(v) for v in articles_by_account.values())
    if total == 0:
        return None

    articles_text = _build_articles_text(articles_by_account)
    prompt = SUMMARIZE_PROMPT.format(articles_text=articles_text)

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 1500,
    }, ensure_ascii=False).encode("utf-8")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/your-org/wechat-feishu-digest",
        "X-Title": "wechat-feishu-digest",
    }

    req = urllib.request.Request(
        f"{OPENROUTER_BASE}/chat/completions",
        data=payload,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")[:300]
        print(f"  ⚠ AI 摘要失败 (HTTP {e.code}): {body}")
        return None
    except Exception as e:
        print(f"  ⚠ AI 摘要失败: {e}")
        return None
