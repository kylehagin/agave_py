import asyncio
import json
import logging
import random
import struct
import time
from collections import deque
from dataclasses import dataclass
from typing import Awaitable, Callable, Deque, Dict, Iterable, List, Optional, Set, Tuple

from .crypto import Keypair, sign, verify
from .transaction import Transaction
from .operations import RateLimiter, MetricsRegistry


# Gossip intervals tuned for a lightweight prototype; shortened so nodes quickly
# learn about each other and exchange data plane contact info.
GOSSIP_PUSH_INTERVAL = 1.0
GOSSIP_PULL_INTERVAL = 5.0
MAX_SEEN_CACHE = 512


@dataclass
class ContactInfo:
    """Signed contact info entry stored in the CRDS."""

    identity: str
    gossip_addr: Tuple[str, int]
    tpu_udp: Tuple[str, int]
    tpu_quic: Tuple[str, int]
    tvu: Tuple[str, int]
    stake_weight: float = 1.0
    wallclock: float
    signature: bytes

    def _payload(self) -> bytes:
        host, gossip_port = self.gossip_addr
        _, tpu_udp_port = self.tpu_udp
        _, tpu_quic_port = self.tpu_quic
        _, tvu_port = self.tvu
        wallclock_int = int(self.wallclock * 1000)
        return f"{self.identity}:{host}:{gossip_port}:{tpu_udp_port}:{tpu_quic_port}:{tvu_port}:{self.stake_weight}:{wallclock_int}".encode()

    def verify(self) -> bool:
        try:
            return verify(self._payload(), self.signature, bytes.fromhex(self.identity))
        except Exception:
            return False

    def to_dict(self) -> Dict[str, object]:
        return {
            "identity": self.identity,
            "gossip": [self.gossip_addr[0], self.gossip_addr[1]],
            "tpu_udp": [self.tpu_udp[0], self.tpu_udp[1]],
            "tpu_quic": [self.tpu_quic[0], self.tpu_quic[1]],
            "tvu": [self.tvu[0], self.tvu[1]],
            "stake": self.stake_weight,
            "wallclock": self.wallclock,
            "signature": self.signature.hex(),
        }

    @classmethod
    def from_dict(cls, raw: Dict[str, object]) -> "ContactInfo":
        return cls(
            identity=str(raw["identity"]),
            gossip_addr=(str(raw["gossip"][0]), int(raw["gossip"][1])),
            tpu_udp=(str(raw["tpu_udp"][0]), int(raw["tpu_udp"][1])),
            tpu_quic=(str(raw["tpu_quic"][0]), int(raw["tpu_quic"][1])),
            tvu=(str(raw["tvu"][0]), int(raw["tvu"][1])),
            stake_weight=float(raw.get("stake", 1.0)),
            wallclock=float(raw["wallclock"]),
            signature=bytes.fromhex(str(raw["signature"])),
        )

    @classmethod
    def create(
        cls,
        keypair: Keypair,
        host: str,
        gossip_port: int,
        tpu_udp_port: int,
        tpu_quic_port: int,
        tvu_port: int,
        stake_weight: float = 1.0,
    ) -> "ContactInfo":
        identity = keypair.public_key.hex()
        wallclock = time.time()
        stub = cls(
            identity=identity,
            gossip_addr=(host, gossip_port),
            tpu_udp=(host, tpu_udp_port),
            tpu_quic=(host, tpu_quic_port),
            tvu=(host, tvu_port),
            stake_weight=stake_weight,
            wallclock=wallclock,
            signature=b"",
        )
        signature = sign(stub._payload(), keypair)
        return cls(
            identity=identity,
            gossip_addr=stub.gossip_addr,
            tpu_udp=stub.tpu_udp,
            tpu_quic=stub.tpu_quic,
            tvu=stub.tvu,
            stake_weight=stake_weight,
            wallclock=wallclock,
            signature=signature,
        )


