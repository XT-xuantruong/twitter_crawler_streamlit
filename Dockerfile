# ==========================================================
# Stage 1: Builder
# ==========================================================
FROM python:3.11 AS builder

WORKDIR /app

# -------------------------------
# Install system dependencies
# -------------------------------
RUN apt-get update && apt-get install -y \
    curl wget unzip gnupg apt-transport-https ca-certificates \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libasound2 unixodbc-dev gcc g++ \
    && wget -q https://packages.microsoft.com/debian/11/prod/pool/main/m/msodbcsql18/msodbcsql18_18.3.2.1-1_amd64.deb \
    && ACCEPT_EULA=Y dpkg -i msodbcsql18_18.3.2.1-1_amd64.deb || apt-get -fy install \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------
# Install Python dependencies
# -------------------------------
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install Playwright Chromium
RUN playwright install chromium --with-deps


# ==========================================================
# Stage 2: Runtime
# ==========================================================
FROM python:3.11

WORKDIR /app

# Copy runtime deps
COPY --from=builder /usr/local /usr/local
COPY --from=builder /usr/lib/x86_64-linux-gnu/libodbc* /usr/lib/x86_64-linux-gnu/
RUN DRIVER_PATH=$(find /opt/microsoft/msodbcsql18/lib64 -name "libmsodbcsql-*.so*" | head -n 1) \
    && echo "[ODBC Driver 18 for SQL Server]\nDescription=Microsoft ODBC Driver 18 for SQL Server\nDriver=$DRIVER_PATH\nUsageCount=1" > /etc/odbcinst.ini
    
COPY . .

ENV PYTHONUNBUFFERED=1 \
    ACCEPT_EULA=Y \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501"]
