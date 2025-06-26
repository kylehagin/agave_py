import asyncio
from .fast_utils import fast_hash

class Validator:
    def __init__(self):
        self.blocks = []

    async def validate_block(self, block_data: bytes) -> int:
        """Validate a block and return its hash."""
        block_hash = fast_hash(block_data)
        self.blocks.append(block_hash)
        return block_hash

async def main():
    v = Validator()
    data = b"example block"
    h = await v.validate_block(data)
    print("Validated block hash:", h)

if __name__ == "__main__":
    asyncio.run(main())
