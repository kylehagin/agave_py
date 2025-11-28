import asyncio
import base64
import asyncio
import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

try:
    import websockets
except ImportError:  # pragma: no cover - dependency documented in requirements
    websockets = None

from .transaction import Transaction


def _jsonrpc_error(code: int, message: str, _id=None):
    return {"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": _id}


def _jsonrpc_result(result, _id=None):
    return {"jsonrpc": "2.0", "result": result, "id": _id}


class WebSocketRPC:
    """Minimal websocket server for Solana-style subscriptions."""

    def __init__(self, validator, host: str = "127.0.0.1", port: int = 8900):
        self.validator = validator
        self.host = host
        self.port = port
        self.loop: asyncio.AbstractEventLoop | None = None
        self.thread: threading.Thread | None = None
        self.server = None
        self._slot_subs: dict[int, websockets.WebSocketServerProtocol] = {}
        self._sig_subs: dict[int, tuple[str, websockets.WebSocketServerProtocol]] = {}
        self._next_id = 1

    async def _handler(self, websocket):
        try:
            async for message in websocket:
                try:
                    payload = json.loads(message)
                except Exception:
                    await websocket.send(json.dumps(_jsonrpc_error(-32700, "Invalid JSON", None)))
                    continue
                method = payload.get("method")
                pid = payload.get("id")
                params = payload.get("params", [])
                if method == "slotSubscribe":
                    sub_id = self._next_id
                    self._next_id += 1
                    self._slot_subs[sub_id] = websocket
                    await websocket.send(json.dumps(_jsonrpc_result(sub_id, pid)))
                    await websocket.send(
                        json.dumps(
                            {
                                "jsonrpc": "2.0",
                                "method": "slotNotification",
                                "params": {"result": {"slot": self.validator.current_slot - 1}, "subscription": sub_id},
                            }
                        )
                    )
                elif method == "signatureSubscribe":
                    sig = params[0] if params else None
                    if not isinstance(sig, str):
                        await websocket.send(json.dumps(_jsonrpc_error(-32602, "Invalid signature", pid)))
                        continue
                    sub_id = self._next_id
                    self._next_id += 1
                    self._sig_subs[sub_id] = (sig, websocket)
                    await websocket.send(json.dumps(_jsonrpc_result(sub_id, pid)))
                    status = self.validator.ledger.get_transaction_status(sig)
                    if status and status.get("slot") is not None:
                        await websocket.send(
                            json.dumps(
                                {
                                    "jsonrpc": "2.0",
                                    "method": "signatureNotification",
                                    "params": {
                                        "result": {"err": status.get("err"), "slot": status.get("slot")},
                                        "subscription": sub_id,
                                    },
                                }
                            )
                        )
                else:
                    await websocket.send(json.dumps(_jsonrpc_error(-32601, "Method not found", pid)))
        finally:
            dead = [sid for sid, ws in self._slot_subs.items() if ws is websocket]
            for sid in dead:
                self._slot_subs.pop(sid, None)
            dead = [sid for sid, (sig, ws) in self._sig_subs.items() if ws is websocket]
            for sid in dead:
                self._sig_subs.pop(sid, None)

    def start(self):
        if websockets is None:
            return

        def _run():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.server = self.loop.run_until_complete(websockets.serve(self._handler, self.host, self.port))
            self.loop.run_forever()

        self.thread = threading.Thread(target=_run, daemon=True)
        self.thread.start()

    def stop(self):
        if websockets is None or not self.loop:
            return
        if self.server:
            self.loop.call_soon_threadsafe(self.server.close)
        self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread:
            self.thread.join()

    def notify_slot(self, slot: int):
        if not self.loop:
            return
        for sub_id, ws in list(self._slot_subs.items()):
            asyncio.run_coroutine_threadsafe(
                ws.send(
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "method": "slotNotification",
                            "params": {"result": {"slot": slot}, "subscription": sub_id},
                        }
                    )
                ),
                self.loop,
            )

    def notify_signature(self, signature: str, slot: int, blockhash: str):
        if not self.loop:
            return
        for sub_id, (sig, ws) in list(self._sig_subs.items()):
            if sig != signature:
                continue
            asyncio.run_coroutine_threadsafe(
                ws.send(
                    json.dumps(
                        {
                            "jsonrpc": "2.0",
                            "method": "signatureNotification",
                            "params": {
                                "result": {"err": None, "slot": slot, "blockhash": blockhash},
                                "subscription": sub_id,
                            },
                        }
                    )
                ),
                self.loop,
            )


