import json
from dataclasses import dataclass
from typing import List

from .crypto import Keypair, sign


class WireTransactionParseError(Exception):
    """Raised when a raw Solana wire transaction cannot be parsed."""


def _read_shortvec(data: bytes, offset: int) -> tuple[int, int]:
    """Decode Solana's shortvec encoding starting at ``offset``.

    Returns the decoded integer and the new offset after consumption.
    """

    value = 0
    shift = 0
    while True:
        if offset >= len(data):
            raise WireTransactionParseError("shortvec truncated")
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if (byte & 0x80) == 0:
            break
        shift += 7
        if shift > 21:  # u16 max represented across three bytes
            raise WireTransactionParseError("shortvec too long")
    return value, offset


@dataclass
class Instruction:
    program_id_index: int
    accounts: List[int]
    data: bytes


@dataclass
class MessageHeader:
    num_required_signatures: int
    num_readonly_signed_accounts: int
    num_readonly_unsigned_accounts: int


@dataclass
class WireTransactionParts:
    message: bytes
    signatures: List[bytes]
    account_keys: List[bytes]
    num_required_signatures: int
    recent_blockhash: str
    instructions: List[Instruction]
    header: MessageHeader

@dataclass
class Transaction:
    sender: str | None
    receiver: str | None
    amount: int | None
    signature: bytes | None
    recent_blockhash: str | None = None
    wire_bytes: bytes | None = None

    @classmethod
    def create(
        cls, sender_kp: Keypair, receiver: str, amount: int, recent_blockhash: str
    ) -> "Transaction":
        payload = f"{sender_kp.public_key.hex()}->{receiver}:{amount}:{recent_blockhash}".encode()
        signature = sign(payload, sender_kp)
        return cls(sender_kp.public_key.hex(), receiver, amount, signature, recent_blockhash)

    def to_bytes(self) -> bytes:
        if self.wire_bytes is not None:
            # Prefer the raw wire payload so we can forward Solana-compatible packets over TPU.
            return self.wire_bytes

        payload = {
            "sender": self.sender,
            "receiver": self.receiver,
            "amount": self.amount,
            "signature": self.signature.hex() if self.signature is not None else None,
            "recent_blockhash": self.recent_blockhash,
        }
        return json.dumps(payload).encode()

    @classmethod
    def from_bytes(cls, raw: bytes) -> "Transaction":
        try:
            payload = json.loads(raw.decode())
            signature = payload.get("signature")
            return cls(
                sender=payload.get("sender"),
                receiver=payload.get("receiver"),
                amount=int(payload.get("amount")) if payload.get("amount") is not None else None,
                signature=bytes.fromhex(signature) if isinstance(signature, str) else None,
                recent_blockhash=payload.get("recent_blockhash"),
            )
        except Exception:
            # Non-JSON payloads are treated as raw Solana wire transactions so we can
            # accept packets directly from production-style TPU senders.
            return cls(sender=None, receiver=None, amount=None, signature=None, wire_bytes=raw)


def parse_wire_transaction(raw: bytes) -> WireTransactionParts:
    """Parse a legacy Solana wire transaction for signature verification.

    This is a minimal decoder that validates the layout (shortvec-encoded
    signature and instruction vectors) and surfaces the pieces needed for
    signature checks: message bytes, signer public keys, and the recent
    blockhash. Address table lookups (v0 messages) are intentionally omitted
    for simplicity.
    """

    offset = 0
    signature_count, offset = _read_shortvec(raw, offset)
    if signature_count <= 0:
        raise WireTransactionParseError("missing signatures")

    signatures: List[bytes] = []
    for _ in range(signature_count):
        end = offset + 64
        if end > len(raw):
            raise WireTransactionParseError("signature section truncated")
        signatures.append(raw[offset:end])
        offset = end

    message = raw[offset:]
    if len(message) < 3:
        raise WireTransactionParseError("message header truncated")

    header = MessageHeader(
        num_required_signatures=message[0],
        num_readonly_signed_accounts=message[1],
        num_readonly_unsigned_accounts=message[2],
    )
    num_required_signatures = header.num_required_signatures
    if signature_count != num_required_signatures:
        raise WireTransactionParseError("signature vector does not match header")
    offset = 3  # past header

    account_keys_count, offset = _read_shortvec(message, offset)
    if account_keys_count < num_required_signatures:
        raise WireTransactionParseError("not enough account keys for required signatures")

    if header.num_readonly_signed_accounts > num_required_signatures:
        raise WireTransactionParseError("readonly signed accounts exceed signer count")

    unsigned_count = account_keys_count - num_required_signatures
    if header.num_readonly_unsigned_accounts > unsigned_count:
        raise WireTransactionParseError("readonly unsigned accounts exceed available unsigned keys")
    account_keys: List[bytes] = []
    for _ in range(account_keys_count):
        end = offset + 32
        if end > len(message):
            raise WireTransactionParseError("account keys truncated")
        account_keys.append(message[offset:end])
        offset = end

    if offset + 32 > len(message):
        raise WireTransactionParseError("recent blockhash truncated")
    recent_blockhash = message[offset : offset + 32].hex()
    offset += 32

    # Validate instruction vector layout even if we don't interpret programs.
    instruction_count, offset = _read_shortvec(message, offset)
    instructions: List[Instruction] = []
    for _ in range(instruction_count):
        if offset >= len(message):
            raise WireTransactionParseError("instruction header truncated")
        program_id_index = message[offset]
        offset += 1
        account_count, offset = _read_shortvec(message, offset)
        end = offset + account_count
        if end > len(message):
            raise WireTransactionParseError("instruction account list truncated")
        account_list = list(message[offset:end])
        offset = end
        data_length, offset = _read_shortvec(message, offset)
        end = offset + data_length
        if end > len(message):
            raise WireTransactionParseError("instruction data truncated")
        data_slice = message[offset:end]
        offset = end

        if program_id_index >= account_keys_count:
            raise WireTransactionParseError("program id index out of bounds")
        if any(idx >= account_keys_count for idx in account_list):
            raise WireTransactionParseError("instruction account index out of bounds")
        instructions.append(
            Instruction(program_id_index=program_id_index, accounts=account_list, data=data_slice)
        )

    if offset != len(message):
        raise WireTransactionParseError("extra trailing bytes in message")

    return WireTransactionParts(
        message=message,
        signatures=signatures,
        account_keys=account_keys,
        num_required_signatures=num_required_signatures,
        recent_blockhash=recent_blockhash,
        instructions=instructions,
        header=header,
    )
