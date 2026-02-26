"""微信文章爬取：调用 Node.js 搜索脚本"""
import json
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List


@dataclass
class Article:
    title: str
    url: str
    summary: str
    datetime: str   # ISO 格式 "YYYY-MM-DD HH:MM:SS"
    source: str

    @property
    def date(self) -> str:
        return self.datetime[:10] if self.datetime else ""

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "summary": self.summary,
            "datetime": self.datetime,
            "source": self.source,
        }


def _parse_articles(raw: list) -> List[Article]:
    result = []
    for item in raw:
        result.append(Article(
            title    = item.get("title", "").strip(),
            url      = item.get("url", "").strip(),
            summary  = item.get("summary", "").replace("\n", " ").strip(),
            datetime = item.get("datetime", ""),
            source   = item.get("source", ""),
        ))
    return result


def search(account_name: str, query: str, script_path: str, num: int = 30) -> List[Article]:
    """调用 Node.js 脚本搜索微信文章"""
    if not os.path.exists(script_path):
        print(f"  ⚠ 搜索脚本不存在: {script_path}")
        return []

    tmp_out = f"/tmp/wechat_search_{account_name.replace('/', '_')}.json"
    cmd = ["node", script_path, query, "-n", str(num), "-o", tmp_out]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"  ⚠ 搜索出错 [{account_name}]: {result.stderr[:200]}")
            return []
        if not os.path.exists(tmp_out):
            return []
        with open(tmp_out, encoding="utf-8") as f:
            data = json.load(f)
        raw = data.get("articles", data if isinstance(data, list) else [])
        articles = _parse_articles(raw)
        articles.sort(key=lambda a: a.datetime, reverse=True)
        return articles
    except subprocess.TimeoutExpired:
        print(f"  ⚠ 搜索超时 [{account_name}]")
        return []
    except Exception as e:
        print(f"  ⚠ 搜索失败 [{account_name}]: {e}")
        return []


def filter_recent(articles: List[Article], days: int) -> List[Article]:
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return [a for a in articles if a.date >= cutoff]
