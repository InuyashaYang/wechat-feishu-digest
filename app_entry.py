"""
app_entry.py — PyInstaller 打包入口
双击 .exe 时自动启动 UI 并打开浏览器
"""
import os
import sys
import threading
import webbrowser
from pathlib import Path

# ── frozen 路径修正 ──────────────────────────────────────────────────────────
# sys._MEIPASS = PyInstaller 解压的临时目录（只读，存放代码/静态文件）
# EXE_DIR      = .exe 所在目录（可读写，存放 .env / output /）

EXE_DIR   = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
MEIPASS   = Path(getattr(sys, "_MEIPASS", str(EXE_DIR)))

# 将 src/ 加入 import 路径
sys.path.insert(0, str(MEIPASS / "src"))
sys.path.insert(0, str(MEIPASS))

# 修正工作目录（让 .env 写到 exe 旁边）
os.chdir(str(EXE_DIR))

# ── 启动 UI ──────────────────────────────────────────────────────────────────
PORT = 8765

def _open_browser():
    import time
    time.sleep(1.2)
    webbrowser.open(f"http://localhost:{PORT}")

if __name__ == "__main__":
    # 设置 ui.py 所需的路径常量（覆盖模块级默认值）
    import ui as ui_module
    ui_module.BASE_DIR = EXE_DIR
    ui_module.ENV_FILE = EXE_DIR / ".env"
    ui_module.UI_DIR   = MEIPASS / "ui"

    print(f"""
  ┌──────────────────────────────────────────┐
  │  🗞  AI 公众号周报                       │
  │      http://localhost:{PORT}               │
  │                                          │
  │  关闭此窗口即可停止服务                  │
  └──────────────────────────────────────────┘
""")

    threading.Thread(target=_open_browser, daemon=True).start()

    from http.server import HTTPServer
    from ui import Handler
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