class CRDS:
    """Lightweight CRDS map for gossip contact info."""

    def __init__(self):
        self.entries: Dict[str, ContactInfo] = {}

    def update(self, info: ContactInfo) -> bool:
        if not info.verify():
            return False
        existing = self.entries.get(info.identity)
        if existing and existing.wallclock >= info.wallclock:
            return False
        self.entries[info.identity] = info
        return True

    def newest_wallclock(self) -> float:
        if not self.entries:
            return 0.0
        return max(e.wallclock for e in self.entries.values())

    def peers(self, exclude_identity: str | None = None) -> List[ContactInfo]:
        infos = list(self.entries.values())
        if exclude_identity is None:
            return infos
        return [c for c in infos if c.identity != exclude_identity]


class _GossipProtocol(asyncio.DatagramProtocol):
    def __init__(self, node: "GossipNode"):
        self.node = node

    def datagram_received(self, data: bytes, addr):
        if not data or data in self.node._seen or not self.node._allow_inbound():
            return
        if addr:
            host, port = addr[0], addr[1]
            self.node.add_peer(host, int(port))
        self.node._seen.append(data)
        self.node._loop.create_task(self.node._handle_payload(data, addr))


class GossipNode:
    """CRDS-backed gossip with pull/push mechanics and signed contact info."""

    def __init__(
        self,
        host: str,
        port: int,
        keypair: Keypair,
        on_message: Callable[[bytes], Awaitable[None]] | None = None,
        allowed_identities: Set[str] | None = None,
        max_packets_per_sec: int = 500,
        metrics: MetricsRegistry | None = None,
        logger: logging.Logger | None = None,
        stake_weight: float = 1.0,
    ):
        self.host = host
        self.port = port
        self.keypair = keypair
        self.identity = keypair.public_key.hex()
        self.peers: Set[tuple[str, int]] = set()
        self.tpu_peers: Set[Tuple[str, int]] = set()
        self.tvu_peers: Set[Tuple[str, int]] = set()
        self.transport: asyncio.DatagramTransport | None = None
        self._seen: Deque[bytes] = deque(maxlen=MAX_SEEN_CACHE)
        self._loop: asyncio.AbstractEventLoop | None = None
        self._on_message = on_message
        self._crds = CRDS()
        self._push_task: asyncio.Task | None = None
        self._pull_task: asyncio.Task | None = None
        self._rate_limiter = RateLimiter(max_packets_per_sec)
        self._allowed = set(allowed_identities) if allowed_identities else None
        self.metrics = metrics
        self.logger = logger or logging.getLogger(__name__)
        self._stake_weight = stake_weight

    async def start(self):
        self._loop = asyncio.get_running_loop()
        self.transport, _ = await self._loop.create_datagram_endpoint(
            lambda: _GossipProtocol(self), local_addr=(self.host, self.port)
        )
        await self.register_self()
        self._push_task = asyncio.create_task(self._push_loop())
        self._pull_task = asyncio.create_task(self._pull_loop())

    async def broadcast(self, data: bytes) -> None:
        if not self.transport:
            return
        for peer in list(self.peers):
            try:
                self.transport.sendto(data, peer)
            except Exception:
                pass

    async def _send_direct(self, data: bytes, addr: Tuple[str, int]) -> None:
        if not self.transport:
            return
        try:
            self.transport.sendto(data, addr)
        except Exception:
            pass

    def add_peer(self, host: str, port: int):
        """Add a peer to the gossip set."""
        self.peers.add((host, port))

    async def register_self(self, tpu_port: int | None = None, tpu_quic: int | None = None, tvu_port: int | None = None, stake_weight: float | None = None) -> None:
        """Broadcast this node's gossip, TPU, and TVU contact info."""

        tpu_port = tpu_port if tpu_port is not None else self.port + 1
        tpu_quic = tpu_quic if tpu_quic is not None else tpu_port + 1000
        tvu_port = tvu_port if tvu_port is not None else tpu_port + 1
        stake = self._stake_weight if stake_weight is None else stake_weight
        info = ContactInfo.create(self.keypair, self.host, self.port, tpu_port, tpu_quic, tvu_port, stake_weight=stake)
        self._crds.update(info)
        await self._broadcast_contact(info)

    def _refresh_peer_sets(self) -> None:
        peers = self._crds.peers()
        self.peers = {(c.gossip_addr[0], c.gossip_addr[1]) for c in peers if c.identity != self.identity}
        self.tpu_peers = {(c.tpu_udp[0], c.tpu_udp[1]) for c in peers if c.identity != self.identity}
        self.tvu_peers = {(c.tvu[0], c.tvu[1]) for c in peers if c.identity != self.identity}

    async def _broadcast_contact(self, info: ContactInfo) -> None:
        payload = json.dumps({"type": "contact", "contact": info.to_dict()}).encode()
        await self.broadcast(payload)

    async def _push_loop(self) -> None:
        while True:
            try:
                me = self._crds.entries.get(self.identity)
                if me is not None:
                    await self._broadcast_contact(me)
            except Exception:
                pass
            await asyncio.sleep(GOSSIP_PUSH_INTERVAL)

    async def _pull_loop(self) -> None:
        while True:
            if self.peers:
                peer = random.choice(list(self.peers))
                message = {
                    "type": "pull",
                    "since": self._crds.newest_wallclock(),
                    "from": self.identity,
                }
                await self._send_direct(json.dumps(message).encode(), peer)
            await asyncio.sleep(GOSSIP_PULL_INTERVAL)

    async def stop(self):
        if self._push_task:
            self._push_task.cancel()
        if self._pull_task:
            self._pull_task.cancel()
        if self.transport:
            self.transport.close()
            self.transport = None

    async def _handle_payload(self, data: bytes, addr: Optional[Tuple[str, int]] = None) -> None:
        try:
            message = json.loads(data.decode())
            mtype = message.get("type")
            if mtype == "contact":
                contact = ContactInfo.from_dict(message["contact"])
                if self._allowed is not None and contact.identity not in self._allowed:
                    return
                updated = self._crds.update(contact)
                if updated:
                    self._refresh_peer_sets()
                    if self.metrics:
                        self.metrics.incr("gossip_contacts")
                    await self.broadcast(data)
            elif mtype == "pull":
                since = float(message.get("since", 0))
                newer = [c.to_dict() for c in self._crds.entries.values() if c.wallclock > since]
                if newer and addr:
                    resp = json.dumps({"type": "pull_resp", "contacts": newer}).encode()
                    await self._send_direct(resp, addr)
            elif mtype == "pull_resp":
                changed = False
                for entry in message.get("contacts", []):
                    try:
                        contact = ContactInfo.from_dict(entry)
                        if self._allowed is not None and contact.identity not in self._allowed:
                            continue
                        if self._crds.update(contact):
                            changed = True
                    except Exception:
                        continue
                if changed:
                    self._refresh_peer_sets()
            else:
                await self._relay_application(data)
        except Exception:
            await self._relay_application(data)

    async def _relay_application(self, data: bytes) -> None:
        try:
            if self.metrics:
                self.metrics.incr("gossip_application_payloads")
            if self._on_message:
                await self._on_message(data)
            await self.broadcast(data)
        except Exception:
            # Best-effort gossip only; ignore malformed payloads
            pass

    def contacts(self) -> List[ContactInfo]:
        return self._crds.peers()

    def _allow_inbound(self) -> bool:
        allowed = self._rate_limiter.allow()
        if not allowed and self.logger:
            self.logger.warning("dropping gossip packet due to rate limit")
        if allowed and self.metrics:
            self.metrics.incr("gossip_packets")
        return allowed


