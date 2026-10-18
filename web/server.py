import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LOG_FILE = os.environ.get("LOG_FILE", "/data/catcher.log")
STATUS_FILE = os.environ.get("STATUS_FILE", "/data/status")
WEB_PORT = int(os.environ.get("WEB_PORT", "8090"))
INDEX = Path(__file__).parent / "index.html"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            body, ctype = INDEX.read_bytes(), "text/html; charset=utf-8"
        elif self.path == "/log":
            try:
                body = Path(LOG_FILE).read_bytes()
            except FileNotFoundError:
                body = b"waiting for first attempt...\n"
            ctype = "text/plain; charset=utf-8"
        elif self.path == "/status":
            try:
                status = Path(STATUS_FILE).read_text().strip() or "starting"
            except FileNotFoundError:
                status = "starting"
            body = json.dumps({"status": status}).encode()
            ctype = "application/json"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


ThreadingHTTPServer(("0.0.0.0", WEB_PORT), Handler).serve_forever()
