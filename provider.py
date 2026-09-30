from __future__ import annotations

import secrets
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from schemas import validate_job, validate_x_observe_job


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class DRAYNProvider:
    """Reusable DRAYN provider boundary."""

    def __init__(self, provider_id: str, capabilities: dict[str, Any]):
        self.provider_id = provider_id
        self.capabilities = capabilities
        self.token = secrets.token_urlsafe(32)
        self.jobs: dict[str, dict[str, Any]] = {}
        self.lock = threading.Lock()
        self.adapters: dict[str, Any] = {}

    def register_adapter(self, capability_id: str, adapter: Any) -> None:
        self.adapters[capability_id] = adapter

    def validate(self, request: dict[str, Any]) -> tuple[bool, str]:
        ok, message = validate_job(request, set(self.capabilities))
        if not ok:
            return False, message

        capability_id = request["capability"]["id"]

        if capability_id == "social.x.observe":
            return validate_x_observe_job(request)

        return True, ""

    def submit(self, request: dict[str, Any]) -> dict[str, Any]:
        ok, message = self.validate(request)
        if not ok:
            return {
                "status_code": 400,
                "payload": {
                    "error": {
                        "code": "INVALID_REQUEST",
                        "message": message,
                    }
                },
            }

        job_id = request["job_id"]

        with self.lock:
            if job_id in self.jobs:
                existing = self.jobs[job_id]
                return {
                    "status_code": 202,
                    "payload": {
                        "job_id": job_id,
                        "provider_id": self.provider_id,
                        "status": existing["status"],
                    },
                }

            capability_id = request["capability"]["id"]

            if capability_id not in self.adapters:
                self.jobs[job_id] = {
                    "request": request,
                    "provider_id": self.provider_id,
                    "status": "refused",
                    "error": {
                        "code": "CAPABILITY_UNAVAILABLE",
                        "message": "Capability is declared but not currently available.",
                    },
                }
                return {
                    "status_code": 409,
                    "payload": {
                        "job_id": job_id,
                        "provider_id": self.provider_id,
                        "status": "refused",
                        "error": self.jobs[job_id]["error"],
                    },
                }

            self.jobs[job_id] = {
                "request": request,
                "provider_id": self.provider_id,
                "status": "accepted",
                "accepted_at": now(),
            }

        threading.Thread(
            target=self._execute,
            args=(job_id,),
            daemon=True,
        ).start()

        return {
            "status_code": 202,
            "payload": {
                "job_id": job_id,
                "provider_id": self.provider_id,
                "status": "accepted",
            },
        }

    def _execute(self, job_id: str) -> None:
        with self.lock:
            job = self.jobs[job_id]
            job["status"] = "running"
            job["started_at"] = now()

        request = job["request"]
        capability_id = request["capability"]["id"]
        adapter = self.adapters[capability_id]

        try:
            result = adapter.execute(request)

            with self.lock:
                job["status"] = "completed"
                job["completed_at"] = now()
                job["work_reference"] = f"work_{uuid.uuid4().hex[:12]}"
                job["result"] = result
        except Exception as exc:
            with self.lock:
                job["status"] = "failed"
                job["completed_at"] = now()
                job["error"] = {
                    "code": "EXECUTION_FAILED",
                    "message": str(exc),
                }

    def status(self, job_id: str) -> tuple[int, dict[str, Any]]:
        with self.lock:
            job = self.jobs.get(job_id)

        if not job:
            return 404, {
                "error": {
                    "code": "JOB_NOT_FOUND",
                    "message": "Job does not exist.",
                }
            }

        return 200, {
            "job_id": job_id,
            "provider_id": self.provider_id,
            "status": job["status"],
        }

    def result(self, job_id: str) -> tuple[int, dict[str, Any]]:
        with self.lock:
            job = self.jobs.get(job_id)

        if not job:
            return 404, {
                "error": {
                    "code": "JOB_NOT_FOUND",
                    "message": "Job does not exist.",
                }
            }

        if job["status"] != "completed":
            return 409, {
                "error": {
                    "code": "RESULT_NOT_READY",
                    "message": "Only completed jobs have results.",
                }
            }

        request = job["request"]
        result = job["result"]

        return 200, {
            "job_id": job_id,
            "provider_id": self.provider_id,
            "capability": request["capability"],
            "status": "completed",
            "result": result,
            "provenance": {
                "provider_version": "0.2",
                "generated_at": job["completed_at"],
            },
            "accounting": {
                "accepted_at": job["accepted_at"],
                "started_at": job["started_at"],
                "completed_at": job["completed_at"],
                "work_reference": job["work_reference"],
            },
            "payment": request["payment"],
        }

    def descriptor(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "protocol_version": "0.2",
            "capabilities": list(self.capabilities.values()),
            "status": "available",
        }
