#!/usr/bin/env bash
# Internal server mode (Linux/Mac): clients on the LAN open http://<server-ip>:8501
set -e
cd "$(dirname "$0")"
[ -f .env ] || cp .env.example .env
[ -d venv ] || python3 -m venv venv
source venv/bin/activate
pip install -q -r backend/requirements.txt
uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
trap "kill $!" EXIT
sleep 6
echo "Clients open: http://$(hostname -I | awk '{print $1}'):8501"
streamlit run frontend/app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
