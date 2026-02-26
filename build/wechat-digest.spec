# -*- mode: python ; coding: utf-8 -*-
# wechat-digest.spec — PyInstaller 打包配置

import os
from pathlib import Path

ROOT = Path(SPECPATH).parent  # build/ 的上级 = 项目根目录

# 需要随包携带的数据文件（目标路径相对于 _MEIPASS）
added_files = [
    (str(ROOT / "ui"),                    "ui"),
    (str(ROOT / "src"),                   "src"),
    (str(ROOT / "wechat_search"),         "wechat_search"),
    (str(ROOT / "run.py"),                "."),
]

# 如果有打包进来的便携版 node.exe，也加进去
node_win = ROOT / "build" / "node.exe"
if node_win.exists():
    added_files.append((str(node_win), "."))

a = Analysis(
    [str(ROOT / "app_entry.py")],
    pathex=[str(ROOT), str(ROOT / "src")],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        "http.server",
        "urllib.parse",
        "json",
        "subprocess",
        "threading",
        "queue",
        "webbrowser",
        "pathlib",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "pandas"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="wechat-digest",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,          # 保留控制台窗口，方便看日志
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "build" / "icon.ico"),
)
