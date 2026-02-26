# build.ps1 — 在 Windows 上打包 wechat-digest.exe
# 用法：在项目根目录下运行 .\build\build.ps1
# 需要：Python 3.8+（已加入 PATH）

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot   # 项目根目录

Write-Host ""
Write-Host "  =====================================" -ForegroundColor Cyan
Write-Host "   wechat-digest.exe 打包脚本" -ForegroundColor Cyan
Write-Host "  =====================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. 检查 Python ────────────────────────────────────────────────────────────
try {
    $pyVer = python --version 2>&1
    Write-Host "  ✓ $pyVer" -ForegroundColor Green
} catch {
    Write-Host "  ✗ 未找到 Python，请先安装 Python 3.8+" -ForegroundColor Red
    exit 1
}

# ── 2. 安装/升级 PyInstaller ──────────────────────────────────────────────────
Write-Host "  → 安装 PyInstaller..."
python -m pip install --quiet --upgrade pyinstaller

# ── 3. Node.js 依赖（cheerio）────────────────────────────────────────────────
$nodeDir = Join-Path $root "wechat_search"
if (-not (Test-Path (Join-Path $nodeDir "node_modules\cheerio"))) {
    Write-Host "  → 安装 Node.js 依赖（cheerio）..."
    Push-Location $nodeDir
    npm install cheerio --silent
    Pop-Location
} else {
    Write-Host "  ✓ cheerio 已安装" -ForegroundColor Green
}

# ── 4. （可选）下载便携版 node.exe ────────────────────────────────────────────
# 如果系统没有 node，将自动下载便携版打包进 .exe
$nodeExe = Join-Path $root "build\node.exe"
$nodeInPath = $null
try { $nodeInPath = (Get-Command node -ErrorAction SilentlyContinue).Path } catch {}

if (-not $nodeInPath -and -not (Test-Path $nodeExe)) {
    Write-Host "  → 未检测到 node，下载便携版 node.exe (~40MB)..."
    $nodeUrl = "https://nodejs.org/dist/v22.13.1/win-x64/node.exe"
    Invoke-WebRequest -Uri $nodeUrl -OutFile $nodeExe -UseBasicParsing
    Write-Host "  ✓ node.exe 下载完成" -ForegroundColor Green
} elseif ($nodeInPath) {
    Write-Host "  ✓ 使用系统 node：$nodeInPath" -ForegroundColor Green
} else {
    Write-Host "  ✓ 使用已缓存 node.exe" -ForegroundColor Green
}

# ── 5. 运行 PyInstaller ───────────────────────────────────────────────────────
Write-Host "  → 运行 PyInstaller（首次较慢，约 1-3 分钟）..."
Push-Location $root
python -m PyInstaller build\wechat-digest.spec --noconfirm --clean
Pop-Location

# ── 6. 整理输出目录 ───────────────────────────────────────────────────────────
$distDir = Join-Path $root "dist"
$exeFile = Join-Path $distDir "wechat-digest.exe"

if (Test-Path $exeFile) {
    # 复制 .env.example 到 dist/（首次运行提示）
    $envExample = Join-Path $root ".env.example"
    if (Test-Path $envExample) {
        Copy-Item $envExample (Join-Path $distDir ".env.example")
    }

    $sizeMB = [math]::Round((Get-Item $exeFile).Length / 1MB, 1)
    Write-Host ""
    Write-Host "  =====================================" -ForegroundColor Green
    Write-Host "   ✅ 打包成功！" -ForegroundColor Green
    Write-Host "   文件：$exeFile" -ForegroundColor Green
    Write-Host "   大小：$sizeMB MB" -ForegroundColor Green
    Write-Host ""
    Write-Host "   使用方式：" -ForegroundColor Yellow
    Write-Host "   1. 复制 dist\ 目录到任意位置" -ForegroundColor Yellow
    Write-Host "   2. 双击 wechat-digest.exe" -ForegroundColor Yellow
    Write-Host "   3. 浏览器自动打开 http://localhost:8765" -ForegroundColor Yellow
    Write-Host "  =====================================" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "  ✗ 打包失败，请检查上方错误信息" -ForegroundColor Red
    exit 1
}
