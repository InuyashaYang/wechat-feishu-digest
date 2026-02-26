"""本地文件输出：Markdown 报告 + JSON 原始数据"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..crawler import Article


def output(
    articles_by_account: Dict[str, List[Article]],
    ai_summary: Optional[str],
    title: str,
    date_range: str,
    config,
) -> Path:
    """输出到本地目录，返回输出目录路径"""

    out_dir: Path = config.local_output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    md_path   = out_dir / f"{today}_digest.md"
    json_path = out_dir / f"{today}_raw.json"

    total = sum(len(v) for v in articles_by_account.values())

    # ── Markdown 报告 ────────────────────────────────────────────────────────
    md_lines = [
        f"# {title}",
        "",
        f"> 爬取范围：{date_range}  ·  合计：{total} 篇",
        f"> 数据来源：搜狗微信搜索（链接点击后跳转原文）",
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "---",
        "",
    ]

    # AI 摘要
    if ai_summary:
        md_lines += [
            "## 📊 AI 智能摘要",
            "",
            ai_summary.strip(),
            "",
            "---",
            "",
        ]

    # 各账号文章
    for account, articles in articles_by_account.items():
        md_lines += [f"## {account}（{len(articles)} 篇）", ""]
        for a in articles:
            if a.url:
                md_lines.append(f"- [{a.date}] [{a.title}]({a.url})")
            else:
                md_lines.append(f"- [{a.date}] {a.title}")
            if a.summary:
                md_lines.append(f"  > {a.summary[:100]}")
        md_lines.append("")

    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    print(f"  ✓ Markdown: {md_path}")

    # ── JSON 原始数据 ────────────────────────────────────────────────────────
    raw = {
        "meta": {
            "title": title,
            "date_range": date_range,
            "generated_at": datetime.now().isoformat(),
            "total": total,
        },
        "ai_summary": ai_summary,
        "articles": {
            account: [a.to_dict() for a in articles]
            for account, articles in articles_by_account.items()
        },
    }
    json_path.write_text(
        json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  ✓ JSON:     {json_path}")

    return out_dir
