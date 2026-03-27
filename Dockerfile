FROM python:3.12-slim


# Environment config
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive


WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl openssl fonts-liberation \
    libasound2 libatk1.0-0 libatk-bridge2.0-0 \
    libc6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxi6 libxdamage1 \
    libxext6 libxfixes3 libxrandr2 libxrender1 libxss1 libxtst6 \
    libdbus-1-3 libdrm2 libgbm1 libglib2.0-0 libgtk-3-0 libnss3 libpango-1.0-0 \
    libxshmfence1 \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

#RUN pip install --no-cache-dir --upgrade pip certifi


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY dynatrace_report_app.py .

#EXPOSE 5000
#CMD ["python", "dynatrace_report_app.py"]


# Install Playwright browsers for this user
RUN python -m playwright install chromium

EXPOSE 5000

# Run with Gunicorn
# -w: workers, -k: worker class (gthread is a solid default for Flask IO)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "-w", "2", "-k", "gthread", "--threads", "8", "dynatrace_report_app:app"]
