# ============================================================
# Stage 1: build the frontend
# ============================================================
FROM node:25-slim AS frontend

# install pnpm via npm
RUN npm install -g pnpm

WORKDIR /pages

# copy dependency manifests first for better layer caching
COPY frontend/.npmrc frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./

# install frontend dependencies
RUN pnpm install --frozen-lockfile

# copy the rest of the frontend source code
COPY frontend/ ./

# build the static pages for production
RUN pnpm run build

# ============================================================
# Stage 2: build the production image
# ============================================================
FROM --platform=linux/amd64 python:3.13-slim

# install system dependencies
# - git: required by gitpython
# - libxml2/libxslt: required by lxml
# - cmake/make/g++: required by opencc
# - aria2: optional built-in download manager
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libxml2 \
    libxslt1.1 \
    cmake \
    make \
    g++ \
    aria2 \
    && rm -rf /var/lib/apt/lists/*

# install Poetry via pip
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true
RUN python -m pip install --no-cache-dir setuptools poetry

WORKDIR /app

# copy backend dependency manifests first for better layer caching
COPY backend/pyproject.toml backend/poetry.lock backend/poetry.toml ./backend/

# install backend dependencies
RUN cd backend && poetry install --no-cache --no-root --only main

# copy the rest of the backend source code
COPY backend/ ./backend/

# copy the built frontend assets from Stage 1
COPY --from=frontend /pages/build/ ./frontend/build/

# environment variable to control built-in aria2
ENV ENABLE_ARIA2=false

# entrypoint script
COPY <<'EOF' /app/entrypoint.sh
#!/bin/sh
cd /app/backend
if [ "$ENABLE_ARIA2" = "true" ]; then
  aria2c \
    --enable-rpc \
    --rpc-listen-all=false \
    --rpc-listen-port=6800 \
    --dir=/app/workspace/downloads \
    --daemon
fi
exec poetry run sanic app.main:app --host 0.0.0.0 --port 8000 --fast
EOF
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
VOLUME /app/workspace
ENTRYPOINT ["/app/entrypoint.sh"]
