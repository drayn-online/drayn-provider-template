from __future__ import annotations

import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from typing import Any

from .base import ProviderAdapter


class XObserverAdapter(ProviderAdapter):
    """
    Example provider-owned X observer.

    Credentials remain local to this provider.

    The target account comes from job['subject']['id'].
    It is NOT a provider-global X_USER_ID.
    """

    def execute(self, job: dict[str, Any]) -> dict[str, Any]:
        subject = job["subject"]
        user_id = subject["id"]

        token = os.getenv("X_BEARER_TOKEN")
        if not token:
            return {
                "observations": [{
                    "observation_id": "synthetic-001",
                    "type": "x_post",
                    "source": "x",
                    "source_id": "synthetic",
                    "observed_at": None,
                    "retrieved_at": None,
                    "content": {
                        "text": "Synthetic observation for contract testing.",
                    },
                    "provenance": {
                        "source_url": "mock://node/provider",
                        "retrieval_method": "synthetic",
                        "transformations": [],
                        "limitations": [
                            "Synthetic data. X_BEARER_TOKEN is not configured."
                        ],
                    },
                }],
                "coverage": {"gaps": ["live_x_credentials_not_configured"]},
                "resource_usage": {"source_requests": 0},
            }

        context = job.get("context", {})
        constraints = job.get("constraints", {})
        max_results = int(constraints.get("max_observations", 25))

        params: dict[str, Any] = {
            "max_results": max(10, min(max_results, 100)),
            "tweet.fields": (
                "id,text,author_id,created_at,conversation_id,"
                "in_reply_to_user_id,referenced_tweets,entities"
            ),
            "expansions": "author_id,referenced_tweets.id",
            "user.fields": "id,name,username",
        }

        if context.get("start_time"):
            params["start_time"] = context["start_time"]
        if context.get("end_time"):
            params["end_time"] = context["end_time"]

        url = (
            f"https://api.x.com/2/users/{user_id}/tweets?"
            f"{urlencode(params)}"
        )

        request = Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
        )

        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))

        if payload.get("errors") and not payload.get("data"):
            raise RuntimeError(
                payload["errors"][0].get("detail", "X API returned an error.")
            )

        observations = []
        for post in payload.get("data", []):
            post_id = post.get("id")
            observations.append({
                "observation_id": f"x-{post_id}",
                "type": "x_post",
                "source": "x",
                "source_id": post_id,
                "observed_at": post.get("created_at"),
                "retrieved_at": None,
                "content": {
                    "text": post.get("text", ""),
                    "language": None,
                },
                "relationships": {
                    "conversation_id": post.get("conversation_id"),
                    "in_reply_to_user_id": post.get("in_reply_to_user_id"),
                    "referenced_tweets": post.get("referenced_tweets", []),
                },
                "provenance": {
                    "source_url": f"https://x.com/i/web/status/{post_id}",
                    "retrieval_method": "x_api_v2_user_posts",
                    "transformations": ["provider_normalization"],
                    "limitations": [],
                },
            })

        return {
            "observations": observations,
            "coverage": {
                "requested_start": context.get("start_time"),
                "requested_end": context.get("end_time"),
                "gaps": [],
            },
            "resource_usage": {
                "source_requests": 1,
                "observations_returned": len(observations),
            },
        }
