@echo off
echo ==============================================
echo   TaxFlow AI - FastAPI Server Setup ^& Launch
echo ==============================================
echo.

cd /d "%~dp0"

echo [1/3] Installing dependencies...
pip install -r backend\requirements.txt
if %ERRORLEVEL% neq 0 (
    echo.
    echo WARNING: Failed to install some dependencies. Make sure python and pip are installed and in your PATH.
    echo.
)

echo [2/3] Initializing database and demo data...
python backend\app\seed.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo Note: Database initialization finished.
)

echo.
echo [3/3] Starting the FastAPI Local Server...
echo Opening TaxFlow AI at http://localhost:8000
echo API Docs available at http://localhost:8000/docs
echo.
start "" "http://localhost:8000/login.html"
python backend\run.py
pause
