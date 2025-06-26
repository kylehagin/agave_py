import asyncio
from typing import Set

class GossipNode:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.peers: Set[tuple[str, int]] = set()
        self.server = None

    async def start(self):
        self.server = await asyncio.start_server(self.handle_conn, self.host, self.port)
        await self.server.start_serving()

    async def handle_conn(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        data = await reader.read(1024)
        writer.close()
        await writer.wait_closed()
        await self.broadcast(data)

    async def broadcast(self, data: bytes) -> None:
        for peer in list(self.peers):
            try:
                r, w = await asyncio.open_connection(*peer)
                w.write(data)
                await w.drain()
                w.close()
                await w.wait_closed()
            except Exception:
                pass

    def add_peer(self, host: str, port: int):
        """Add a peer to the gossip set."""
        self.peers.add((host, port))
