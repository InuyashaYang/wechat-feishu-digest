import os
import sys
from datetime import datetime
from pathlib import Path


def _parse_env_file(path: Path) -> dict:
    result = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            result[key.strip()] = val.strip().strip('"').strip("'")
    return result


def _split_list(s: str) -> list:
    return [x.strip() for x in s.split(",") if x.strip()]


class AccountGroup:
    """一组账号及其专属搜索模板"""
    def __init__(self, name: str, accounts: list, query_template: str):
        self.name = name
        self.accounts = accounts
        self.query_template = query_template


class Config:
    def __init__(self, env_file: str = ".env"):
        env_path = Path(env_file)
        file_vars = _parse_env_file(env_path)

        def get(key, default=None):
            return os.environ.get(key) or file_vars.get(key) or default

        now = datetime.now()
        self._year  = str(now.year)
        self._month = str(now.month)

        # ── 飞书配置（可选）────────────────────────────────────
        self.feishu_app_id       = get("FEISHU_APP_ID", "")
        self.feishu_app_secret   = get("FEISHU_APP_SECRET", "")
        self.feishu_share_openid = get("FEISHU_SHARE_OPENID", "")

        # ── OpenRouter AI 配置（可选）───────────────────────────
        self.openrouter_api_key = get("OPENROUTER_API_KEY", "")
        self.openrouter_model   = get("OPENROUTER_MODEL", "stepfun/step-3.5-flash:free")

        # ── 本地输出（可选）────────────────────────────────────
        self.local_output_dir = Path(get("LOCAL_OUTPUT_DIR", "./output"))

        # ── 爬取配置────────────────────────────────────────────
        self.search_days = int(get("SEARCH_DAYS", "7"))
        self.search_num  = int(get("SEARCH_NUM", "30"))

        # 默认账号 & 搜索模板（{account} {year} {month} 会被自动替换）
        default_accounts = get("ACCOUNTS", "机器之心,新智元,量子位")
        default_tmpl     = get("SEARCH_QUERY_TEMPLATE",
                               "{account} AI 大模型 {year}年{month}月")

        # 投资/商业类账号（可选，与 ACCOUNTS 合并）
        invest_accounts  = get("INVEST_ACCOUNTS",
                               "36氪,钛媒体,晚点LatePost,硅星人Pro")
        invest_tmpl      = get("INVEST_QUERY_TEMPLATE",
                               "{account} AI 投融资 创投 {year}年{month}月")

        # 自定义额外账号组（可选）
        extra_accounts   = get("EXTRA_ACCOUNTS", "")
        extra_tmpl       = get("EXTRA_QUERY_TEMPLATE", default_tmpl)

        # 构建账号组列表
        self.groups: list[AccountGroup] = []
        self.groups.append(AccountGroup(
            "科技媒体", _split_list(default_accounts), default_tmpl))
        self.groups.append(AccountGroup(
            "投资资讯", _split_list(invest_accounts), invest_tmpl))
        if extra_accounts:
            self.groups.append(AccountGroup(
                "自定义", _split_list(extra_accounts), extra_tmpl))

        # 所有账号的扁平列表（便于汇总统计）
        self.accounts = [a for g in self.groups for a in g.accounts]

        # Node.js 搜索脚本路径（frozen 模式从 _MEIPASS 找）
        def _assets_dir():
            if getattr(sys, "frozen", False):
                return Path(getattr(sys, "_MEIPASS", str(Path(__file__).parent)))
            return Path(__file__).parent.parent

        default_script = str(_assets_dir() / "wechat_search" / "scripts" / "search_wechat.js")
        self.search_script_path = get("SEARCH_SCRIPT_PATH", default_script)

    def build_query(self, account: str, template: str) -> str:
        """把模板里的 {account} {year} {month} 替换为实际值"""
        return (template
                .replace("{account}", account)
                .replace("{year}",    self._year)
                .replace("{month}",   self._month))

    def get_group(self, account: str) -> AccountGroup:
        """返回账号所属的分组"""
        for g in self.groups:
            if account in g.accounts:
                return g
        return self.groups[0]

    @property
    def feishu_enabled(self) -> bool:
        return bool(self.feishu_app_id and self.feishu_app_secret)

    @property
    def ai_enabled(self) -> bool:
        return bool(self.openrouter_api_key)