@dataclass
class Shred:
    slot: int
    index: int
    parent_offset: int
    last_in_slot: bool
    data: bytes
    producer: str
    signature: bytes = b""

    HEADER = struct.Struct(">I I I ? I")

    def payload(self) -> bytes:
        producer_bytes = bytes.fromhex(self.producer)
        return self.HEADER.pack(
            self.slot,
            self.index,
            self.parent_offset,
            self.last_in_slot,
            len(self.data),
        ) + producer_bytes + self.data

    def to_bytes(self) -> bytes:
        return self.payload() + (self.signature or b"")

    def sign(self, keypair: Keypair) -> None:
        self.signature = sign(self.payload(), keypair)

    def verify(self) -> bool:
        if not self.signature:
            return False
        try:
            return verify(self.payload(), self.signature, bytes.fromhex(self.producer))
        except Exception:
            return False

    @classmethod
    def from_bytes(cls, raw: bytes) -> "Shred":
        header_size = cls.HEADER.size
        if len(raw) < header_size + 32:
            raise ValueError("shred truncated")
        slot, index, parent_offset, last_in_slot, data_len = cls.HEADER.unpack(raw[:header_size])
        producer_start = header_size
        producer_end = producer_start + 32
        producer_pk = raw[producer_start:producer_end]
        data_start = producer_end
        data_end = data_start + data_len
        if data_end > len(raw):
            raise ValueError("shred data truncated")
        data = raw[data_start:data_end]
        signature = raw[data_end:]
        return cls(
            slot=slot,
            index=index,
            parent_offset=parent_offset,
            last_in_slot=bool(last_in_slot),
            data=data,
            producer=producer_pk.hex(),
            signature=signature,
        )


