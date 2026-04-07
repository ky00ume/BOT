# ── Stage 1: dependency builder ─────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# System libraries required by Pillow (image rendering)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libjpeg-dev \
        zlib1g-dev \
        libfreetype6-dev \
        libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pinned dependencies from lock file
COPY requirements-lock.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements-lock.txt


# ── Stage 2: runtime image ───────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="Vision Town Discord Bot" \
      org.opencontainers.image.description="츄마고치 Discord RPG Bot" \
      org.opencontainers.image.source="https://github.com/ky00ume/BOT"

# Runtime system libraries (Pillow + fonts)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libjpeg62-turbo \
        zlib1g \
        libfreetype6 \
        libpng16-16 \
        fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /install /usr/local

# Non-root user for security
RUN useradd --create-home --shell /bin/bash botuser
WORKDIR /app
RUN chown botuser:botuser /app

USER botuser

# Copy application source
COPY --chown=botuser:botuser . .

# Create directories that the bot writes to at runtime
RUN mkdir -p logs data

# Environment defaults (override via .env or docker-compose environment:)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BOT_LOG_DIR=/app/logs

ENTRYPOINT ["python", "main.py"]
