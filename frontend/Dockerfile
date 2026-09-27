FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt

RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/backend/requirements.txt \
    && pip install --no-cache-dir streamlit

COPY frontend /app/frontend

EXPOSE 8501

CMD ["streamlit", "run", "frontend/app.py", "--server.address=0.0.0.0", "--server.port=8501"]