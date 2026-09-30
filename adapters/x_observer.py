from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from typing import Any

from .base import ProviderAdapter


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class XObserverAdapter(ProviderAdapter):
    """Provider-owned X observer for social.x.observe."""

    def execute(self, job: dict[str, Any]) -> dict[str, Any]:
        subject_id = job["subject"]["id"]
        username = subject_id.lstrip("@")
        retrieved_at = now()

        token = os.getenv("X_BEARER_TOKEN")
        if not token:
            return {
                "format": "structured_observations",
                "summary": "Synthetic observation for contract testing.",
                "observations": [{
                    "subject": subject_id,
                    "observation": "Synthetic data; live X credentials are not configured.",
                    "timestamp": retrieved_at,
                    "source": "x",
                }],
                "provenance": [{
                    "source": "x",
                    "reference": "mock://node/provider",
                    "observed_at": retrieved_at,
                    "retrieved_at": retrieved_at,
                }],
            }

        constraints = job.get("constraints", {})
        window = constraints.get("time_window", {})
        max_results = int(constraints.get("max_observations", 25))

        user_url = f"https://api.x.com/2/users/by/username/{username}"
        user_request = Request(
            user_url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
        with urlopen(user_request, timeout=30) as response:
            user_payload = json.loads(response.read().decode("utf-8"))

        user_data = user_payload.get("data")
        if not user_data or not user_data.get("id"):
            raise RuntimeError("X account could not be resolved from subject.id.")

        user_id = user_data["id"]
        params: dict[str, Any] = {
            "max_results": max(10, min(max_results, 100)),
            "tweet.fields": "id,text,author_id,created_at,conversation_id,in_reply_to_user_id,referenced_tweets,entities",
            "expansions": "author_id,referenced_tweets.id",
            "user.fields": "id,name,username",
        }
        if window.get("from"):
            params["start_time"] = window["from"]
        if window.get("to"):
            params["end_time"] = window["to"]

        url = f"https://api.x.com/2/users/{user_id}/tweets?{urlencode(params)}"
        request = Request(
            url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        )
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))

        if payload.get("errors") and not payload.get("data"):
            raise RuntimeError(payload["errors"][0].get("detail", "X API returned an error."))

        retrieved_at = now()
        observations = []
        provenance = []
        for post in payload.get("data", []):
            post_id = post.get("id")
            timestamp = post.get("created_at")
            observations.append({
                "subject": subject_id,
                "observation": post.get("text", ""),
                "timestamp": timestamp,
                "source": "x",
            })
            provenance.append({
                "source": "x",
                "reference": f"https://x.com/i/web/status/{post_id}",
                "observed_at": timestamp,
                "retrieved_at": retrieved_at,
            })

        return {
            "format": "structured_observations",
            "summary": f"Observed {len(observations)} X posts for {subject_id}.",
            "observations": observations,
            "provenance": provenance,
        }
