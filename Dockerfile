FROM python:3.12-slim

# Environment config
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# 1. Install OS dependencies (must be root)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl openssl fonts-liberation \
    libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libc6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxi6 libxdamage1 \
    libxext6 libxfixes3 libxrandr2 libxrender1 libxss1 libxtst6 \
    libdbus-1-3 libdrm2 libgbm1 libglib2.0-0 libgtk-3-0 libnss3 libpango-1.0-0 \
    libxshmfence1 \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 2. Create non-root user (NUMERIC UID)
RUN groupadd -r appuser --gid 10001 && useradd -r -g appuser --uid 10001 -m appuser

# 3. Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Install Playwright browsers (still root)
RUN python -m playwright install chromium

# 5. Copy application code
COPY dynatrace_report_app.py .

# 6. Fix ownership for non-root user
RUN mkdir -p /app /ms-playwright \
    && chown -R appuser:appuser /app /ms-playwright

# 7. Switch to non-root user (NUMERIC UID)
USER 10001

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "-w", "2", "-k", "gthread", "--threads", "8", "dynatrace_report_app:app"]
