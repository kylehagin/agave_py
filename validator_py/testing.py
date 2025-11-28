"""Testing and benchmarking helpers for the validator prototype.

This module supplies quick-running compatibility and runtime checks along with
throughput probes so the prototype can be validated against the production
expectations outlined in the roadmap.
"""

from __future__ import annotations

import asyncio
import socket
import tempfile
from dataclasses import dataclass
from typing import Iterable, List

from .crypto import Keypair, generate_keypair, sign
from .runtime import Bank
from .transaction import Transaction, WireTransactionParseError, parse_wire_transaction
from .validator import Validator


def _shortvec(value: int) -> bytes:
    encoded = bytearray()
    while True:
        elem = value & 0x7F
        value >>= 7
        if value:
            elem |= 0x80
        encoded.append(elem)
        if not value:
            break
    return bytes(encoded)


def _build_system_transfer_wire(payer: Keypair, dest: bytes, blockhash: bytes, lamports: int) -> bytes:
    """Construct a minimal legacy system transfer transaction in wire format."""

    header = bytes([1, 0, 1])  # one signer, no readonly accounts
    account_keys = [payer.public_key, dest, bytes(32)]  # payer, dest, system program id

    message = bytearray()
    message.extend(header)
    message.extend(_shortvec(len(account_keys)))
    for key in account_keys:
        message.extend(key)
    message.extend(blockhash)

    # Single system transfer instruction referencing payer and destination.
    message.extend(_shortvec(1))  # instruction count
    message.append(2)  # program id index pointing at the system program entry
    message.extend(_shortvec(2))  # account count
    message.extend(bytes([0, 1]))  # payer, destination
    data = (2).to_bytes(4, "little") + lamports.to_bytes(8, "little")
    message.extend(_shortvec(len(data)))
    message.extend(data)

    signature = sign(bytes(message), payer)
    return _shortvec(1) + signature + bytes(message)


def _reserve_port(sock_type: int) -> int:
    with socket.socket(socket.AF_INET, sock_type) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@dataclass
class TestResult:
    name: str
    success: bool
    detail: str


class WireCompatibilitySuite:
    """Exercises Solana legacy wire parsing to guard against regressions."""

    def __init__(self, samples: Iterable[bytes] | None = None):
        self.samples = list(samples) if samples is not None else []
        if not self.samples:
            payer = generate_keypair()
            dest = generate_keypair().public_key
            blockhash = bytes(range(32))
            self.samples.append(_build_system_transfer_wire(payer, dest, blockhash, lamports=500_000))

    def run(self) -> List[TestResult]:
        results: List[TestResult] = []
        for idx, raw in enumerate(self.samples):
            name = f"wire_parse_{idx}"
            try:
                parsed = parse_wire_transaction(raw)
                success = bool(parsed.account_keys and parsed.signatures)
                detail = f"{len(parsed.account_keys)} keys, {len(parsed.signatures)} signatures, blockhash {parsed.recent_blockhash}"
            except WireTransactionParseError as exc:
                success = False
                detail = f"parse failed: {exc}"
            results.append(TestResult(name=name, success=success, detail=detail))
        return results


class BankingRuntimeSuite:
    """Validates fee charging, transfers, and rent checks within the Bank."""

    def run(self) -> List[TestResult]:
        bank = Bank()
        payer_kp = generate_keypair()
        receiver_kp = generate_keypair()
        payer = payer_kp.public_key.hex()
        receiver = receiver_kp.public_key.hex()
        bank.ensure_account(payer, lamports=1_000_000)
        bank.ensure_account(receiver, lamports=0)

        fee_result = TestResult(name="bank_fees", success=False, detail="")
        amount = 50_000
        num_sigs = 2
        expected_fee = bank.fee_calculator.fee_for(num_sigs)
        if bank.process_transfer(payer, receiver, amount, num_signatures=num_sigs):
            payer_balance = bank.get_balance(payer)
            receiver_balance = bank.get_balance(receiver)
            fee_result.success = payer_balance == 1_000_000 - amount - expected_fee and receiver_balance == amount
            fee_result.detail = f"payer {payer_balance}, receiver {receiver_balance}, fee {expected_fee}"
        else:
            fee_result.detail = "transfer rejected"

        rent_result = TestResult(name="rent_enforcement", success=False, detail="")
        rent_receiver = generate_keypair().public_key.hex()
        rent_bytes = b"r" * 128
        bank.ensure_account(rent_receiver, lamports=1_000, data=rent_bytes)
        if not bank.process_transfer(payer, rent_receiver, 1000, num_signatures=1):
            rent_result.success = True
            rent_result.detail = "insufficient rent exemption detected"
        else:
            rent_result.detail = "transfer bypassed rent checks"

        # Legacy transaction path exercising instruction decoding and fee payer handling.
        legacy_result = TestResult(name="legacy_system_transfer", success=False, detail="")
        blockhash = bytes(32)
        raw = _build_system_transfer_wire(payer_kp, receiver_kp.public_key, blockhash, lamports=25_000)
        try:
            parsed = parse_wire_transaction(raw)
            bank.ensure_account(parsed.account_keys[0].hex(), lamports=200_000)
            bank.ensure_account(parsed.account_keys[1].hex(), lamports=0)
            if bank.process_legacy_transaction(parsed):
                legacy_result.success = True
                payer_after = bank.get_balance(parsed.account_keys[0].hex())
                legacy_result.detail = f"payer after {payer_after}, fee {bank.fee_calculator.fee_for(len(parsed.signatures))}"
            else:
                legacy_result.detail = "legacy processing rejected"
        except Exception as exc:  # noqa: BLE001
            legacy_result.detail = f"legacy build failed: {exc}"

        return [fee_result, rent_result, legacy_result]


