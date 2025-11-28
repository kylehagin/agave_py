"""Basic Ed25519 primitives used by the prototype validator.

This module intentionally avoids the previous symmetric-key placeholder and
uses real public-key operations to more closely mirror Solana's requirements.
"""

import binascii
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

from nacl import exceptions as nacl_exceptions
from nacl import signing


@dataclass
class Keypair:
    signing_key: signing.SigningKey
    verify_key: signing.VerifyKey

    @property
    def public_key(self) -> bytes:
        return bytes(self.verify_key)


def generate_keypair() -> Keypair:
    sk = signing.SigningKey.generate()
    return Keypair(sk, sk.verify_key)


def keypair_from_hex(secret_hex: str) -> Keypair:
    sk = signing.SigningKey(bytes.fromhex(secret_hex))
    return Keypair(sk, sk.verify_key)


def serialize_keypair(keypair: Keypair) -> str:
    return keypair.signing_key.encode().hex()


def load_or_create_keypair(path: str | Path) -> Keypair:
    """Persist a keypair with owner-only permissions, creating if absent."""

    dest = Path(path)
    if dest.exists():
        try:
            with dest.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
            secret = payload.get("secret")
            if isinstance(secret, str):
                return keypair_from_hex(secret)
        except Exception:
            pass
    dest.parent.mkdir(parents=True, exist_ok=True)
    kp = generate_keypair()
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as fh:
        json.dump({"secret": serialize_keypair(kp)}, fh)
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        # Best effort; environment may not support chmod (e.g., Windows).
        pass
    tmp.replace(dest)
    try:
        os.chmod(dest, 0o600)
    except OSError:
        pass
    return kp


def sign(message: bytes, keypair: Keypair) -> bytes:
    signed = keypair.signing_key.sign(message)
    return signed.signature


def verify(message: bytes, signature: bytes, public_key: bytes) -> bool:
    try:
        verify_key = signing.VerifyKey(public_key)
        verify_key.verify(message, signature)
        return True
    except (nacl_exceptions.BadSignatureError, binascii.Error, ValueError):
        return False


def poh_hash(prev_hash: bytes, data: bytes) -> bytes:
    return hashlib.sha256(prev_hash + data).digest()
