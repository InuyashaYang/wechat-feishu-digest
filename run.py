#!/usr/bin/env python3
"""
wechat-feishu-digest
一键爬取微信公众号最新文章，AI 聚合摘要，输出到飞书文档或本地目录

用法:
  python run.py                    # 爬取 + 自动检测输出目标
  python run.py --days 14          # 爬最近 14 天
  python run.py --output feishu    # 只写飞书
  python run.py --output local     # 只写本地目录
  python run.py --output both      # 同时写飞书和本地
  python run.py --no-ai            # 跳过 AI 聚合
  python run.py --dry-run          # 仅爬取预览，不写任何输出
  python run.py --config .env.prod # 指定配置文件（默认 .env）
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 把 src 加入路径（让 run.py 在项目根目录直接运行）
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src import crawler, summarizer
from src.outputs import feishu_output, local_output


def main():
    parser = argparse.ArgumentParser(
        description="微信公众号 → 飞书/本地 一键聚合工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--days",    type=int, default=None,   help="爬取最近 N 天（覆盖 .env 中的 SEARCH_DAYS）")
    parser.add_argument("--output",  choices=["feishu", "local", "both", "auto"], default="auto",
                        help="输出目标：feishu / local / both / auto（默认 auto，根据配置自动选）")
    parser.add_argument("--no-ai",   action="store_true",      help="跳过 AI 聚合摘要")
    parser.add_argument("--dry-run", action="store_true",      help="仅爬取预览，不写任何输出")
    parser.add_argument("--config",  default=".env",           help="配置文件路径（默认 .env）")
    args = parser.parse_args()

    # ── 加载配置 ────────────────────────────────────────────────────────────
    config = Config(args.config)
    if args.days:
        config.search_days = args.days

    days  = config.search_days
    now   = datetime.now()
    start = (now - timedelta(days=days)).strftime("%Y-%m-%d")
    end   = now.strftime("%Y-%m-%d")
    date_range = f"{start} ~ {end}"
    title = f"AI公众号周报｜{'·'.join(config.accounts)}（{date_range}）"

    print(f"\n{'='*60}")
    print(f"  微信公众号 AI 周报  {now.strftime('%Y-%m-%d %H:%M')}")
    print(f"  范围: 最近 {days} 天  ({date_range})")
    print(f"  账号: {', '.join(config.accounts)}")
    print(f"{'='*60}\n")

    # ── 爬取 ────────────────────────────────────────────────────────────────
    articles_by_account = {}
    for account in config.accounts:
        query = config.search_query_template.format(account=account)
        print(f"[{account}] 搜索: {query!r} ...", end=" ", flush=True)
        all_arts = crawler.search(account, query, config.search_script_path, config.search_num)
        recent   = crawler.filter_recent(all_arts, days)
        articles_by_account[account] = recent
        print(f"共 {len(all_arts)} 条 → 近{days}天 {len(recent)} 条")

    total = sum(len(v) for v in articles_by_account.values())
    print(f"\n合计: {total} 篇\n")

    if total == 0:
        print("⚠ 未获取到任何文章，退出")
        return

    # ── dry-run 预览 ────────────────────────────────────────────────────────
    if args.dry_run:
        for account, articles in articles_by_account.items():
            print(f"── {account} ({len(articles)}篇) ──")
            for a in articles:
                print(f"  [{a.date}] {a.title[:70]}")
        return

    # ── AI 聚合摘要 ─────────────────────────────────────────────────────────
    ai_summary = None
    if not args.no_ai and config.ai_enabled:
        print("AI 聚合摘要中...", end=" ", flush=True)
        ai_summary = summarizer.summarize(
            articles_by_account,
            api_key=config.openrouter_api_key,
            model=config.openrouter_model,
        )
        print("✓" if ai_summary else "跳过（失败）")
    elif not config.ai_enabled and not args.no_ai:
        print("ℹ AI 聚合已跳过（未配置 OPENROUTER_API_KEY）")

    # ── 确定输出目标 ─────────────────────────────────────────────────────────
    output_mode = args.output
    if output_mode == "auto":
        targets = []
        if config.feishu_enabled:
            targets.append("feishu")
        targets.append("local")   # 本地总是作为 fallback
        output_mode = "both" if "feishu" in targets else "local"

    print(f"\n输出目标: {output_mode}")

    kwargs = dict(
        articles_by_account=articles_by_account,
        ai_summary=ai_summary,
        title=title,
        date_range=date_range,
        config=config,
    )

    # ── 输出 ────────────────────────────────────────────────────────────────
    if output_mode in ("feishu", "both"):
        if config.feishu_enabled:
            print("\n→ 写入飞书文档...")
            try:
                url = feishu_output(**kwargs)
                print(f"  ✅ 飞书文档: {url}")
            except Exception as e:
                print(f"  ❌ 飞书写入失败: {e}")
        else:
            print("⚠ 飞书未配置（FEISHU_APP_ID / FEISHU_APP_SECRET），跳过")

    if output_mode in ("local", "both"):
        print("\n→ 写入本地文件...")
        try:
            out_dir = local_output(**kwargs)
            print(f"  ✅ 本地目录: {out_dir.resolve()}")
        except Exception as e:
            print(f"  ❌ 本地写入失败: {e}")

    print(f"\n{'='*60}")
    print(f"  完成！合计 {total} 篇")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
