# Stage 1: Build environment
FROM python:3.11-slim as builder

WORKDIR /app

# Install system deps for Playwright
RUN apt-get update && apt-get install -y \
    curl wget unzip gnupg \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium --with-deps

# Stage 2: Final image
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /usr/local /usr/local
COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501"]
