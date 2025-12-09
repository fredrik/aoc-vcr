# Frontend Progress

## Completed

- **index.html** - Main page structure with sidebar, canvas, and controls
- **style.css** - Dark theme styling
- **js/app.js** - Application logic, API integration, SSE support
- **js/player.js** - Playback state machine with speed control
- **js/renderers/grid.js** - 2D grid renderer (canvas-based)
- **js/renderers/points.js** - Point collection renderer

## Features

- Run selector sidebar (fetches from `/runs`)
- Canvas visualization with auto-scaling
- Playback controls: first, prev, play/pause, next, last
- Seek bar for frame navigation
- Speed selection (0.5x to 10x)
- Keyboard shortcuts: Space, Arrow keys, Home/End
- State panel showing non-visualization data
- SSE streaming support (connectStream method ready)

## Not Yet Implemented

- Graph renderer (`js/renderers/graph.js`)
- Diff highlighting between frames
- Live mode auto-follow toggle
- Run deletion UI
- Color map configuration per run

## Dependencies

- Backend API at `http://localhost:8000`
- No external JS dependencies (vanilla JS with ES modules)
