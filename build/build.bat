@echo off
:: build.bat — 双击即可在 Windows 上打包 .exe
:: 等价于 .\build\build.ps1，但无需修改执行策略

echo.
echo  正在启动打包脚本...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0build.ps1"
if errorlevel 1 (
    echo.
    echo  打包失败！请检查上方错误信息
    pause
    exit /b 1
)
pause
