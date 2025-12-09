"""API routes for the visualization backend."""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import storage
from . import streaming


router = APIRouter()


class CreateRunRequest(BaseModel):
    day: int
    part: int
    input_hash: str | None = None


class CreateRunResponse(BaseModel):
    run_id: str


class EventRequest(BaseModel):
    data: dict[str, Any]


@router.post("/runs", response_model=CreateRunResponse)
async def create_run(request: CreateRunRequest) -> CreateRunResponse:
    """Create a new run."""
    run_id = str(uuid.uuid4())[:8]
    storage.create_run(
        run_id=run_id,
        day=request.day,
        part=request.part,
        input_hash=request.input_hash,
    )
    return CreateRunResponse(run_id=run_id)


@router.post("/runs/{run_id}/events")
async def add_event(run_id: str, request: EventRequest) -> dict[str, Any]:
    """Add a state snapshot to a run."""
    event = storage.add_event(run_id, request.data)
    if event is None:
        raise HTTPException(status_code=404, detail="Run not found or already finished")

    # Broadcast to SSE subscribers
    await streaming.broadcast_to_subscribers(run_id, "state", event)

    return {"iteration": event["iteration"]}


@router.post("/runs/{run_id}/finish")
async def finish_run(run_id: str) -> dict[str, Any]:
    """Mark a run as complete."""
    finish_event = storage.finish_run(run_id)
    if finish_event is None:
        raise HTTPException(status_code=404, detail="Run not found or already finished")

    # Broadcast to SSE subscribers
    await streaming.broadcast_to_subscribers(run_id, "finish", finish_event)

    return finish_event


@router.get("/runs/{run_id}/stream")
async def stream_run(run_id: str) -> StreamingResponse:
    """SSE stream for live events."""
    run = storage.get_run_state(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    async def event_generator():
        async for event in streaming.stream_run(run_id):
            yield streaming.format_sse(event["event"], event["data"])

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/runs/{run_id}")
async def get_run(run_id: str) -> dict[str, Any]:
    """Get full run data for replay."""
    run_data = storage.read_run(run_id)
    if run_data is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run_data


@router.get("/runs")
async def list_runs() -> list[dict[str, Any]]:
    """List all runs."""
    return storage.list_runs()


@router.delete("/runs/{run_id}")
async def delete_run(run_id: str) -> dict[str, str]:
    """Delete a run."""
    # Remove from active runs if present
    if run_id in storage.active_runs:
        del storage.active_runs[run_id]

    if not storage.delete_run(run_id):
        raise HTTPException(status_code=404, detail="Run not found")

    return {"status": "deleted"}
