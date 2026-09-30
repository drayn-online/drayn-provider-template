from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from capabilities import X_OBSERVE, capability_document
from provider import DRAYNProvider


HOST = os.getenv("PROVIDER_HOST", "127.0.0.1")
PORT = int(os.getenv("PROVIDER_PORT", "8010"))
ROOT = Path(__file__).parent
TOKEN_FILE = ROOT / "provider-token.txt"

provider = DRAYNProvider(
    provider_id=os.getenv("PROVIDER_ID", "provider-local"),
    capabilities={
        X_OBSERVE.id: capability_document(X_OBSERVE),
    },
)

from adapters.x_observer import XObserverAdapter
provider.register_adapter(X_OBSERVE.id, XObserverAdapter())

if os.getenv("DRAYN_PROVIDER_TOKEN"):
    provider.token = os.environ["DRAYN_PROVIDER_TOKEN"]
elif TOKEN_FILE.exists():
    provider.token = TOKEN_FILE.read_text(encoding="utf-8").strip()
else:
    TOKEN_FILE.write_text(provider.token + "\n", encoding="utf-8")


def send_json(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    server_version = "DRAYN-Provider-Template/0.2"

    def authorized(self) -> bool:
        return self.headers.get("Authorization") == f"Bearer {provider.token}"

    def read_json(self) -> dict[str, Any] | None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            value = json.loads(self.rfile.read(length))
            return value if isinstance(value, dict) else None
        except (ValueError, json.JSONDecodeError):
            return None

    def do_GET(self) -> None:
        if self.path == "/":
            send_json(self, 200, provider.descriptor())
            return

        if not self.authorized():
            send_json(self, 401, {
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Bearer token is invalid.",
                }
            })
            return

        parts = self.path.strip("/").split("/")

        if len(parts) == 2 and parts[0] == "jobs":
            status, payload = provider.status(parts[1])
            send_json(self, status, payload)
            return

        if len(parts) == 3 and parts[0] == "jobs" and parts[2] == "result":
            status, payload = provider.result(parts[1])
            send_json(self, status, payload)
            return

        send_json(self, 404, {
            "error": {
                "code": "NOT_FOUND",
                "message": "Endpoint not found.",
            }
        })

    def do_POST(self) -> None:
        if self.path != "/jobs":
            send_json(self, 404, {
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Endpoint not found.",
                }
            })
            return

        if not self.authorized():
            send_json(self, 401, {
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Bearer token is invalid.",
                }
            })
            return

        request = self.read_json()
        if request is None:
            send_json(self, 400, {
                "error": {
                    "code": "INVALID_JSON",
                    "message": "Request body must be a JSON object.",
                }
            })
            return

        response = provider.submit(request)
        send_json(
            self,
            response["status_code"],
            response["payload"],
        )

    def log_message(self, fmt: str, *args: Any) -> None:
        print(fmt % args)


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"DRAYN provider listening at http://{HOST}:{PORT}")
    print(f"Provider ID: {provider.provider_id}")
    print(f"Provider token stored at {TOKEN_FILE}")
    print("Use a trusted HTTPS reverse proxy for remote production exposure.")
    server.serve_forever()
