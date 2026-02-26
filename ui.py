#!/usr/bin/env python3
"""
ui.py - wechat-feishu-digest 配置与运行界面
纯 Python 标准库实现，无外部依赖

用法:
  python ui.py          # 启动 UI，默认 http://localhost:8765
  python ui.py --port 9000
"""

import argparse
import json
import os
import queue
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"
UI_DIR   = BASE_DIR / "ui"


# ─── .env 读写 ────────────────────────────────────────────────────────────────

def read_env() -> dict:
    result = {}
    if not ENV_FILE.exists():
        return result
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip().strip('"').strip("'")
    return result


def write_env(data: dict) -> None:
    """将 dict 写回 .env，保留注释结构"""
    existing = []
    if ENV_FILE.exists():
        existing = ENV_FILE.read_text(encoding="utf-8").splitlines()

    # 找出已有 key，更新它们
    written_keys = set()
    new_lines = []
    for line in existing:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k = stripped.partition("=")[0].strip()
            if k in data:
                new_lines.append(f"{k}={data[k]}")
                written_keys.add(k)
                continue
        new_lines.append(line)

    # 追加新 key
    for k, v in data.items():
        if k not in written_keys:
            new_lines.append(f"{k}={v}")

    ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


# ─── 运行状态管理 ─────────────────────────────────────────────────────────────

run_lock   = threading.Lock()
run_queue: queue.Queue = queue.Queue()
is_running = False


def _do_run(extra_args: list):
    global is_running
    cmd = [sys.executable, str(BASE_DIR / "run.py")] + extra_args
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(BASE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in proc.stdout:
            run_queue.put({"type": "log", "text": line.rstrip()})
        proc.wait()
        status = "done" if proc.returncode == 0 else "error"
        run_queue.put({"type": "status", "status": status, "code": proc.returncode})
    except Exception as e:
        run_queue.put({"type": "status", "status": "error", "text": str(e)})
    finally:
        is_running = False


def start_run(args: list):
    global is_running
    with run_lock:
        if is_running:
            return False
        is_running = True
    # 清空旧队列
    while not run_queue.empty():
        try:
            run_queue.get_nowait()
        except queue.Empty:
            break
    t = threading.Thread(target=_do_run, args=(args,), daemon=True)
    t.start()
    return True


# ─── HTTP 处理器 ──────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # 静默访问日志

    def _json(self, code: int, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _html(self, body: bytes):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _sse_start(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def _sse_send(self, data: str):
        msg = f"data: {data}\n\n"
        self.wfile.write(msg.encode())
        self.wfile.flush()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/":
            # 服务 index.html
            html_path = UI_DIR / "index.html"
            if html_path.exists():
                self._html(html_path.read_bytes())
            else:
                self._html(b"<h1>index.html not found</h1>")

        elif path == "/api/config":
            env = read_env()
            self._json(200, {
                "accounts":               env.get("ACCOUNTS", "机器之心,新智元,量子位"),
                "search_query_template":  env.get("SEARCH_QUERY_TEMPLATE",
                                                  "{account} AI 大模型 {year}年{month}月"),
                "invest_accounts":        env.get("INVEST_ACCOUNTS", "36氪,钛媒体,晚点,硅星人"),
                "invest_query_template":  env.get("INVEST_QUERY_TEMPLATE",
                                                  "{account} AI 融资 大模型 {year}年{month}月"),
                "extra_accounts":         env.get("EXTRA_ACCOUNTS", ""),
                "extra_query_template":   env.get("EXTRA_QUERY_TEMPLATE", ""),
                "openrouter_api_key":     env.get("OPENROUTER_API_KEY", ""),
                "openrouter_model":       env.get("OPENROUTER_MODEL",
                                                  "stepfun/step-3.5-flash:free"),
                "local_output_dir":       env.get("LOCAL_OUTPUT_DIR", "./output"),
                "feishu_app_id":          env.get("FEISHU_APP_ID", ""),
                "feishu_app_secret":      env.get("FEISHU_APP_SECRET", ""),
                "feishu_share_openid":    env.get("FEISHU_SHARE_OPENID", ""),
                "search_days":            env.get("SEARCH_DAYS", "7"),
                "search_num":             env.get("SEARCH_NUM", "30"),
            })

        elif path == "/api/stream":
            # Server-Sent Events：流式返回运行日志
            self._sse_start()
            timeout = 300  # 最多等 5 分钟
            elapsed = 0
            try:
                while elapsed < timeout:
                    try:
                        item = run_queue.get(timeout=1)
                        self._sse_send(json.dumps(item, ensure_ascii=False))
                        if item.get("type") == "status":
                            break
                    except queue.Empty:
                        if not is_running:
                            break
                        elapsed += 1
                        self._sse_send(json.dumps({"type": "ping"}))
            except (BrokenPipeError, ConnectionResetError):
                pass

        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b""

        if path == "/api/config":
            try:
                data = json.loads(body.decode())
                # 映射前端字段 → .env key
                mapping = {
                    "accounts":              "ACCOUNTS",
                    "search_query_template": "SEARCH_QUERY_TEMPLATE",
                    "invest_accounts":       "INVEST_ACCOUNTS",
                    "invest_query_template": "INVEST_QUERY_TEMPLATE",
                    "extra_accounts":        "EXTRA_ACCOUNTS",
                    "extra_query_template":  "EXTRA_QUERY_TEMPLATE",
                    "openrouter_api_key":    "OPENROUTER_API_KEY",
                    "openrouter_model":      "OPENROUTER_MODEL",
                    "local_output_dir":      "LOCAL_OUTPUT_DIR",
                    "feishu_app_id":         "FEISHU_APP_ID",
                    "feishu_app_secret":     "FEISHU_APP_SECRET",
                    "feishu_share_openid":   "FEISHU_SHARE_OPENID",
                    "search_days":           "SEARCH_DAYS",
                    "search_num":            "SEARCH_NUM",
                }
                env_data = {mapping[k]: v for k, v in data.items() if k in mapping and v}
                write_env(env_data)
                self._json(200, {"ok": True})
            except Exception as e:
                self._json(400, {"error": str(e)})

        elif path == "/api/run":
            try:
                data = json.loads(body.decode()) if body else {}
                extra = []
                if data.get("output"):
                    extra += ["--output", data["output"]]
                if data.get("days"):
                    extra += ["--days", str(data["days"])]
                if data.get("no_ai"):
                    extra.append("--no-ai")
                if data.get("dry_run"):
                    extra.append("--dry-run")
                if start_run(extra):
                    self._json(200, {"ok": True, "started": True})
                else:
                    self._json(409, {"ok": False, "reason": "already running"})
            except Exception as e:
                self._json(400, {"error": str(e)})

        elif path == "/api/stop":
            self._json(200, {"ok": True, "note": "stop not implemented (process completes naturally)"})

        else:
            self._json(404, {"error": "not found"})


# ─── 主函数 ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="wechat-feishu-digest UI")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    UI_DIR.mkdir(exist_ok=True)

    server = HTTPServer(("0.0.0.0", args.port), Handler)
    url = f"http://localhost:{args.port}"
    print(f"\n  ✅ UI 已启动：{url}")
    print(f"  📁 项目目录：{BASE_DIR}")
    print(f"  ⚙️  配置文件：{ENV_FILE}")
    print(f"\n  按 Ctrl+C 停止\n")

    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  已停止")


if __name__ == "__main__":
    main()
