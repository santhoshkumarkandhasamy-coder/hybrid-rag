@echo off
REM One-command local start (Windows): double-click run.bat
cd /d "%~dp0"
if not exist .env copy .env.example .env
if not exist venv (
    REM Prefer Python 3.12 (best package support), then 3.11, then default
    py -3.12 -m venv venv 2>nul || py -3.11 -m venv venv 2>nul || python -m venv venv
)
call venv\Scripts\activate
python -c "import sys,struct; v=sys.version_info; ok=(3,10)<=v[:2]<=(3,12) and struct.calcsize('P')==8; print('Python',sys.version.split()[0],'64-bit' if struct.calcsize('P')==8 else '32-bit'); sys.exit(0 if ok else 1)"
if errorlevel 1 (
    echo.
    echo ERROR: This app needs 64-bit Python 3.10, 3.11 or 3.12.
    echo Install Python 3.12 64-bit from https://www.python.org/downloads/release/python-3120/
    echo then delete the "venv" folder here and run this file again.
    pause
    exit /b 1
)
pip install -q -r backend\requirements.txt
start "Hybrid RAG backend" cmd /k "call venv\Scripts\activate && uvicorn backend.main:app --port 8000"
timeout /t 5 >nul
start http://localhost:8501
streamlit run frontend\app.py
