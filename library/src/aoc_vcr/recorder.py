"""Recorder class for capturing AoC solver state snapshots."""

import hashlib
import logging
import queue
import threading
from datetime import datetime, timezone
from typing import Any

import httpx

from .serializers import serialize_value

logger = logging.getLogger(__name__)


class Recorder:
    """Records state snapshots from an AoC solver and sends them to the backend."""

    def __init__(
        self,
        day: int,
        part: int,
        backend_url: str = "http://localhost:8000",
        input_data: str | None = None,
        enabled: bool = True,
    ):
        """Create a new run on the backend.

        Args:
            day: AoC day number (1-25)
            part: Part number (1 or 2)
            backend_url: URL of the visualization backend
            input_data: Optional input data for hashing
            enabled: If False, all methods become no-ops
        """
        self.enabled = enabled
        if not enabled:
            return

        self.backend_url = backend_url.rstrip("/")
        self.day = day
        self.part = part
        self.input_hash = (
            hashlib.sha256(input_data.encode()).hexdigest()[:16]
            if input_data
            else None
        )
        self.iteration = 0
        self.run_id: str | None = None

        self._queue: queue.Queue[dict | None] = queue.Queue()
        self._client = httpx.Client(timeout=10.0)
        self._worker_thread: threading.Thread | None = None
        self._started = False

        self._create_run()

    def _create_run(self) -> None:
        """Create a new run on the backend."""
        try:
            response = self._client.post(
                f"{self.backend_url}/runs",
                json={
                    "day": self.day,
                    "part": self.part,
                    "input_hash": self.input_hash,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
            response.raise_for_status()
            self.run_id = response.json()["run_id"]
            self._start_worker()
        except Exception as e:
            logger.warning(f"Failed to create run: {e}")
            self.enabled = False

    def _start_worker(self) -> None:
        """Start the background worker thread."""
        if self._started:
            return
        self._started = True
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

    def _worker(self) -> None:
        """Background worker that sends events to the backend."""
        while True:
            event = self._queue.get()
            if event is None:
                break
            try:
                self._client.post(
                    f"{self.backend_url}/runs/{self.run_id}/events",
                    json=event,
                )
            except Exception as e:
                logger.warning(f"Failed to send event: {e}")

    def snapshot(self, **state: Any) -> None:
        """Record a state snapshot.

        Args:
            **state: Key-value pairs representing the current state.
                     Values are auto-serialized based on their type.
        """
        if not self.enabled or not self.run_id:
            return

        serialized = {key: serialize_value(value) for key, value in state.items()}

        event = {
            "iteration": self.iteration,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": serialized,
        }

        self._queue.put(event)
        self.iteration += 1

    def finish(self) -> None:
        """Mark the run as complete and flush pending events."""
        if not self.enabled or not self.run_id:
            return

        self._queue.put(None)
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)

        try:
            self._client.post(
                f"{self.backend_url}/runs/{self.run_id}/finish",
                json={"total_iterations": self.iteration},
            )
        except Exception as e:
            logger.warning(f"Failed to finish run: {e}")
        finally:
            self._client.close()

    def __enter__(self) -> "Recorder":
        return self

    def __exit__(self, *args: Any) -> None:
        self.finish()
