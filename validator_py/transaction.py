from dataclasses import dataclass
from .crypto import SimpleKeypair, sign

@dataclass
class Transaction:
    sender: str
    receiver: str
    amount: int
    signature: bytes

    @classmethod
    def create(cls, sender_kp: SimpleKeypair, receiver: str, amount: int) -> "Transaction":
        payload = f"{sender_kp.public_key.hex()}->{receiver}:{amount}".encode()
        signature = sign(payload, sender_kp)
        return cls(sender_kp.public_key.hex(), receiver, amount, signature)