def make_shreds(
    payload: bytes,
    slot: int,
    parent_slot: int | None,
    keypair: Keypair,
    shred_data_size: int = 900,
) -> List[Shred]:
    chunks = [payload[i : i + shred_data_size] for i in range(0, len(payload), shred_data_size)] or [b""]
    shreds: List[Shred] = []
    parent_offset = slot - parent_slot if parent_slot is not None else 0
    for idx, chunk in enumerate(chunks):
        shred = Shred(
            slot=slot,
            index=idx,
            parent_offset=parent_offset,
            last_in_slot=idx == len(chunks) - 1,
            data=chunk,
            producer=keypair.public_key.hex(),
        )
        shred.sign(keypair)
        shreds.append(shred)
    return shreds


class ShredAssembler:
    """Reassembles shreds per slot and surfaces repair hints."""

    def __init__(self):
        self.shreds: Dict[int, Dict[int, Shred]] = {}
        self.expected: Dict[int, int] = {}

    def add_shred(self, shred: Shred) -> tuple[bool, List[int] | None, bytes | None]:
        slot_map = self.shreds.setdefault(shred.slot, {})
        slot_map[shred.index] = shred
        if shred.last_in_slot:
            self.expected[shred.slot] = shred.index + 1
        expected = self.expected.get(shred.slot)
        if expected is not None:
            missing = [idx for idx in range(expected) if idx not in slot_map]
            if not missing:
                data = b"".join(slot_map[idx].data for idx in range(expected))
                return True, None, data
            return False, missing, None
        return False, None, None


def build_turbine_tree(identity: str, peers: Iterable[ContactInfo], fanout: int = 4) -> Dict[str, List[ContactInfo]]:
    ordered = sorted(
        [p for p in peers if p.identity != identity],
        key=lambda c: (-1 * c.stake_weight, c.identity),
    )
    mapping: Dict[str, List[ContactInfo]] = {identity: []}
    queue: Deque[str] = deque([identity])
    while ordered and queue:
        parent_identity = queue.popleft()
        mapping.setdefault(parent_identity, [])
        for _ in range(fanout):
            if not ordered:
                break
            child = ordered.pop(0)
            mapping[parent_identity].append(child)
            mapping.setdefault(child.identity, [])
            queue.append(child.identity)
    return mapping


class _DataPlaneProtocol(asyncio.DatagramProtocol):
    def __init__(self, plane: "DataPlane"):
        self.plane = plane

    def datagram_received(self, data: bytes, addr):
        if not data:
            return
        self.plane._loop.create_task(self.plane._handle_datagram(data, addr))


