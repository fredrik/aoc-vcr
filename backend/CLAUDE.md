# Backend Progress

## Status: Complete

The backend is fully implemented per the design in `plans/aoc-vcr.md`.

## Structure

```
backend/
├── Dockerfile
├── pyproject.toml
└── src/aoc_vcr_backend/
    ├── __init__.py
    ├── main.py          # FastAPI app, CORS middleware
    ├── routes.py        # API endpoints
    ├── storage.py       # JSONL persistence, in-memory state
    └── streaming.py     # SSE handling
```

## Endpoints

| Method | Path | Status |
|--------|------|--------|
| POST | `/runs` | Done |
| POST | `/runs/{id}/events` | Done |
| POST | `/runs/{id}/finish` | Done |
| GET | `/runs/{id}/stream` | Done |
| GET | `/runs/{id}` | Done |
| GET | `/runs` | Done |
| DELETE | `/runs/{id}` | Done |
| GET | `/health` | Done |

## Running

```bash
# Local development
cd backend && uv run uvicorn aoc_vcr_backend.main:app --reload

# Docker
docker compose up backend
```

## Dependencies

- fastapi
- uvicorn[standard]
- sse-starlette

## Notes

- Runs stored as JSONL in `./runs/{run_id}.jsonl`
- SSE stream sends historical events to late joiners
- CORS origins configurable via `CORS_ORIGINS` env var
