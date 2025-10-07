# ==========================================================
# Stage 1: Builder
# ==========================================================
FROM python:3.11-slim AS builder

WORKDIR /app

# -------------------------------
# Install system deps for Playwright + SQL Server ODBC
# -------------------------------
RUN apt-get update && apt-get install -y \
    curl wget unzip gnupg apt-transport-https ca-certificates \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libasound2 \
    && mkdir -p /etc/apt/keyrings \
    && curl https://packages.microsoft.com/keys/microsoft.asc \
        | gpg --dearmor > /etc/apt/keyrings/microsoft.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod stable main" \
        > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update && ACCEPT_EULA=Y apt-get install -y \
        msodbcsql18 unixodbc-dev gcc g++ \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------
# Install Python deps
# -------------------------------
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Install Playwright browsers (Chromium only)
RUN playwright install chromium --with-deps


# ==========================================================
# Stage 2: Runtime
# ==========================================================
FROM python:3.11-slim

WORKDIR /app

# Copy runtime deps from builder
COPY --from=builder /usr/local /usr/local
COPY --from=builder /opt/microsoft /opt/microsoft
COPY --from=builder /etc/apt/keyrings/microsoft.gpg /etc/apt/keyrings/microsoft.gpg
COPY --from=builder /etc/apt/sources.list.d/mssql-release.list /etc/apt/sources.list.d/mssql-release.list
COPY --from=builder /usr/lib/x86_64-linux-gnu/libodbc* /usr/lib/x86_64-linux-gnu/
COPY . .

ENV PYTHONUNBUFFERED=1 \
    ACCEPT_EULA=Y

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501"]
