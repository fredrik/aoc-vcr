# AoC Visualization System - Design Document

A system for recording and visualizing Advent of Code solutions as they execute, supporting both live streaming and playback of recorded runs.

## Overview

```
┌─────────────┐      HTTP POST       ┌─────────────┐       SSE        ┌─────────────┐
│   Python    │ ──────────────────→  │   Python    │ ───────────────→ │   Browser   │
│   Solver    │                      │   Backend   │                  │   Frontend  │
│  + Recorder │                      │  (FastAPI)  │                  │  (vanilla)  │
└─────────────┘                      └─────────────┘                  └─────────────┘
                                           │
                                           ↓ persist
                                     ./runs/{id}.jsonl
```

**Live mode**: Solver POSTs state snapshots → Backend persists + broadcasts via SSE → Frontend renders in real-time

**Replay mode**: Frontend fetches complete run from `/runs/{id}` → Steps through frames locally with playback controls

## Components

### 1. Python Client Library (`aoc-viz-client`)

A minimal library that hooks into solver code to record state snapshots.

#### Usage

```python
from aoc_viz import Recorder

def solve(input, part):
    rec = Recorder(day=4, part=part)
    grid = parse_input(input)

    removed_count = 1
    while removed_count != 0:
        grid, removed_count = remove(grid)
        rec.snapshot(grid=grid, removed=removed_count)

    rec.finish()
    return total_removed
```

#### API

```python
class Recorder:
    def __init__(
        self,
        day: int,
        part: int,
        backend_url: str = "http://localhost:8000",
        input_data: str | None = None,  # for hashing
        enabled: bool = True,            # easy toggle
    ):
        """
        Creates a new run on the backend.
        Computes input_hash if input_data provided.
        """

    def snapshot(self, **state) -> None:
        """
        Records a state snapshot. Auto-serializes:
        - dict[(i,j), value] → 2D grid
        - set/list of tuples → point collection
        - primitives → as-is

        Sends to backend, non-blocking.
        Increments internal iteration counter.
        """

    def finish(self) -> None:
        """
        Marks run as complete. Flushes pending events.
        """
```

#### Serialization

The library auto-detects and converts common AoC data structures:

| Python Type | Detected When | Serialized As |
|-------------|---------------|---------------|
| `dict[(int,int), str]` | All keys are 2-tuples of ints | `{"type": "grid", "data": [[...], ...], "bounds": {...}}` |
| `set[tuple[int, ...]]` | Set of tuples | `{"type": "points", "data": [[x,y], ...]}` |
| `dict[node, list[node]]` | Values are lists | `{"type": "graph", "nodes": [...], "edges": [...]}` |
| primitives | — | As-is |

Grid serialization preserves sparse grids efficiently:
```python
# Input: {(0,0): '#', (0,1): '.', (2,2): '@'}
# Output:
{
    "type": "grid",
    "data": {"0,0": "#", "0,1": ".", "2,2": "@"},
    "bounds": {"min_row": 0, "max_row": 2, "min_col": 0, "max_col": 2}
}
```

#### Error Handling

- Connection failures are logged but don't raise (solver keeps running)
- `enabled=False` makes all methods no-ops (zero overhead for production runs)
- Events are buffered and sent in batches if backend is slow

---

### 2. Backend (FastAPI)

A lightweight server that receives events, persists them, and streams to connected frontends.

#### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/runs` | Create new run, returns `{run_id}` |
| `POST` | `/runs/{run_id}/events` | Add state snapshot to run |
| `POST` | `/runs/{run_id}/finish` | Mark run complete |
| `GET` | `/runs/{run_id}/stream` | SSE stream (live events) |
| `GET` | `/runs/{run_id}` | Full run data (replay) |
| `GET` | `/runs` | List all runs |
| `DELETE` | `/runs/{run_id}` | Delete a run |

#### SSE Streaming

