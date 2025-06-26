import asyncio
from .fast_utils import fast_hash
from .crypto import generate_keypair, sign, verify, poh_hash
from .ledger import Ledger
from .network import GossipNode
from .rpc import RPCServer
from .transaction import Transaction

class Validator:
    def __init__(self, host: str = "127.0.0.1", port: int = 8000, rpc_port: int = 8899):
        """Initialize the validator with networking and RPC endpoints."""
        self.ledger = Ledger()
        self.node = GossipNode(host, port)
        self.rpc = RPCServer(self.ledger, host, rpc_port)
        self.blocks = []
        self.prev_hash = b"0" * 32
        self.keypair = generate_keypair()

    async def start(self):
        await self.node.start()
        self.rpc.start()

    async def stop(self):
        if self.rpc:
            self.rpc.stop()

    def add_peer(self, host: str, port: int):
        self.node.add_peer(host, port)

    async def validate_block(self, block_data: bytes) -> bytes:
        block_hash = fast_hash(block_data)
        poh = poh_hash(self.prev_hash, block_hash.to_bytes(8, "big"))
        self.prev_hash = poh
        self.blocks.append(poh)
        return poh

    async def process_transaction(self, tx: Transaction):
        if self.ledger.process_transaction(tx):
            msg = f"TX:{tx.sender}->{tx.receiver}:{tx.amount}".encode()
            await self.node.broadcast(msg)

async def main():
    v = Validator()
    await v.start()
    tx = Transaction.create(v.keypair, "receiver", 10)
    await v.process_transaction(tx)
    h = await v.validate_block(b"example block")
    print("PoH hash:", h.hex())

if __name__ == "__main__":
    asyncio.run(main())
