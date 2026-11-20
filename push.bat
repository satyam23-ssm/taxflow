@echo off
echo ==============================================
echo   TaxFlow AI - Git Add, Commit and Push
echo ==============================================
echo.

cd /d "%~dp0"

echo [1/3] Checking status and staging files...
git add .

echo [2/3] Committing changes...
git commit -m "Convert frontend to JS render engine, inline styles, and optimize architecture"

echo [3/3] Pushing to GitHub (origin/main)...
git push origin main

echo.
if %ERRORLEVEL% equ 0 (
    echo ==============================================
    echo   Successfully pushed to GitHub!
    echo ==============================================
) else (
    echo.
    echo Note: If authentication was requested, please ensure your GitHub login or Personal Access Token is active.
)
echo.
pause

