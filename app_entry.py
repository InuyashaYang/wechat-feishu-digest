"""
app_entry.py - PyInstaller entry point
"""
# --- Step 1: force UTF-8 BEFORE anything else touches stdout ---
import os
import sys

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    import io
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# --- Step 2: frozen path resolution ---
import threading
import webbrowser
from pathlib import Path

EXE_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
MEIPASS = Path(getattr(sys, "_MEIPASS", str(EXE_DIR)))

sys.path.insert(0, str(MEIPASS / "src"))
sys.path.insert(0, str(MEIPASS))

os.chdir(str(EXE_DIR))

# --- Step 3: start UI ---
PORT = 8765


def _open_browser():
    import time
    time.sleep(1.2)
    webbrowser.open(f"http://localhost:{PORT}")


if __name__ == "__main__":
    import ui as ui_module
    ui_module.BASE_DIR = EXE_DIR
    ui_module.ENV_FILE = EXE_DIR / ".env"
    ui_module.UI_DIR   = MEIPASS / "ui"

    print("")
    print("  +------------------------------------------+")
    print("  |  AI WeChat Digest                        |")
    print(f"  |  http://localhost:{PORT}                    |")
    print("  |  Close this window to stop the server   |")
    print("  +------------------------------------------+")
    print("")
    sys.stdout.flush()

    threading.Thread(target=_open_browser, daemon=True).start()

    from http.server import HTTPServer
    from ui import Handler
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopped.")