class DataPlane:
    """QUIC-like TPU/TVU data plane with turbine forwarding and repair."""

    def __init__(
        self,
        identity: Keypair,
        host: str,
        tvu_port: int,
        peer_provider: Callable[[], Iterable[ContactInfo]],
        on_recovered_payload: Callable[[int, bytes], Awaitable[None]] | None = None,
        fanout: int = 4,
        allowed_identities: Set[str] | None = None,
        max_packets_per_sec: int = 2000,
        metrics: MetricsRegistry | None = None,
        logger: logging.Logger | None = None,
    ):
        self.identity = identity.public_key.hex()
        self._keypair = identity
        self.host = host
        self.tvu_port = tvu_port
        self._peer_provider = peer_provider
        self._fanout = fanout
        self._transport: asyncio.DatagramTransport | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._assembler = ShredAssembler()
        self._seen: Set[Tuple[int, int, str]] = set()
        self._pending_repairs: Dict[Tuple[int, int], float] = {}
        self._on_recovered = on_recovered_payload
        self._allowed = set(allowed_identities) if allowed_identities else None
        self._rate_limiter = RateLimiter(max_packets_per_sec)
        self._egress_limiters: Dict[str, RateLimiter] = {}
        self.metrics = metrics
        self.logger = logger or logging.getLogger(__name__)

    async def start(self) -> None:
        self._loop = asyncio.get_running_loop()
        self._transport, _ = await self._loop.create_datagram_endpoint(
            lambda: _DataPlaneProtocol(self), local_addr=(self.host, self.tvu_port)
        )

    async def stop(self) -> None:
        if self._transport:
            self._transport.close()
            self._transport = None

    async def _handle_datagram(self, data: bytes, addr: Tuple[str, int]) -> None:
        if not self._rate_limiter.allow():
            if self.logger:
                self.logger.warning("dropping data plane packet due to rate limit")
            return
        try:
            message = json.loads(data.decode())
            mtype = message.get("type")
            forwarder = str(message.get("forwarder")) if message.get("forwarder") else None
            hop = int(message.get("hop", 0))
            if mtype == "shred":
                payload = bytes.fromhex(message["payload"])
                if not self._validate_forwarder(forwarder, message.get("auth"), payload, hop):
                    return
                shred = Shred.from_bytes(payload)
                await self._ingest_shred(shred, hop)
            elif mtype == "repair_req":
                payload = f"{message['slot']}:{message['index']}".encode()
                if not self._validate_forwarder(forwarder, message.get("auth"), payload, hop):
                    return
                slot = int(message["slot"])
                index = int(message["index"])
                await self._handle_repair_request(slot, index, addr)
            elif mtype == "repair_resp":
                payload = bytes.fromhex(message["payload"])
                if not self._validate_forwarder(forwarder, message.get("auth"), payload, hop):
                    return
                shred = Shred.from_bytes(payload)
                await self._ingest_shred(shred, hop)
        except Exception:
            # Ignore malformed payloads to keep the data plane resilient.
            pass

    def _validate_forwarder(self, forwarder: str | None, auth: str | None, payload: bytes, hop: int) -> bool:
        if forwarder is None or auth is None:
            return False
        if self._allowed is not None and forwarder not in self._allowed:
            return False
        try:
            return verify(payload + hop.to_bytes(4, "big"), bytes.fromhex(auth), bytes.fromhex(forwarder))
        except Exception:
            return False

    def _wrap_packet(self, packet_type: str, payload: bytes, hop: int, extra: dict | None = None) -> bytes:
        signature = sign(payload + hop.to_bytes(4, "big"), self._keypair)
        body = {
            "type": packet_type,
            "payload": payload.hex(),
            "hop": hop,
            "forwarder": self.identity,
            "auth": signature.hex(),
        }
        if extra:
            body.update(extra)
        return json.dumps(body).encode()

    async def _ingest_shred(self, shred: Shred, hop: int) -> None:
        key = (shred.slot, shred.index, shred.producer)
        if key in self._seen:
            return
        if self._allowed is not None and shred.producer not in self._allowed:
            return
        if not shred.verify():
            return
        self._seen.add(key)
        if self.metrics:
            self.metrics.incr("shreds_ingested")
        complete, missing, payload = self._assembler.add_shred(shred)
        if complete and payload is not None and self._on_recovered:
            await self._on_recovered(shred.slot, payload)
        elif missing:
            await self._request_repairs(shred.slot, missing)
        await self._forward_shred(shred, hop)

    def _send_with_qos(self, packet: bytes, contact: ContactInfo) -> None:
        limiter = self._egress_limiters.setdefault(contact.identity, RateLimiter(800))
        if not limiter.allow():
            if self.logger:
                self.logger.debug("dropping packet to %s due to egress QoS", contact.identity)
            return
        try:
            if self._transport:
                self._transport.sendto(packet, contact.tvu)
        except Exception:
            return

    async def _forward_shred(self, shred: Shred, hop: int) -> None:
        peers = list(self._peer_provider())
        if not peers:
            return
        tree = build_turbine_tree(self.identity, peers, self._fanout)
        children = tree.get(self.identity, [])
        packet = self._wrap_packet("shred", shred.to_bytes(), hop + 1)
        for child in children:
            self._send_with_qos(packet, child)
        if self.metrics:
            self.metrics.incr("shreds_forwarded")

    async def _request_repairs(self, slot: int, missing: List[int]) -> None:
        now = time.time()
        peers = list(self._peer_provider())
        if not peers:
            return
        for index in missing[: self._fanout]:
            key = (slot, index)
            last = self._pending_repairs.get(key, 0)
            if now - last < 1.0:
                continue
            self._pending_repairs[key] = now
            peer = random.choice(peers)
            payload = f"{slot}:{index}".encode()
            request = self._wrap_packet("repair_req", payload, 0, {"slot": slot, "index": index})
            self._send_with_qos(request, peer)
        if self.metrics:
            self.metrics.incr("repair_requests")

    async def _handle_repair_request(self, slot: int, index: int, addr: Tuple[str, int]) -> None:
        shred = self._assembler.shreds.get(slot, {}).get(index)
        if shred is None:
            return
        resp = self._wrap_packet("repair_resp", shred.to_bytes(), 0)
        try:
            if self._transport:
                self._transport.sendto(resp, addr)
        except Exception:
            pass
        else:
            if self.metrics:
                self.metrics.incr("repair_responses")

    async def broadcast_shreds(self, shreds: List[Shred]) -> None:
        if not shreds:
            return
        peers = list(self._peer_provider())
        tree = build_turbine_tree(self.identity, peers, self._fanout)
        first_hop = tree.get(self.identity, [])
        packet_cache: Dict[int, bytes] = {}
        for shred in shreds:
            packet_cache[shred.index] = self._wrap_packet("shred", shred.to_bytes(), 0)
            for peer in first_hop:
                self._send_with_qos(packet_cache[shred.index], peer)
        if self.metrics:
            self.metrics.incr("shreds_broadcast", len(shreds))


