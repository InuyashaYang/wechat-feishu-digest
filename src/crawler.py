"""微信文章爬取：调用 Node.js 搜索脚本"""
import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional


@dataclass
class Article:
    title:    str
    url:      str
    summary:  str
    datetime: str      # "YYYY-MM-DD HH:MM:SS"
    source:   str
    group:    str = "" # 所属账号组名称（科技媒体 / 投资资讯 / …）

    @property
    def date(self) -> str:
        return self.datetime[:10] if self.datetime else ""

    def to_dict(self) -> dict:
        return {
            "title":    self.title,
            "url":      self.url,
            "summary":  self.summary,
            "datetime": self.datetime,
            "source":   self.source,
            "group":    self.group,
        }


def _parse_articles(raw: list, group: str = "") -> List[Article]:
    result = []
    for item in raw:
        result.append(Article(
            title    = item.get("title", "").strip(),
            url      = item.get("url", "").strip(),
            summary  = item.get("summary", "").replace("\n", " ").strip(),
            datetime = item.get("datetime", ""),
            source   = item.get("source", ""),
            group    = group,
        ))
    return result


def search(
    account_name: str,
    query: str,
    script_path: str,
    num: int = 30,
    group: str = "",
) -> List[Article]:
    """调用 Node.js 脚本搜索微信文章，按日期倒序返回"""
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
        articles = _parse_articles(raw, group)
        # 严格按发布时间倒序（最新在前）
        articles.sort(key=lambda a: a.datetime or "0000-00-00", reverse=True)
        return articles
    except subprocess.TimeoutExpired:
        print(f"  ⚠ 搜索超时 [{account_name}]")
        return []
    except Exception as e:
        print(f"  ⚠ 搜索失败 [{account_name}]: {e}")
        return []


def filter_recent(articles: List[Article], days: int) -> List[Article]:
    """只保留最近 days 天的文章，并去重（同标题只取最新一条）"""
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    recent = [a for a in articles if a.date >= cutoff]

    # 去重：同标题只保留时间最新的一条
    seen: dict[str, Article] = {}
    for a in recent:
        key = a.title.strip()
        if key not in seen or a.datetime > seen[key].datetime:
            seen[key] = a
    return list(seen.values())
