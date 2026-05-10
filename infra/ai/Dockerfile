# AI service — wraps the Anthropic SDK. v1 has only /health; real endpoint
# lands in Phase 6. Build context is the repo root.

FROM python:3.11-slim

WORKDIR /app

COPY services/ai/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY services/ai/app /app/app

EXPOSE 8001

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request, sys; \
sys.exit(0 if urllib.request.urlopen('http://localhost:8001/health', timeout=4).status == 200 else 1)" \
  || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
