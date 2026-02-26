"""飞书文档输出"""
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, List, Optional

from ..crawler import Article

FEISHU_BASE = "https://open.feishu.cn/open-apis"


# ─── 飞书 API 工具 ───────────────────────────────────────────────────────────

def _request(method: str, path: str, token: str = None, body: dict = None) -> dict:
    url = f"{FEISHU_BASE}{path}"
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"飞书 API HTTP {e.code}: {e.read().decode('utf-8')[:300]}")


def _get_token(app_id: str, app_secret: str) -> str:
    resp = _request("POST", "/auth/v3/tenant_access_token/internal", body={
        "app_id": app_id, "app_secret": app_secret,
    })
    if resp.get("code") != 0:
        raise RuntimeError(f"获取 token 失败: {resp}")
    return resp["tenant_access_token"]


def _create_doc(token: str, title: str) -> str:
    resp = _request("POST", "/docx/v1/documents", token=token, body={"title": title})
    if resp.get("code") != 0:
        raise RuntimeError(f"创建文档失败: {resp}")
    return resp["data"]["document"]["document_id"]


def _append_blocks(token: str, doc_id: str, blocks: list) -> None:
    resp = _request(
        "POST",
        f"/docx/v1/documents/{doc_id}/blocks/{doc_id}/children",
        token=token,
        body={"children": blocks, "index": -1},
    )
    if resp.get("code") != 0:
        raise RuntimeError(f"追加块失败 (code={resp.get('code')}): {resp}")


def _share(token: str, doc_id: str, open_id: str) -> None:
    resp = _request(
        "POST",
        f"/drive/v1/permissions/{doc_id}/members?type=docx",
        token=token,
        body={
            "member_type": "openid",
            "member_id": open_id,
            "perm": "full_access",
            "type": "user",
        },
    )
    if resp.get("code") not in (0, 230001):
        print(f"  ⚠ 共享时返回: code={resp.get('code')} {resp.get('msg','')}")


# ─── 块构造 ─────────────────────────────────────────────────────────────────

def _text_elem(content: str, bold: bool = False, link: str = None) -> dict:
    style = {}
    if bold:
        style["bold"] = True
    if link:
        safe_url = urllib.parse.quote(link, safe=":/?=&%#@+._-~")
        style["link"] = {"url": safe_url}
    return {"text_run": {"content": content, "text_element_style": style}}


def _text_block(text: str) -> dict:
    return {"block_type": 2, "text": {"elements": [_text_elem(text)], "style": {"align": 1}}}


def _heading2_block(text: str) -> dict:
    return {"block_type": 4, "heading2": {"elements": [_text_elem(text)], "style": {"align": 1}}}


def _bullet_block(elements: list) -> dict:
    return {"block_type": 12, "bullet": {"elements": elements, "style": {"align": 1}}}


# ─── 主输出函数 ──────────────────────────────────────────────────────────────

def output(
    articles_by_account: Dict[str, List[Article]],
    ai_summary: Optional[str],
    title: str,
    date_range: str,
    config,
) -> str:
    """输出到飞书文档，返回文档链接"""

    token = _get_token(config.feishu_app_id, config.feishu_app_secret)
    doc_id = _create_doc(token, title)
    print(f"  ✓ 文档创建: https://feishu.cn/docx/{doc_id}")

    total = sum(len(v) for v in articles_by_account.values())
    summary_parts = [f"{n}: {len(a)}篇" for n, a in articles_by_account.items()]

    blocks = []

    # 元信息
    blocks.append(_text_block(f"爬取范围: {date_range}  |  合计: {total}篇  |  {'  '.join(summary_parts)}"))
    blocks.append(_text_block("数据来源: 搜狗微信搜索（链接点击后跳转原文）"))

    # AI 摘要（如有）
    if ai_summary:
        blocks.append(_heading2_block("📊 AI 智能摘要"))
        for line in ai_summary.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("## ") or line.startswith("### "):
                heading = line.lstrip("#").strip()
                blocks.append(_text_block(f"▶ {heading}"))
            elif line.startswith("- ") or line.startswith("• "):
                blocks.append(_bullet_block([_text_elem(line[2:].strip())]))
            elif line.startswith("**") and line.endswith("**"):
                blocks.append(_text_block(line.strip("*")))
            else:
                blocks.append(_text_block(line))

    # 各账号文章
    for account, articles in articles_by_account.items():
        blocks.append(_heading2_block(f"{account}（{len(articles)}篇）"))
        for a in articles:
            elems = [_text_elem(f"[{a.date}]  ")]
            if a.url:
                elems.append(_text_elem(a.title, link=a.url))
            else:
                elems.append(_text_elem(a.title, bold=True))
            blocks.append(_bullet_block(elems))

    # 分批写入（单次最多 40 块）
    chunk_size = 40
    for i in range(0, len(blocks), chunk_size):
        chunk = blocks[i: i + chunk_size]
        _append_blocks(token, doc_id, chunk)
        print(f"  ✓ 块 {i+1}~{min(i+chunk_size, len(blocks))}/{len(blocks)}")

    # 共享权限
    if config.feishu_share_openid:
        _share(token, doc_id, config.feishu_share_openid)
        print(f"  ✓ 已共享给 {config.feishu_share_openid}")

    return f"https://feishu.cn/docx/{doc_id}"
