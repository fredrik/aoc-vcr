# AoC VCR Client Library

Python client library for recording AoC solver state snapshots.

## Status

**Phase 1: Complete**

Core functionality implemented:
- `Recorder` class with non-blocking `snapshot()` via background thread
- Auto-serialization for grids, points, and graphs
- Connection failure handling (logs warning, doesn't crash solver)
- `enabled=False` for zero-overhead production runs
- Context manager support

## Structure

```
library/
├── pyproject.toml
└── src/aoc_vcr/
    ├── __init__.py
    ├── recorder.py      # Main Recorder class
    └── serializers.py   # Type detection + conversion
```

## API

```python
from aoc_vcr import Recorder

rec = Recorder(day=4, part=1, input_data=raw_input)
rec.snapshot(grid=grid, removed=count)
rec.finish()

# Or as context manager:
with Recorder(day=4, part=1) as rec:
    rec.snapshot(grid=grid)
```

## Dependencies

- `httpx>=0.27`

## Installation

```bash
uv pip install -e ./library
```

## Backend API Expected

The client expects these endpoints:

- `POST /runs` → `{"run_id": "..."}`
- `POST /runs/{run_id}/events` (accepts iteration, timestamp, data)
- `POST /runs/{run_id}/finish` (accepts total_iterations)

## Future Work

- Event batching if backend is slow
- Retry logic for transient failures
- Optional async mode using `httpx.AsyncClient`
