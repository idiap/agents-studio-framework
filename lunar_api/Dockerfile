# SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only

# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS base

# Declare the build arg
ARG APP_ENVIRONMENT

# Set working directory
WORKDIR /app

# Install only the tools required to fetch the private lunarflow dependency.
RUN apt-get update \
&& apt-get install -y --no-install-recommends -o Acquire::Retries=3 git openssh-client ca-certificates \
&& rm -rf /var/lib/apt/lists/*

# Copy configuration files first (for better caching)
COPY pyproject.toml uv.lock ./


# Install only external dependencies (not the project itself) for better layer caching
RUN uv sync --frozen --no-install-project --no-dev

# Copy the rest of the application (including src/)
COPY . .

# Now install the project itself
RUN uv sync --frozen --no-dev

# Expose the port the app runs on
EXPOSE 8000

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Command to run the application with hot reload in development, without in production
CMD if [ "$APP_ENVIRONMENT" = "development" ]; then \
    uv run uvicorn lunar_api.api.main:app --host 0.0.0.0 --port 8000 --reload; \
    else \
    uv run uvicorn lunar_api.api.main:app --host 0.0.0.0 --port 8000 --workers 4; \
    fi