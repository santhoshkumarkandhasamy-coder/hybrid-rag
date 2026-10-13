@echo off
REM One-command local start (Windows): double-click run.bat
cd /d "%~dp0"
if not exist .env copy .env.example .env
if not exist venv python -m venv venv
call venv\Scripts\activate
pip install -q -r backend\requirements.txt
start "Hybrid RAG backend" cmd /k "call venv\Scripts\activate && uvicorn backend.main:app --port 8000"
timeout /t 5 >nul
start http://localhost:8501
streamlit run frontend\app.py