```
GET /runs/{run_id}/stream

# Response (text/event-stream):
event: metadata
data: {"run_id": "abc123", "day": 4, "part": 1, ...}

event: state
data: {"iteration": 0, "timestamp": "...", "data": {...}}

event: state
data: {"iteration": 1, "timestamp": "...", "data": {...}}

event: finish
data: {"total_iterations": 42}
```

New connections receive:
1. Run metadata immediately
2. All historical states (for late joiners)
3. New states as they arrive

#### Storage Format

Each run is stored as a JSONL file: `./runs/{run_id}.jsonl`

```jsonl
{"type": "metadata", "run_id": "abc123", "day": 4, "part": 1, "timestamp": "2025-12-09T14:30:00Z", "input_hash": "a1b2c3..."}
{"type": "state", "iteration": 0, "timestamp": "2025-12-09T14:30:00.001Z", "data": {"grid": {...}, "removed": 5}}
{"type": "state", "iteration": 1, "timestamp": "2025-12-09T14:30:00.002Z", "data": {"grid": {...}, "removed": 3}}
{"type": "finish", "timestamp": "2025-12-09T14:30:00.050Z", "total_iterations": 42}
```

#### Internal State

```python
# In-memory state for active runs
active_runs: dict[str, RunState] = {}

@dataclass
class RunState:
    metadata: dict
    events: list[dict]           # buffered for late-joining SSE clients
    subscribers: list[Queue]     # SSE client queues
    finished: bool = False
```

---

### 3. Frontend (Vanilla HTML/CSS/JS)

A single-page application with no build step or dependencies.

#### Structure

```
frontend/
├── index.html      # Main page, run selector + viz container
├── style.css       # Minimal styling
└── js/
    ├── app.js      # Main application logic
    ├── player.js   # Playback controls state machine
    └── renderers/
        ├── grid.js     # 2D grid renderer (canvas)
        └── points.js   # Point collection renderer
```

#### Views

**Run Selector**
- List of available runs (fetched from `/runs`)
- Shows: day, part, timestamp, iteration count
- Click to load

**Visualization**
- Canvas element for rendering
- Adapts to grid bounds automatically
- Color mapping for cell values (configurable)

**Playback Controls**
```
[|◀] [▶/❚❚] [▶|]    ◀━━━━━━●━━━━━━━━▶    [1x ▼]    Frame: 42/156
 prev play  next         seek bar          speed
```

#### Player State Machine

```
        ┌─────────────────────────────────────┐
        │                                     │
        ▼                                     │
   ┌─────────┐  play   ┌─────────┐  finish   │
   │ PAUSED  │ ──────→ │ PLAYING │ ──────────┘
   └─────────┘         └─────────┘
        ▲                   │
        │      pause        │
        └───────────────────┘
```

States:
- `PAUSED`: Manual stepping enabled, no auto-advance
- `PLAYING`: Auto-advance at configured speed
- `LIVE`: Streaming mode, follows latest frame (future enhancement)

#### Rendering

Grid renderer (canvas-based):
```javascript
class GridRenderer {
    constructor(canvas, colorMap = {}) { }

    render(gridData, options = {}) {
        // gridData: {type: "grid", data: {...}, bounds: {...}}
        // Calculates cell size based on canvas size and bounds
        // Draws each cell with mapped color
    }

    setColorMap(map) {
        // e.g., {'#': '#333', '.': '#eee', '@': '#e74c3c'}
    }

    highlightCells(cells) {
        // Overlay for showing "current" or "changed" cells
    }
}
```

---

## Data Flow

### Live Streaming

```
Solver                    Backend                    Frontend
   │                         │                          │
   │ POST /runs              │                          │
   │ ──────────────────────→ │                          │
   │ {run_id: "abc"}         │                          │
   │ ←────────────────────── │                          │
   │                         │                          │
   │                         │    GET /runs/abc/stream  │
   │                         │ ←──────────────────────  │
   │                         │    (SSE connection)      │
   │                         │                          │
   │ POST /runs/abc/events   │                          │
   │ {grid: {...}}           │                          │
   │ ──────────────────────→ │                          │
   │                         │ ─── event: state ──────→ │
   │                         │                          │
   │ POST /runs/abc/events   │                          │
   │ ──────────────────────→ │                          │
   │                         │ ─── event: state ──────→ │
   │                         │                          │
   │ POST /runs/abc/finish   │                          │
   │ ──────────────────────→ │                          │
   │                         │ ─── event: finish ─────→ │
```

