# aoc-vcr

Visualize your Advent of Code solvers in real-time.

Record state snapshots from your Python solver and watch them play back in a web UI with playback controls, speed adjustment, and live streaming.

## Quick Start

1. Start the backend:
   ```bash
   cd backend && uv run uvicorn aoc_vcr_backend.main:app --reload
   ```

2. Open `frontend/index.html` in your browser

3. Install the client library:
   ```bash
   uv pip install -e ./library
   ```

4. Add recording to your solver:
   ```python
   from aoc_vcr import Recorder

   with Recorder(day=4, part=1) as rec:
       for step in solve(data):
           rec.snapshot(grid=grid, count=count)
   ```

5. Run your solver and watch the visualization update live

## Architecture

- **library/** - Python library for recording snapshots
- **backend/** - FastAPI server with SSE streaming
- **frontend/** - Vanilla JS web UI with canvas rendering

## Features

- Non-blocking recording (won't slow your solver)
- Live streaming via Server-Sent Events
- Playback controls with speed adjustment (0.5x - 10x)
- Keyboard shortcuts (Space, Arrow keys, Home/End)
- Grid and point visualization renderers
