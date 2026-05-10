# FastAPI service — Pi IoT Platform main API.
# Build context is the repo root.

FROM python:3.11-slim

WORKDIR /app

# Install runtime deps separately so they cache.
COPY services/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy source.
COPY services/api/app /app/app

EXPOSE 8000

# Healthcheck uses Python's stdlib so we don't need curl in the image.
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request, sys; \
sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=4).status == 200 else 1)" \
  || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
