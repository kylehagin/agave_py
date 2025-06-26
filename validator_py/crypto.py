import hashlib
import hmac
import os

class SimpleKeypair:
    def __init__(self, private_key: bytes):
        self.private_key = private_key
        self.public_key = private_key  # Placeholder for symmetric key

def generate_keypair() -> SimpleKeypair:
    return SimpleKeypair(os.urandom(32))

def sign(message: bytes, keypair: SimpleKeypair) -> bytes:
    return hmac.new(keypair.private_key, message, hashlib.sha256).digest()

def verify(message: bytes, signature: bytes, keypair: SimpleKeypair) -> bool:
    expected = hmac.new(keypair.private_key, message, hashlib.sha256).digest()
    return hmac.compare_digest(expected, signature)


def poh_hash(prev_hash: bytes, data: bytes) -> bytes:
    return hashlib.sha256(prev_hash + data).digest()
