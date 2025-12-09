"""SSE streaming for live run updates."""

import asyncio
import json
from typing import Any, AsyncGenerator

from . import storage


async def broadcast_to_subscribers(run_id: str, event_type: str, data: dict[str, Any]) -> None:
    """Broadcast an event to all subscribers of a run."""
    run = storage.active_runs.get(run_id)
    if run is None:
        return

    message = {"event": event_type, "data": data}

    # Send to all subscribers, remove dead ones
    dead_subscribers = []
    for queue in run.subscribers:
        try:
            queue.put_nowait(message)
        except asyncio.QueueFull:
            dead_subscribers.append(queue)

    for queue in dead_subscribers:
        run.subscribers.remove(queue)


async def stream_run(run_id: str) -> AsyncGenerator[dict[str, Any], None]:
    """Generate SSE events for a run.

    Yields all historical events first, then streams new ones.
    """
    run = storage.get_run_state(run_id)
    if run is None:
        return

    # Create a queue for this subscriber
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=1000)
    run.subscribers.append(queue)

    try:
        # Send metadata first
        yield {"event": "metadata", "data": run.metadata}

        # Send all historical events
        for event in run.events:
            yield {"event": "state", "data": event}

        # If already finished, send finish event and stop
        if run.finished:
            yield {
                "event": "finish",
                "data": {"total_iterations": len(run.events)},
            }
            return

        # Stream new events
        while True:
            try:
                message = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield message

                if message["event"] == "finish":
                    break
            except asyncio.TimeoutError:
                # Send keepalive
                yield {"event": "keepalive", "data": {}}

    finally:
        # Clean up subscriber
        if queue in run.subscribers:
            run.subscribers.remove(queue)


def format_sse(event: str, data: dict[str, Any]) -> str:
    """Format data as SSE message."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
