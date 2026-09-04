@echo off
REM cph-by-chenkx 一键推送脚本
REM 1. 首先在 https://github.com/new 创建名为 cph-by-chenkx 的空仓库 (Public, 不要勾选 README/license/.gitignore)
REM 2. 在 https://github.com/settings/tokens 生成新 token (勾选 repo 权限)
REM 3. 运行本脚本，粘贴 token 完成推送

setlocal
cd /d "%~dp0"

echo ========================================
echo cph-by-chenkx push helper
echo ========================================
echo.

REM Check git
where git >nul 2>&1
if errorlevel 1 (
    echo [ERROR] git not found. Please install git first.
    pause
    exit /b 1
)

REM Set git config if not set
git config user.name >nul 2>&1
if errorlevel 1 (
    set /p GITHUB_USER="Enter your GitHub username: "
    git config user.name "!GITHUB_USER!"
)

REM Check remote
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    git remote add origin https://github.com/chenkx/cph-by-chenkx.git
)

echo.
echo Current remote:
git remote -v
echo.
echo Branch:
git branch --show-current
echo.
echo.

set /p GITHUB_TOKEN="Enter your NEW GitHub token (with repo permission): "

if "!GITHUB_TOKEN!"=="" (
    echo [ERROR] Token is required.
    pause
    exit /b 1
)

echo.
echo Pushing to GitHub...
git push -u https://!GITHUB_TOKEN!@github.com/chenkx/cph-by-chenkx.git master

if errorlevel 1 (
    echo.
    echo [ERROR] Push failed. Possible reasons:
    echo   1. Repository cph-by-chenkx does not exist on GitHub
    echo      Please create it at: https://github.com/new
    echo   2. Token does not have 'repo' permission
    echo   3. Token has expired
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Pushed to GitHub!
echo Repository: https://github.com/chenkx/cph-by-chenkx
pause
endlocal