### Replay

```
Frontend                  Backend
   │                         │
   │ GET /runs               │
   │ ──────────────────────→ │
   │ [{run_id, day, ...}]    │
   │ ←────────────────────── │
   │                         │
   │ GET /runs/abc           │
   │ ──────────────────────→ │
   │ {metadata, events: [...]}│
   │ ←────────────────────── │
   │                         │
   │ (local playback)        │
   │ ████████░░░░░░░░░░░░░░  │
```

---

## Project Structure

```
aoc-viz/
├── docker-compose.yml
├── README.md
│
├── backend/
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── src/
│       └── aoc_viz_backend/
│           ├── __init__.py
│           ├── main.py          # FastAPI app
│           ├── routes.py        # API endpoints
│           ├── storage.py       # JSONL persistence
│           └── streaming.py     # SSE handling
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── js/
│       ├── app.js
│       ├── player.js
│       └── renderers/
│           ├── grid.js
│           └── points.js
│
└── client/
    ├── pyproject.toml
    └── src/
        └── aoc_viz/
            ├── __init__.py
            ├── recorder.py      # Main Recorder class
            └── serializers.py   # Type detection + conversion
```

---

## Docker Compose

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./runs:/app/runs    # persist recordings
    environment:
      - CORS_ORIGINS=http://localhost:3000

  frontend:
    image: nginx:alpine
    ports:
      - "3000:80"
    volumes:
      - ./frontend:/usr/share/nginx/html:ro
```

---

## Implementation Order

### Phase 1: Minimal Viable Loop
1. Backend: POST `/runs`, POST `/runs/{id}/events`, GET `/runs/{id}`
2. Client: `Recorder` with basic `snapshot()` (no auto-serialization yet)
3. Frontend: Hardcoded run fetch, basic grid render, prev/next buttons
4. **Test**: Record a simple grid solver, replay it

### Phase 2: Live Streaming
5. Backend: SSE endpoint `/runs/{id}/stream`
6. Frontend: Connect to SSE, render frames as they arrive
7. **Test**: Watch solver execute in real-time

### Phase 3: Polish
8. Client: Auto-serialization for grids, points
9. Frontend: Full playback controls, speed adjustment, run selector
10. Backend: Run listing, deletion

### Phase 4: Extensions (future)
- Graph visualization renderer
- Diff highlighting (show what changed between frames)
- Multiple visualization panels
- Export to GIF/video

---

## Open Questions

1. **Cell colors**: Hardcoded mapping or configurable per-run via metadata?
2. **Large grids**: Canvas scaling strategy for grids > 200x200?
3. **Frame rate**: Default playback speed? 10 fps? Configurable in metadata?
4. **Authentication**: None for now (local only), but worth considering structure for later?

---

## Example: Visualizing Day 4

Day 4 iteratively removes cells from a grid. With the viz system:

```python
from aoc_viz import Recorder

def solve(input, part):
    rec = Recorder(day=4, part=part, input_data="".join(input))
    grid = parse_input(input)
    rec.snapshot(grid=grid, label="initial")

    total_removed = 0
    removed_count = 1

    while removed_count != 0:
        grid, removed_count = remove(grid)
        total_removed += removed_count
        rec.snapshot(grid=grid, removed_this_step=removed_count, total_removed=total_removed)

    rec.finish()
    return total_removed
```

Frontend renders each frame, showing:
- Grid state (cells colored by value)
- Sidebar with `removed_this_step` and `total_removed` counters
- Playback controls to step through the erosion process
