@echo off
REM Internal server mode (Windows): clients on the LAN open http://<server-ip>:8501
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
REM API stays private (127.0.0.1); only the web UI is exposed to the network
start "Hybrid RAG backend" /min cmd /c "call venv\Scripts\activate && uvicorn backend.main:app --host 127.0.0.1 --port 8000"
timeout /t 6 >nul
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do echo Clients open:  http://%%a:8501
streamlit run frontend\app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
