@echo off
REM Internal server mode (Windows): clients on the LAN open http://<server-ip>:8501
cd /d "%~dp0"
if not exist .env copy .env.example .env
if not exist venv python -m venv venv
call venv\Scripts\activate
pip install -q -r backend\requirements.txt
REM API stays private (127.0.0.1); only the web UI is exposed to the network
start "Hybrid RAG backend" /min cmd /c "call venv\Scripts\activate && uvicorn backend.main:app --host 127.0.0.1 --port 8000"
timeout /t 6 >nul
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do echo Clients open:  http://%%a:8501
streamlit run frontend\app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
