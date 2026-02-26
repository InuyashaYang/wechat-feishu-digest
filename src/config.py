"""配置加载：从 .env 文件或环境变量读取"""
import os
from pathlib import Path


def _parse_env_file(path: Path) -> dict:
    """简单解析 .env 文件，支持注释行和空行"""
    result = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            result[key] = val
    return result


class Config:
    def __init__(self, env_file: str = ".env"):
        env_path = Path(env_file)
        file_vars = _parse_env_file(env_path)

        def get(key, default=None):
            return os.environ.get(key) or file_vars.get(key) or default

        # ── 飞书配置（可选）────────────────────────────────────
        self.feishu_app_id     = get("FEISHU_APP_ID", "")
        self.feishu_app_secret = get("FEISHU_APP_SECRET", "")
        self.feishu_share_openid = get("FEISHU_SHARE_OPENID", "")

        # ── OpenRouter AI 配置（可选）───────────────────────────
        self.openrouter_api_key = get("OPENROUTER_API_KEY", "")
        self.openrouter_model   = get("OPENROUTER_MODEL", "stepfun/step-3.5-flash:free")

        # ── 本地输出（可选）────────────────────────────────────
        self.local_output_dir = Path(get("LOCAL_OUTPUT_DIR", "./output"))

        # ── 爬取配置────────────────────────────────────────────
        accounts_str = get("ACCOUNTS", "机器之心,新智元,量子位")
        self.accounts = [a.strip() for a in accounts_str.split(",") if a.strip()]
        self.search_days = int(get("SEARCH_DAYS", "7"))
        self.search_num  = int(get("SEARCH_NUM", "30"))

        # 搜索关键词模板（可选，默认 "{account} AI 大模型 2026"）
        self.search_query_template = get("SEARCH_QUERY_TEMPLATE", "{account} AI 大模型 2026")

        # Node.js 搜索脚本路径
        default_script = str(Path(__file__).parent.parent / "wechat_search" / "scripts" / "search_wechat.js")
        self.search_script_path = get("SEARCH_SCRIPT_PATH", default_script)

    @property
    def feishu_enabled(self) -> bool:
        return bool(self.feishu_app_id and self.feishu_app_secret)

    @property
    def ai_enabled(self) -> bool:
        return bool(self.openrouter_api_key)
