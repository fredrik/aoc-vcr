# Instructions for Claude Code

This file contains instructions for Claude Code while working on this project.

## Project Overview

AoC VCR - A visualization tool for Advent of Code solver state snapshots.

## Structure

```
aoc-vcr/
├── backend/          # FastAPI backend
├── frontend/         # Vanilla JS web UI
├── library/          # Python client library
├── runs/             # JSONL run storage
└── docker-compose.yml
```

## Backend

FastAPI app with SSE streaming support.

**Running:**
```bash
cd backend && uv run uvicorn aoc_vcr_backend.main:app --reload
# or: docker compose up backend
```

**Endpoints:** POST `/runs`, GET/DELETE `/runs/{id}`, POST `/runs/{id}/events`, POST `/runs/{id}/finish`, GET `/runs/{id}/stream`, GET `/health`

**Dependencies:** fastapi, uvicorn[standard], sse-starlette

## Frontend

Vanilla JS with ES modules. No external dependencies.

**Features:** Run selector, canvas visualization, playback controls, speed selection, keyboard shortcuts, SSE streaming

**Not implemented:** Graph renderer, diff highlighting, live mode auto-follow, run deletion UI

## Client Library

Python client for recording solver state snapshots.

```python
from aoc_vcr import Recorder

with Recorder(day=4, part=1) as rec:
    rec.snapshot(grid=grid)
```

**Dependencies:** httpx>=0.27

**Install:** `uv pip install -e ./library`
