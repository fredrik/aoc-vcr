"""JSONL persistence for runs."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import asyncio


RUNS_DIR = Path("./runs")


@dataclass
class RunState:
    """In-memory state for an active run."""

    metadata: dict[str, Any]
    events: list[dict[str, Any]] = field(default_factory=list)
    subscribers: list[asyncio.Queue] = field(default_factory=list)
    finished: bool = False


# In-memory state for active runs
active_runs: dict[str, RunState] = {}


def ensure_runs_dir() -> None:
    """Ensure the runs directory exists."""
    RUNS_DIR.mkdir(exist_ok=True)


def run_file_path(run_id: str) -> Path:
    """Get the file path for a run."""
    return RUNS_DIR / f"{run_id}.jsonl"


def append_to_run(run_id: str, data: dict[str, Any]) -> None:
    """Append a JSON line to a run file."""
    ensure_runs_dir()
    with open(run_file_path(run_id), "a") as f:
        f.write(json.dumps(data) + "\n")


def read_run(run_id: str) -> dict[str, Any] | None:
    """Read a complete run from disk."""
    path = run_file_path(run_id)
    if not path.exists():
        return None

    metadata = None
    events = []
    finished = False

    with open(path) as f:
        for line in f:
            data = json.loads(line.strip())
            if data["type"] == "metadata":
                metadata = data
            elif data["type"] == "state":
                events.append(data)
            elif data["type"] == "finish":
                finished = True

    if metadata is None:
        return None

    return {
        "metadata": metadata,
        "events": events,
        "finished": finished,
    }


def list_runs() -> list[dict[str, Any]]:
    """List all runs with their metadata."""
    ensure_runs_dir()
    runs = []

    for path in RUNS_DIR.glob("*.jsonl"):
        with open(path) as f:
            first_line = f.readline()
            if first_line:
                metadata = json.loads(first_line.strip())
                if metadata.get("type") == "metadata":
                    # Count events
                    event_count = sum(1 for line in f if '"type": "state"' in line)
                    runs.append({
                        "run_id": metadata.get("run_id"),
                        "day": metadata.get("day"),
                        "part": metadata.get("part"),
                        "timestamp": metadata.get("timestamp"),
                        "event_count": event_count,
                    })

    # Sort by timestamp descending
    runs.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return runs


def delete_run(run_id: str) -> bool:
    """Delete a run file."""
    path = run_file_path(run_id)
    if path.exists():
        path.unlink()
        return True
    return False


def create_run(run_id: str, day: int, part: int, input_hash: str | None = None) -> dict[str, Any]:
    """Create a new run and persist metadata."""
    metadata = {
        "type": "metadata",
        "run_id": run_id,
        "day": day,
        "part": part,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_hash": input_hash,
    }

    append_to_run(run_id, metadata)

    # Create in-memory state
    active_runs[run_id] = RunState(metadata=metadata)

    return metadata


def add_event(run_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
    """Add an event to a run."""
    run = active_runs.get(run_id)
    if run is None:
        # Try to load from disk
        disk_run = read_run(run_id)
        if disk_run is None:
            return None
        run = RunState(
            metadata=disk_run["metadata"],
            events=disk_run["events"],
            finished=disk_run["finished"],
        )
        active_runs[run_id] = run

    if run.finished:
        return None

    iteration = len(run.events)
    event = {
        "type": "state",
        "iteration": iteration,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }

    append_to_run(run_id, event)
    run.events.append(event)

    return event


def finish_run(run_id: str) -> dict[str, Any] | None:
    """Mark a run as finished."""
    run = active_runs.get(run_id)
    if run is None:
        return None

    if run.finished:
        return None

    finish_event = {
        "type": "finish",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_iterations": len(run.events),
    }

    append_to_run(run_id, finish_event)
    run.finished = True

    return finish_event


def get_run_state(run_id: str) -> RunState | None:
    """Get the in-memory state for a run."""
    run = active_runs.get(run_id)
    if run is not None:
        return run

    # Try to load from disk
    disk_run = read_run(run_id)
    if disk_run is None:
        return None

    run = RunState(
        metadata=disk_run["metadata"],
        events=disk_run["events"],
        finished=disk_run["finished"],
    )
    active_runs[run_id] = run
    return run