class IntegrationHarness:
    """Runs a lightweight in-process validator smoke test."""

    async def run(self) -> TestResult:
        with tempfile.TemporaryDirectory() as tmpdir:
            gossip_port = _reserve_port(socket.SOCK_DGRAM)
            tpu_port = _reserve_port(socket.SOCK_DGRAM)
            tvu_port = _reserve_port(socket.SOCK_DGRAM)
            rpc_port = _reserve_port(socket.SOCK_STREAM)
            validator = Validator(
                host="127.0.0.1",
                port=gossip_port,
                rpc_port=rpc_port,
                tpu_port=tpu_port,
                tvu_port=tvu_port,
                ledger_dir=tmpdir,
            )
            await validator.start()
            try:
                receiver = generate_keypair().public_key.hex()
                recent_blockhash = validator.latest_blockhash()
                tx = Transaction.create(validator.keypair, receiver, 10_000, recent_blockhash)
                accepted = await validator.process_transaction(tx)
                await asyncio.sleep(1.0)
                balance = validator.ledger.get_balance(receiver)
                success = accepted and balance >= 10_000
                detail = f"accepted={accepted}, balance={balance}, blockhash={recent_blockhash}"
                return TestResult(name="validator_smoke", success=success, detail=detail)
            finally:
                await validator.stop()


class BenchmarkSuite:
    """Provides simple throughput probes for TPU ingress and block replay."""

    async def tpu_throughput(self, transactions: int = 200) -> TestResult:
        with tempfile.TemporaryDirectory() as tmpdir:
            gossip_port = _reserve_port(socket.SOCK_DGRAM)
            tpu_port = _reserve_port(socket.SOCK_DGRAM)
            tvu_port = _reserve_port(socket.SOCK_DGRAM)
            rpc_port = _reserve_port(socket.SOCK_STREAM)
            validator = Validator(
                host="127.0.0.1",
                port=gossip_port,
                rpc_port=rpc_port,
                tpu_port=tpu_port,
                tvu_port=tvu_port,
                ledger_dir=tmpdir,
            )
            await validator.start()
            start_height = len(validator.ledger.history)
            loop = asyncio.get_running_loop()
            transport, _ = await loop.create_datagram_endpoint(
                lambda: asyncio.DatagramProtocol(), remote_addr=("127.0.0.1", tpu_port)
            )
            try:
                blockhash = validator.latest_blockhash()
                for i in range(transactions):
                    dest = f"bench_receiver_{i}"
                    tx = Transaction.create(validator.keypair, dest, 1, blockhash)
                    transport.sendto(tx.to_bytes())
                await asyncio.sleep(2.0)
            finally:
                transport.close()
                await validator.stop()

            accepted = len(validator.ledger.history) - start_height
            rate = accepted / 2.0
            detail = f"accepted {accepted}/{transactions} ({rate:.1f} tx/s)"
            return TestResult(name="tpu_throughput", success=accepted > 0, detail=detail)


async def run_default_suite() -> List[TestResult]:
    """Run a representative test suite covering parsing, runtime, and TPU ingress."""

    results: List[TestResult] = []
    results.extend(WireCompatibilitySuite().run())
    results.extend(BankingRuntimeSuite().run())
    results.append(await IntegrationHarness().run())
    results.append(await BenchmarkSuite().tpu_throughput())
    return results


def summarize(results: Iterable[TestResult]) -> str:
    lines = []
    for res in results:
        status = "PASS" if res.success else "FAIL"
        lines.append(f"[{status}] {res.name}: {res.detail}")
    return "\n".join(lines)


def run_sync() -> None:
    results = asyncio.run(run_default_suite())
    print(summarize(results))


if __name__ == "__main__":
    run_sync()
