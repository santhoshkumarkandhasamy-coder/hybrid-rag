#!/usr/bin/env bash
# One-command local start (Mac/Linux): ./run.sh
set -e
cd "$(dirname "$0")"
[ -f .env ] || { cp .env.example .env; echo "Created .env (admin password: see ADMIN_PASSWORD in it)"; }
PY=$(command -v python3.12 || command -v python3.11 || command -v python3.10 || command -v python3)
[ -d venv ] || "$PY" -m venv venv
source venv/bin/activate
pip install -q -r backend/requirements.txt
uvicorn backend.main:app --port 8000 &
BACK=$!
trap "kill $BACK" EXIT
sleep 4
echo "Open http://localhost:8501"
streamlit run frontend/app.py
