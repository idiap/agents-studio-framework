<!--
# SPDX-FileCopyrightText: 2026 Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Danilo Gusicuma <danilo@lunarbase.ai>
#
# SPDX-License-Identifier: GPL-3.0-only
-->
# Argumentation Agent

## Prerequisites

- Python 3.13+
- uv
- Node.js 20+

## Backend (FastAPI)

From the repo root:

1. Install Python dependencies

- uv sync

2. Run the API

- uv run uvicorn lunar_api.api.main:app --host 0.0.0.0 --port 8000

The API will be available at <http://localhost:8000>.

### Migrations

Migrations run automatically on startup. To run them manually:

- uv run python -c "from lunar_api.app_context.config import AppConfig; from lunar_api.persistence.connections.sqlite_connection import SQLiteConnection; from lunar_api.persistence.migrations import run_migrations; config=AppConfig.from_env(); conn=SQLiteConnection(config.database_path); conn.connect(); applied=run_migrations(conn); print('Applied migrations:', applied); conn.disconnect()"

By default, the SQLite database is stored at ./lunar_api.db. Override with:

- SQLITE_DATABASE_PATH=/absolute/path/to/db.sqlite

## Frontend (Next.js)

From [lunar-chat-interface](lunar-chat-interface):

1. Install dependencies

- npm install

2. Run the dev server

- npm run dev

The frontend will be available at <http://localhost:8080>.

## Tests

From the repo root:

- uv run pytest
