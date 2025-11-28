import asyncio
import json
import logging
from pathlib import Path
from .consensus import Consensus
from .crypto import Keypair, load_or_create_keypair
from .ledger import Ledger
from .network import DataPlane, GossipNode, TPUReceiver, make_shreds
from .persistence import SnapshotManager
from .poh import BlockProducer, LeaderSchedule, PoHRecorder
from .rpc import RPCServer
from .transaction import Transaction
from .operations import MetricsRegistry, HealthMonitor, setup_logging

class Validator:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        rpc_port: int = 8899,
        tpu_port: int = 8001,
        tvu_port: int = 8002,
        tpu_quic_port: int = 9001,
        ledger_dir: str = "validator_ledger",
        full_snapshot_interval: int = 200,
        incremental_snapshot_interval: int = 25,
        allowed_peers: list[str] | None = None,
        gossip_rate_limit: int = 750,
        tvu_rate_limit: int = 2500,
        tpu_rate_limit: int = 750,
    ):
        """Initialize the validator with networking, TPU, TVU, and RPC endpoints."""
        setup_logging()
        self.logger = logging.getLogger(__name__)
        self.metrics = MetricsRegistry()
        self.health = HealthMonitor(self.metrics)
        self.keypair: Keypair = load_or_create_keypair(Path(ledger_dir) / "validator-keypair.json")
        self.vote_keypair: Keypair = load_or_create_keypair(Path(ledger_dir) / "vote-keypair.json")
        self.stake_keypair: Keypair = load_or_create_keypair(Path(ledger_dir) / "stake-keypair.json")
        self.identity = self.keypair.public_key.hex()
        self.snapshot_manager = SnapshotManager(
            base_dir=ledger_dir,
            full_snapshot_interval=full_snapshot_interval,
            incremental_snapshot_interval=incremental_snapshot_interval,
            signing_keypair=self.keypair,
            expected_authority=self.identity,
        )
        bootstrap = self.snapshot_manager.bootstrap()
        if bootstrap:
            slot, self.ledger, self.consensus, self.poh = bootstrap
            self.current_slot = slot + 1
            self.consensus.identity = self.identity
            self.consensus.stake = 1
        else:
            self.ledger = Ledger()
            self.consensus = Consensus(identity=self.identity, stake=1)
            self.current_slot = 1
            self.poh = PoHRecorder()
        self.ledger.enable_persistence(Path(ledger_dir) / "records")
        # Seed the identity with lamports so it can pay fees and transfers.
        if self.identity not in self.ledger.bank.accounts:
            self.ledger.bank.ensure_account(self.identity, lamports=1_000_000_000)
        self.tpu_port = tpu_port
        self.tvu_port = tvu_port
        self.tpu_quic_port = tpu_quic_port
        self.allowed_peers = set(allowed_peers) if allowed_peers else None
        if self.allowed_peers is not None:
            self.allowed_peers.add(self.identity)
        self.node = GossipNode(
            host,
            port,
            self.keypair,
            self.handle_gossip_payload,
            allowed_identities=self.allowed_peers,
            max_packets_per_sec=gossip_rate_limit,
            metrics=self.metrics,
            logger=self.logger,
            stake_weight=self.consensus.stake,
        )
        self.tpu = TPUReceiver(host, tpu_port, self.process_transaction, max_packets_per_sec=tpu_rate_limit, metrics=self.metrics)
        self.data_plane = DataPlane(
            self.keypair,
            host,
            tvu_port,
            peer_provider=self.node.contacts,
            on_recovered_payload=self.handle_recovered_block,
            allowed_identities=self.allowed_peers,
            max_packets_per_sec=tvu_rate_limit,
            metrics=self.metrics,
            logger=self.logger,
        )
        schedule = LeaderSchedule({self.identity: float(self.consensus.stake)})
        self.block_producer = BlockProducer(
            self.register_block,
            self.poh,
            leader_schedule=[leader for leader in schedule._ordered],
            identity=self.identity,
        )
        self.rpc = RPCServer(self, host, rpc_port)

    async def start(self):
        await self.node.start()
        # Refresh the CRDS entry with the actual TPU/TVU endpoints.
        await self.node.register_self(self.tpu_port, self.tpu_quic_port, self.tvu_port, stake_weight=self.consensus.stake)
        await self.tpu.start()
        await self.data_plane.start()
        await self.block_producer.start()
        self.rpc.start()

    async def stop(self):
        if self.rpc:
            self.rpc.stop()
        if self.block_producer:
            await self.block_producer.stop()
        if self.tpu:
            await self.tpu.stop()
        if self.data_plane:
            await self.data_plane.stop()
        if self.node:
            await self.node.stop()

    def add_peer(self, host: str, port: int):
        self.node.add_peer(host, port)

    async def register_on_gossip(self):
        """Publish this node to existing peers so they learn our TPU/TVU endpoints."""
        await self.node.register_self(self.tpu_port, self.tpu_quic_port, self.tvu_port, stake_weight=self.consensus.stake)

    async def register_block(self, blockhash: bytes, num_hashes: int, parent: str | None, transactions: list[Transaction]):
        blockhash_hex = blockhash.hex()
        parent_hash = parent or self.consensus.best_blockhash()
        self.ledger.record_block(self.current_slot, blockhash_hex, parent_hash, num_hashes, transactions)
        self.consensus.register_block(self.current_slot, blockhash_hex, parent_hash)
        self.consensus.record_vote(self.identity, blockhash_hex, stake=self.consensus.stake, slot=self.current_slot)
        self.health.record_block(self.current_slot)
        gossip_parent = parent_hash if parent_hash is not None else "None"
        await self.node.broadcast(f"BLOCK {self.current_slot} {blockhash_hex} {gossip_parent}".encode())
        await self.node.broadcast(self.consensus.vote_message(self.identity, self.current_slot, blockhash_hex))
        block_payload = json.dumps(
            {
                "slot": self.current_slot,
                "blockhash": blockhash_hex,
                "parent": gossip_parent,
                "hash_height": num_hashes,
                "transactions": [tx.to_bytes().hex() for tx in transactions],
            }
        ).encode()
        parent_slot = self.ledger.block_slots.get(parent_hash, self.current_slot - 1 if parent_hash else 0)
        shreds = make_shreds(block_payload, self.current_slot, parent_slot, self.keypair)
        await self.data_plane.broadcast_shreds(shreds)
        self.snapshot_manager.persist_block(self.current_slot, blockhash_hex, parent_hash, num_hashes, transactions)
        self.snapshot_manager.maybe_snapshot(self.current_slot, self.ledger, self.consensus, self.poh)
        if self.rpc:
            self.rpc.notify_slot(self.current_slot)
            for tx in transactions:
                if tx.signature:
                    self.rpc.notify_signature(tx.signature.hex(), self.current_slot, blockhash_hex)
        self.current_slot += 1

    async def process_transaction(self, tx: Transaction):
        accepted = self.ledger.process_transaction(tx)
        self.health.record_transaction(accepted)
        if accepted:
            self.block_producer.record_transaction(tx)
            await self.broadcast_transaction(tx)
            return True
        return False

    def latest_blockhash(self) -> str:
        return self.consensus.best_blockhash() or self.ledger.recent_blockhashes[-1]

    async def handle_gossip_payload(self, data: bytes):
        try:
            if data.startswith(b"VOTE"):
                _, voter, slot, blockhash = data.decode().split()
                slot_int = int(slot)
                self.consensus.record_vote(voter, blockhash, slot=slot_int)
            elif data.startswith(b"BLOCK"):
                _, slot, blockhash, parent = data.decode().split()
                slot_int = int(slot)
                parent_hash = parent if parent != "None" else None
                self.ledger.register_blockhash(blockhash, slot_int, parent_hash)
                self.consensus.register_block(slot_int, blockhash, parent_hash)
            self.health.record_gossip()
        except Exception:
            # Ignore malformed gossip payloads to keep the node resilient.
            pass

    async def broadcast_transaction(self, tx: Transaction):
        """Send a transaction to all known TPU peers discovered via gossip."""
        loop = asyncio.get_running_loop()
        for peer in list(self.node.tpu_peers):
            if peer == (self.node.host, self.tpu_port):
                continue
            try:
                transport, _ = await loop.create_datagram_endpoint(
                    lambda: asyncio.DatagramProtocol(), remote_addr=peer
                )
                transport.sendto(tx.to_bytes())
                transport.close()
            except Exception:
                # Ignore unreachable peers; gossip may introduce stale entries
                pass

    async def handle_recovered_block(self, slot: int, payload: bytes) -> None:
        """Reassemble a block from shreds and register it locally."""

        try:
            block = json.loads(payload.decode())
        except Exception:
            return
        blockhash = block.get("blockhash")
        parent = block.get("parent")
        if not isinstance(blockhash, str):
            return
        parent_hash = parent if isinstance(parent, str) else None
        transactions = []
        for raw in block.get("transactions", []):
            try:
                tx_bytes = bytes.fromhex(raw)
                transactions.append(Transaction.from_bytes(tx_bytes))
            except Exception:
                continue
        self.ledger.record_block(slot, blockhash, parent_hash, block.get("hash_height"), transactions)
        self.consensus.register_block(slot, blockhash, parent_hash)
        for tx in transactions:
            self.ledger.process_transaction(tx)
            if self.rpc and tx.signature:
                self.rpc.notify_signature(tx.signature.hex(), slot, blockhash)
        if self.rpc:
            self.rpc.notify_slot(slot)
        self.snapshot_manager.persist_block(slot, blockhash, parent_hash, block.get("hash_height"), transactions)
        self.snapshot_manager.maybe_snapshot(slot, self.ledger, self.consensus, self.poh)

async def main():
    v = Validator()
    await v.start()
    tx = Transaction.create(v.keypair, "receiver", 10, v.latest_blockhash())
    await v.process_transaction(tx)
    await asyncio.sleep(1)
    print("Latest blockhash:", v.latest_blockhash())

if __name__ == "__main__":
    asyncio.run(main())
