"""Durable single-worker queue for local add-game operations."""

import json
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path


class JobStore:
    def __init__(self, path, operation, companion_operation=None):
        self.path = Path(path)
        self.operation = operation
        self.companion_operation = companion_operation
        self.lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="add-game")
        try:
            self.jobs = json.loads(self.path.read_text())
        except (OSError, ValueError):
            self.jobs = {}
        for job in self.jobs.values():
            if job["state"] in ("queued", "running"):
                job.update(
                    state="failed", message="Server restarted before completion. Retry to continue from saved data."
                )
        if self.jobs:
            self._save()

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.jobs, indent=2))
        tmp.replace(self.path)

    def get(self, job_id):
        with self.lock:
            return dict(self.jobs[job_id]) if job_id in self.jobs else None

    def submit(self, game_pk):
        return self._submit("add-game", {"gamePk": game_pk})

    def submit_companions(self, payload):
        return self._submit("companions", {"payload": payload})

    def _submit(self, kind, details):
        with self.lock:
            for job in self.jobs.values():
                if (job.get("kind", "add-game") == kind
                        and all(job.get(k) == v for k, v in details.items())
                        and job["state"] in ("queued", "running")):
                    return dict(job)
            job = {
                "id": uuid.uuid4().hex,
                "kind": kind,
                **details,
                "state": "queued",
                "stage": "queued",
                "message": "Waiting to process",
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "saved": False,
                "processed": False,
                "deployed": False,
            }
            self.jobs[job["id"]] = job
            self._save()
            self.executor.submit(self._run, job["id"])
            return dict(job)

    def _update(self, job_id, **values):
        with self.lock:
            self.jobs[job_id].update(values, updatedAt=datetime.now(timezone.utc).isoformat())
            self._save()

    def _run(self, job_id):
        self._update(job_id, state="running", stage="save", message="Saving game")
        try:
            job = self.jobs[job_id]
            companion_job = job.get("kind") == "companions"
            operation = self.companion_operation if companion_job else self.operation
            result = operation(
                job["payload"] if companion_job else job["gamePk"],
                on_progress=lambda values: self._update(job_id, **values)
            )
            self._update(job_id, **result, state="complete" if result["ok"] else "failed")
        except Exception as exc:
            self._update(job_id, state="failed", message=f"Processing stopped: {exc}")
