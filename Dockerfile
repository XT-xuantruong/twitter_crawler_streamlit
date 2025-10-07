# ==========================================================
# Stage 1: Builder
# ==========================================================
FROM python:3.11-slim as builder

WORKDIR /app

# -------------------------------
# Install system deps for Playwright + SQL Server
# -------------------------------
RUN apt-get update && apt-get install -y \
    curl wget unzip gnupg apt-transport-https ca-certificates \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libasound2 \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && ACCEPT_EULA=Y apt-get install -y \
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

# -------------------------------
# Copy dependencies & runtime binaries from builder
# -------------------------------
COPY --from=builder /usr/local /usr/local
COPY --from=builder /opt/microsoft /opt/microsoft
COPY --from=builder /etc/apt/sources.list.d/mssql-release.list /etc/apt/sources.list.d/mssql-release.list
COPY --from=builder /usr/lib/x86_64-linux-gnu/libodbc* /usr/lib/x86_64-linux-gnu/
COPY . .

ENV PYTHONUNBUFFERED=1 \
    ACCEPT_EULA=Y

EXPOSE 8501

# -------------------------------
# Run the app
# -------------------------------
CMD ["streamlit", "run", "app.py", "--server.port=8501"]
