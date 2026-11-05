FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --system --uid 10001 --create-home appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; port=os.getenv('PORT','8000'); urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health/ready',timeout=3).read()" || exit 1
CMD ["sh", "-c", "alembic upgrade head && uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