class RPCHandler(BaseHTTPRequestHandler):
    validator = None
    auth_token: str | None = None

    def _write_json(self, obj, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def _schedule(self, coro):
        loop = getattr(self.validator.node, "_loop", None)
        if loop and loop.is_running():
            return asyncio.run_coroutine_threadsafe(coro, loop).result()
        return asyncio.run(coro)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/balance":
            params = parse_qs(parsed.query)
            acct = params.get("account", [None])[0]
            if acct is None:
                self._write_json({"error": "missing account"}, 400)
                return
            bal = self.validator.ledger.get_balance(acct)
            self._write_json({"balance": bal})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        data = self.rfile.read(content_length or 0)
        token = self.headers.get("X-Validator-Auth")
        if self.auth_token and token != self.auth_token:
            self._write_json(_jsonrpc_error(-32000, "unauthorized"), 401)
            return
        try:
            body = json.loads(data.decode())
        except Exception:
            self._write_json({"error": "invalid json"}, 400)
            return

        method = body.get("method")
        params = body.get("params", [])
        rid = body.get("id")

        if method in ("getRecentBlockhash", "getLatestBlockhash"):
            blockhash = self.validator.latest_blockhash()
            slot = self.validator.ledger.block_slots.get(blockhash, self.validator.current_slot - 1)
            result = {
                "context": {"slot": slot},
                "value": {"blockhash": blockhash, "lastValidBlockHeight": slot + 150},
            }
            self._write_json(_jsonrpc_result(result, rid))
            return

        if method == "getHealth":
            healthy, reason = self.validator.health.status()
            if healthy:
                self._write_json(_jsonrpc_result("ok", rid))
            else:
                self._write_json(_jsonrpc_error(-32001, reason, rid), 503)
            return

        if method == "getVersion":
            self._write_json(_jsonrpc_result({"solana-core": "validator_py prototype"}, rid))
            return

        if method == "getMetrics":
            snapshot = self.validator.metrics.snapshot()
            self._write_json(_jsonrpc_result(snapshot, rid))
            return

        if method == "getSlot":
            self._write_json(_jsonrpc_result(self.validator.current_slot - 1, rid))
            return

        if method == "getBlockHeight":
            self._write_json(_jsonrpc_result(self.validator.current_slot - 1, rid))
            return

        if method == "getBalance":
            account = None
            if isinstance(params, list) and params:
                account = params[0]
            elif isinstance(params, dict):
                account = params.get("account")
            if not isinstance(account, str):
                self._write_json(_jsonrpc_error(-32602, "Invalid account", rid))
                return
            bal = self.validator.ledger.get_balance(account)
            commitment = None
            if isinstance(params, dict):
                opts = params.get("commitment")
                commitment = opts if isinstance(opts, str) else None
            result = {"context": {"slot": self.validator.current_slot - 1, "commitment": commitment or "processed"}, "value": bal}
            self._write_json(_jsonrpc_result(result, rid))
            return

        if method == "getAccountInfo":
            account = params[0] if isinstance(params, list) and params else None
            if not isinstance(account, str):
                self._write_json(_jsonrpc_error(-32602, "Invalid account", rid))
                return
            acc = self.validator.ledger.bank.accounts.get(account)
            value = None
            if acc:
                value = {
                    "lamports": acc.lamports,
                    "owner": acc.owner.hex(),
                    "data": [base64.b64encode(acc.data).decode(), "base64"],
                    "executable": acc.executable,
                    "rentEpoch": 0,
                }
            self._write_json(_jsonrpc_result({"context": {"slot": self.validator.current_slot - 1}, "value": value}, rid))
            return

        if method == "getProgramAccounts":
            if isinstance(params, list) and params:
                program_id = params[0]
                config = params[1] if len(params) > 1 else {}
            elif isinstance(params, dict):
                program_id = params.get("programId")
                config = params
            else:
                self._write_json(_jsonrpc_error(-32602, "Invalid params", rid))
                return
            if not isinstance(program_id, str):
                self._write_json(_jsonrpc_error(-32602, "Invalid program id", rid))
                return
            filters = config.get("filters", []) if isinstance(config, dict) else []
            results = []
            for pubkey, acc in self.validator.ledger.bank.accounts.items():
                if acc.owner.hex() != program_id:
                    continue
                match = True
                for f in filters:
                    if isinstance(f, dict) and "memcmp" in f:
                        mem = f["memcmp"]
                        offset = mem.get("offset", 0)
                        expected = mem.get("bytes", "")
                        try:
                            expected_bytes = base64.b64decode(expected)
                        except Exception:
                            expected_bytes = expected.encode()
                        if acc.data[offset : offset + len(expected_bytes)] != expected_bytes:
                            match = False
                            break
                if not match:
                    continue
                results.append({
                    "pubkey": pubkey,
                    "account": {
                        "lamports": acc.lamports,
                        "owner": acc.owner.hex(),
                        "data": [base64.b64encode(acc.data).decode(), "base64"],
                        "executable": acc.executable,
                        "rentEpoch": 0,
                    },
                })
            self._write_json(_jsonrpc_result({"context": {"slot": self.validator.current_slot - 1}, "value": results}, rid))
            return

        if method == "requestAirdrop":
            if not (isinstance(params, list) and len(params) >= 2):
                self._write_json(_jsonrpc_error(-32602, "Invalid params", rid))
                return
            account, amount = params[0], params[1]
            try:
                amount_int = int(amount)
            except (TypeError, ValueError):
                self._write_json(_jsonrpc_error(-32602, "Invalid amount", rid))
                return
            self.validator.ledger.bank.ensure_account(account, lamports=self.validator.ledger.bank.get_balance(account) + amount_int)
            sig = f"airdrop-{account}-{self.validator.current_slot}"
            self.validator.ledger.tx_status[sig] = {"slot": self.validator.current_slot - 1, "err": None, "blockhash": self.validator.latest_blockhash()}
            self._write_json(_jsonrpc_result(sig, rid))
            return

        if method == "sendTransaction":
            tx_payload = None
            if isinstance(params, list) and params:
                tx_payload = params[0]
            else:
                tx_payload = body.get("transaction")

            tx: Transaction
            if isinstance(tx_payload, str):
                try:
                    raw = base64.b64decode(tx_payload)
                except Exception:
                    self._write_json(_jsonrpc_error(-32602, "Invalid transaction encoding", rid))
                    return
                tx = Transaction.from_bytes(raw)
            elif isinstance(tx_payload, dict):
                signature = tx_payload.get("signature")
                signature_bytes = None
                try:
                    if isinstance(signature, str):
                        signature_bytes = bytes.fromhex(signature)
                except ValueError:
                    pass
                tx = Transaction(
                    sender=tx_payload.get("sender"),
                    receiver=tx_payload.get("receiver"),
                    amount=tx_payload.get("amount"),
                    signature=signature_bytes,
                    recent_blockhash=tx_payload.get("recent_blockhash"),
                )
                if tx.amount is not None:
                    try:
                        tx.amount = int(tx.amount)
                    except ValueError:
                        self._write_json(_jsonrpc_error(-32602, "invalid amount"), 400)
                        return
            else:
                self._write_json(_jsonrpc_error(-32602, "Unsupported transaction payload", rid))
                return

            try:
                accepted = self._schedule(self.validator.process_transaction(tx))
            except Exception:
                accepted = False
            if accepted:
                sig_hex = tx.signature.hex() if tx.signature else None
                self._write_json(_jsonrpc_result(sig_hex, rid))
            else:
                self._write_json(_jsonrpc_error(-32002, "Transaction rejected", rid))
            return

        if method == "getBlock":
            slot = params[0] if isinstance(params, list) and params else None
            try:
                slot_int = int(slot)
            except (TypeError, ValueError):
                self._write_json(_jsonrpc_error(-32602, "Invalid slot", rid))
                return
            block = self.validator.ledger.get_block(slot_int)
            if not block:
                self._write_json(_jsonrpc_error(-32004, "Block not available", rid))
                return
            parent_slot = self.validator.ledger.block_slots.get(block.get("parent"), slot_int - 1)
            result = {
                "blockhash": block.get("blockhash"),
                "previousBlockhash": block.get("previousBlockhash"),
                "parentSlot": parent_slot,
                "transactions": block.get("transactions", []),
                "blockHeight": slot_int,
            }
            self._write_json(_jsonrpc_result(result, rid))
            return

        if method == "getTransaction":
            signature = params[0] if isinstance(params, list) and params else None
            if not isinstance(signature, str):
                self._write_json(_jsonrpc_error(-32602, "Invalid signature", rid))
                return
            status = self.validator.ledger.get_transaction_status(signature)
            if not status:
                self._write_json(_jsonrpc_error(-32005, "Transaction not found", rid))
                return
            tx = status.get("transaction")
            wire = tx.to_bytes().hex() if tx else None
            result = {
                "slot": status.get("slot"),
                "meta": {"err": status.get("err")},
                "transaction": wire,
                "blockhash": status.get("blockhash"),
                "confirmationStatus": "finalized" if status.get("slot") and status.get("slot") <= self.validator.consensus.root else "processed",
            }
            self._write_json(_jsonrpc_result(result, rid))
            return

        self._write_json(_jsonrpc_error(-32601, "Method not found", rid))

class RPCServer:
    def __init__(self, validator, host="127.0.0.1", port=8899, ws_port: int | None = 8900):
        self.validator = validator
        self.host = host
        self.port = port
        self.httpd = None
        self.thread = None
        self.websocket = WebSocketRPC(validator, host, ws_port) if ws_port else None
        self.auth_token = None

    def start(self):
        handler = type("_H", (RPCHandler,), {"validator": self.validator, "auth_token": self.auth_token})
        self.httpd = HTTPServer((self.host, self.port), handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        if self.websocket:
            self.websocket.start()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            if self.thread:
                self.thread.join()
        if self.websocket:
            self.websocket.stop()

    def notify_slot(self, slot: int):
        if self.websocket:
            self.websocket.notify_slot(slot)

    def notify_signature(self, signature: str, slot: int, blockhash: str):
        if self.websocket:
            self.websocket.notify_signature(signature, slot, blockhash)
