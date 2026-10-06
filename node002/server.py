import json
import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from provider import Node002Provider
from x_observer import XObserverAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

ROOT=Path(__file__).parent
TOKEN_FILE=ROOT/"provider-token.txt"
provider=Node002Provider()
provider.adapter=XObserverAdapter()
if os.getenv("NODE002_PROVIDER_TOKEN"):
    provider.token=os.environ["NODE002_PROVIDER_TOKEN"]
elif TOKEN_FILE.exists():
    provider.token=TOKEN_FILE.read_text().strip()
else:
    TOKEN_FILE.write_text(provider.token+"\n")

def send(handler,status,payload):
    body=json.dumps(payload).encode()
    handler.send_response(status)
    handler.send_header("Content-Type","application/json")
    handler.send_header("Content-Length",str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)

class Handler(BaseHTTPRequestHandler):
    def authorized(self):
        return self.headers.get("Authorization")==f"Bearer {provider.token}"

    def read_json(self):
        try:
            value=json.loads(self.rfile.read(int(self.headers.get("Content-Length","0"))))
            return value if isinstance(value,dict) else None
        except (ValueError,json.JSONDecodeError):
            return None

    def do_GET(self):
        if not self.authorized():
            return send(self,401,{"error":{"code":"UNAUTHORIZED","message":"Bearer token is invalid."}})
        parts=self.path.strip("/").split("/")
        if len(parts)==2 and parts[0]=="jobs":
            status,payload=provider.status(parts[1])
            return send(self,status,payload)
        if len(parts)==3 and parts[0]=="jobs" and parts[2]=="result":
            status,payload=provider.result(parts[1])
            return send(self,status,payload)
        send(self,404,{"error":{"code":"NOT_FOUND","message":"Endpoint not found."}})

    def do_POST(self):
        if self.path!="/jobs":
            return send(self,404,{"error":{"code":"NOT_FOUND","message":"Endpoint not found."}})
        if not self.authorized():
            return send(self,401,{"error":{"code":"UNAUTHORIZED","message":"Bearer token is invalid."}})
        request=self.read_json()
        if request is None:
            return send(self,400,{"error":{"code":"INVALID_JSON","message":"Request body must be a JSON object."}})
        status,payload=provider.submit(request)
        send(self,status,payload)

    def log_message(self,fmt,*args):
        print(fmt%args)

if __name__=="__main__":
    host=os.getenv("PROVIDER_HOST","127.0.0.1")
    port=int(os.getenv("PROVIDER_PORT","8010"))
    print(f"DRAYN Node 002 listening at http://{host}:{port}")
    ThreadingHTTPServer((host,port),Handler).serve_forever()
