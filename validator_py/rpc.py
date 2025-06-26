import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

class RPCHandler(BaseHTTPRequestHandler):
    ledger = None

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/balance":
            params = parse_qs(parsed.query)
            acct = params.get("account", [None])[0]
            if acct is None:
                self.send_response(400)
                self.end_headers()
                return
            bal = self.ledger.get_balance(acct)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"balance": bal}).encode())
        else:
            self.send_response(404)
            self.end_headers()

class RPCServer:
    def __init__(self, ledger, host="127.0.0.1", port=8899):
        self.ledger = ledger
        self.host = host
        self.port = port
        self.httpd = None
        self.thread = None

    def start(self):
        handler = type("_H", (RPCHandler,), {"ledger": self.ledger})
        self.httpd = HTTPServer((self.host, self.port), handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.thread.join()