class _TPUProtocol(asyncio.DatagramProtocol):
    def __init__(
        self,
        on_transaction: Callable[[Transaction], asyncio.Future | asyncio.Task | None],
        loop: asyncio.AbstractEventLoop,
        rate_limiter: Callable[[], bool],
        metrics: MetricsRegistry | None = None,
    ):
        self._on_transaction = on_transaction
        self._loop = loop
        self._rate_limiter = rate_limiter
        self.metrics = metrics

    def datagram_received(self, data: bytes, addr):
        if not data or not self._rate_limiter():
            return
        tx = Transaction.from_bytes(data)
        if self.metrics:
            self.metrics.incr("tpu_packets")
        result = self._on_transaction(tx)
        if asyncio.iscoroutine(result):
            self._loop.create_task(result)


class TPUReceiver:
    def __init__(
        self,
        host: str,
        port: int,
        on_transaction: Callable[[Transaction], asyncio.Future | asyncio.Task | None],
        max_packets_per_sec: int = 500,
        metrics: MetricsRegistry | None = None,
    ):
        self.host = host
        self.port = port
        self._transport: asyncio.DatagramTransport | None = None
        self._protocol: _TPUProtocol | None = None
        self._on_transaction = on_transaction
        self._max_rate = max_packets_per_sec
        self._arrival_window: Deque[float] = deque()
        self.metrics = metrics

    def _allow_packet(self) -> bool:
        now = time.time()
        self._arrival_window.append(now)
        cutoff = now - 1.0
        while self._arrival_window and self._arrival_window[0] < cutoff:
            self._arrival_window.popleft()
        return len(self._arrival_window) <= self._max_rate

    async def start(self):
        loop = asyncio.get_running_loop()
        self._protocol = _TPUProtocol(self._on_transaction, loop, self._allow_packet, metrics=self.metrics)
        self._transport, _ = await loop.create_datagram_endpoint(
            lambda: self._protocol, local_addr=(self.host, self.port)
        )

    async def stop(self):
        if self._transport:
            self._transport.close()
            self._transport = None
