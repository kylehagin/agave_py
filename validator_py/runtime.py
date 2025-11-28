"""Lightweight banking runtime with fee, rent, and system transfer support.

This module introduces a minimal accounts database, fee calculation, and
rent-exemption enforcement to bring the validator prototype closer to a
production-style banking stage. Only the system program transfer path is
implemented, but the scaffolding models fee-payer handling and atomic
instruction application across a transaction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List

from .transaction import Instruction, WireTransactionParts

SYSTEM_PROGRAM_ID = bytes(32)
STAKE_PROGRAM_ID = b"stake_program".ljust(32, b"\x00")
VOTE_PROGRAM_ID = b"vote_program".ljust(32, b"\x00")
NONCE_PROGRAM_ID = b"nonce_program".ljust(32, b"\x00")


@dataclass
class Account:
    lamports: int
    owner: bytes = SYSTEM_PROGRAM_ID
    data: bytes = b""
    executable: bool = False


class FeeCalculator:
    """Calculate transaction fees based on signature count."""

    lamports_per_signature: int = 5000

    def fee_for(self, num_signatures: int) -> int:
        return self.lamports_per_signature * num_signatures


class Rent:
    """Minimal rent model enforcing rent-exempt minimums for data-bearing accounts."""

    lamports_per_byte_year: int = 3480
    exemption_threshold: float = 2.0

    def minimum_balance(self, data_length: int) -> int:
        return int(self.lamports_per_byte_year * data_length * self.exemption_threshold)


class Bank:
    """Holds account state and applies verified transactions atomically."""

    def __init__(self, fee_calculator: FeeCalculator | None = None, rent: Rent | None = None):
        self.fee_calculator = fee_calculator or FeeCalculator()
        self.rent = rent or Rent()
        self.accounts: Dict[str, Account] = {}
        self.programs: Dict[bytes, Callable[[Dict[str, int], Instruction, List[str], int], bool]] = {
            SYSTEM_PROGRAM_ID: self._apply_system_transfer,
            STAKE_PROGRAM_ID: self._apply_stake_program,
            VOTE_PROGRAM_ID: self._apply_vote_program,
            NONCE_PROGRAM_ID: self._apply_nonce_program,
        }
        self.vote_accounts: Dict[str, dict] = {}
        self.stake_accounts: Dict[str, dict] = {}
        self.nonce_accounts: Dict[str, dict] = {}
        self.rent_burned: int = 0

    def register_program(self, program_id: bytes, handler: Callable[[Dict[str, int], Instruction, List[str], int], bool]) -> None:
        self.programs[program_id] = handler

    def _normalize(self, pubkey: str | bytes) -> str:
        return pubkey.hex() if isinstance(pubkey, (bytes, bytearray)) else pubkey

    def get_balance(self, owner: str | bytes) -> int:
        key = self._normalize(owner)
        account = self.accounts.get(key)
        return account.lamports if account else 0

    def ensure_account(
        self, owner: str | bytes, lamports: int = 0, owner_program: bytes | None = None, data: bytes = b"", executable: bool = False
    ) -> Account:
        key = self._normalize(owner)
        if key not in self.accounts:
            self.accounts[key] = Account(lamports=lamports, owner=owner_program or SYSTEM_PROGRAM_ID, data=data, executable=executable)
        else:
            self.accounts[key].lamports = lamports
        return self.accounts[key]

    def _snapshot_balances(self) -> Dict[str, int]:
        return {k: acc.lamports for k, acc in self.accounts.items()}

    def _apply_fee(self, staged: Dict[str, int], payer: str, fee: int) -> bool:
        if fee <= 0:
            return True
        staged.setdefault(payer, self.accounts.get(payer, Account(0)).lamports)
        if staged[payer] < fee:
            return False
        staged[payer] -= fee
        return True

    def _debit(self, staged: Dict[str, int], owner: str, amount: int) -> bool:
        staged.setdefault(owner, self.accounts.get(owner, Account(0)).lamports)
        if amount < 0:
            return False
        if staged[owner] < amount:
            return False
        staged[owner] -= amount
        return True

    def _credit(self, staged: Dict[str, int], owner: str, amount: int) -> None:
        staged.setdefault(owner, self.accounts.get(owner, Account(0)).lamports)
        staged[owner] += amount

    def _rent_exempt_ok(self, staged: Dict[str, int], touched_accounts: Iterable[str]) -> bool:
        for key in touched_accounts:
            account = self.accounts.get(key)
            data_length = len(account.data) if account else 0
            if data_length == 0:
                continue
            required = self.rent.minimum_balance(data_length)
            if staged.get(key, 0) < required:
                return False
        return True

    def _apply_rent_accrual(self, staged: Dict[str, int], touched: Iterable[str]) -> None:
        for key in touched:
            account = self.accounts.get(key)
            if not account:
                continue
            data_len = len(account.data)
            if data_len == 0:
                continue
            due = max(self.rent.lamports_per_byte_year // 100, 1) * data_len
            staged.setdefault(key, account.lamports)
            staged[key] = max(0, staged[key] - due)
            self.rent_burned += due

    def _commit(self, staged: Dict[str, int]) -> None:
        for key, amount in staged.items():
            if key not in self.accounts:
                self.accounts[key] = Account(lamports=amount)
            else:
                self.accounts[key].lamports = amount

    def process_transfer(self, sender: str, receiver: str, amount: int, num_signatures: int = 1) -> bool:
        """Apply a simple transfer with fee deduction."""

        if amount < 0:
            return False

        staged = self._snapshot_balances()
        fee = self.fee_calculator.fee_for(num_signatures)
        if not self._apply_fee(staged, payer=sender, fee=fee):
            return False
        if not self._debit(staged, sender, amount):
            return False
        self._credit(staged, receiver, amount)

        if not self._rent_exempt_ok(staged, [sender, receiver]):
            return False

        self._commit(staged)
        return True

    def _apply_system_transfer(self, staged: Dict[str, int], instr: Instruction, keys: List[str], depth: int = 0) -> bool:
        if len(instr.accounts) < 2:
            return False
        if len(instr.data) < 4:
            return False
        instruction_id = int.from_bytes(instr.data[:4], "little")
        if instruction_id == 0:  # CreateAccount
            if len(instr.accounts) < 2 or len(instr.data) < 20:
                return False
            lamports = int.from_bytes(instr.data[4:12], "little")
            space = int.from_bytes(instr.data[12:20], "little")
            try:
                funder = keys[instr.accounts[0]]
                new_account = keys[instr.accounts[1]]
            except IndexError:
                return False
            if not self._debit(staged, funder, lamports):
                return False
            staged.setdefault(new_account, 0)
            staged[new_account] += lamports
            self.accounts.setdefault(new_account, Account(lamports=lamports, data=bytes(space)))
            return True
        if instruction_id != 2:  # SystemInstruction::Transfer
            return False
        if len(instr.data) < 12:
            return False
        lamports = int.from_bytes(instr.data[4:12], "little")
        try:
            source = keys[instr.accounts[0]]
            dest = keys[instr.accounts[1]]
        except IndexError:
            return False
        if lamports < 0:
            return False
        if not self._debit(staged, source, lamports):
            return False
        self._credit(staged, dest, lamports)
        return True

    def _apply_vote_program(self, staged: Dict[str, int], instr: Instruction, keys: List[str], depth: int = 0) -> bool:
        if len(instr.data) < 4:
            return False
        vote_instruction = int.from_bytes(instr.data[:4], "little")
        if vote_instruction == 0:  # InitializeAccount
            if len(instr.accounts) < 2:
                return False
            try:
                vote_account = keys[instr.accounts[0]]
                authorized = keys[instr.accounts[1]]
            except IndexError:
                return False
            self.vote_accounts[vote_account] = {"authorized": authorized, "credits": 0, "last_vote": None}
            self.accounts.setdefault(vote_account, Account(lamports=staged.get(vote_account, 0), owner=VOTE_PROGRAM_ID))
            return True
        if vote_instruction == 1:  # Vote
            if len(instr.accounts) < 2 or len(instr.data) < 12:
                return False
            try:
                vote_account = keys[instr.accounts[0]]
                signer = keys[instr.accounts[1]]
            except IndexError:
                return False
            state = self.vote_accounts.get(vote_account)
            if not state or state.get("authorized") != signer:
                return False
            slot = int.from_bytes(instr.data[4:12], "little")
            state["last_vote"] = slot
            state["credits"] = state.get("credits", 0) + 1
            return True
        return False

    def _apply_stake_program(self, staged: Dict[str, int], instr: Instruction, keys: List[str], depth: int = 0) -> bool:
        if len(instr.data) < 4:
            return False
        stake_instruction = int.from_bytes(instr.data[:4], "little")
        if stake_instruction == 0:  # DelegateStake
            if len(instr.accounts) < 3 or len(instr.data) < 12:
                return False
            try:
                stake_account = keys[instr.accounts[0]]
                source = keys[instr.accounts[1]]
                vote_account = keys[instr.accounts[2]]
            except IndexError:
                return False
            lamports = int.from_bytes(instr.data[4:12], "little")
            if not self._debit(staged, source, lamports):
                return False
            staged.setdefault(stake_account, self.accounts.get(stake_account, Account(0)).lamports)
            staged[stake_account] += lamports
            self.accounts.setdefault(stake_account, Account(lamports=staged[stake_account], owner=STAKE_PROGRAM_ID))
            self.stake_accounts[stake_account] = {
                "delegated_vote": vote_account,
                "stake": staged[stake_account],
                "active": True,
            }
            return True
        if stake_instruction == 1:  # DeactivateStake
            if len(instr.accounts) < 1:
                return False
            try:
                stake_account = keys[instr.accounts[0]]
            except IndexError:
                return False
            state = self.stake_accounts.get(stake_account)
            if not state:
                return False
            state["active"] = False
            return True
        if stake_instruction == 2:  # Withdraw
            if len(instr.accounts) < 2:
                return False
            try:
                stake_account = keys[instr.accounts[0]]
                destination = keys[instr.accounts[1]]
            except IndexError:
                return False
            state = self.stake_accounts.get(stake_account)
            if not state:
                return False
            if state.get("active"):
                return False
            available = staged.get(stake_account, self.accounts.get(stake_account, Account(0)).lamports)
            staged.setdefault(destination, self.accounts.get(destination, Account(0)).lamports)
            staged[destination] += available
            staged[stake_account] = 0
            self.accounts.setdefault(destination, Account(lamports=staged[destination]))
            return True
        return False

    def _apply_nonce_program(self, staged: Dict[str, int], instr: Instruction, keys: List[str], depth: int = 0) -> bool:
        if len(instr.data) < 4:
            return False
        nonce_instruction = int.from_bytes(instr.data[:4], "little")
        if nonce_instruction == 0:  # InitializeNonceAccount
            if len(instr.accounts) < 2:
                return False
            try:
                nonce_account = keys[instr.accounts[0]]
                authority = keys[instr.accounts[1]]
            except IndexError:
                return False
            self.nonce_accounts[nonce_account] = {"authority": authority, "nonce": instr.data[4:36].hex() if len(instr.data) >= 36 else "0" * 64}
            self.accounts.setdefault(nonce_account, Account(lamports=staged.get(nonce_account, 0), owner=NONCE_PROGRAM_ID))
            return True
        if nonce_instruction == 1:  # AdvanceNonce
            if len(instr.accounts) < 2:
                return False
            try:
                nonce_account = keys[instr.accounts[0]]
                authority = keys[instr.accounts[1]]
            except IndexError:
                return False
            state = self.nonce_accounts.get(nonce_account)
            if not state or state.get("authority") != authority:
                return False
            state["nonce"] = instr.data[4:36].hex() if len(instr.data) >= 36 else state.get("nonce")
            return True
        return False

    def _dispatch_instruction(
        self, staged: Dict[str, int], parsed: WireTransactionParts, instr: Instruction, keys: List[str], depth: int = 0
    ) -> bool:
        if depth > 4:
            return False
        try:
            program_id = parsed.account_keys[instr.program_id_index]
        except IndexError:
            return False
        handler = self.programs.get(program_id)
        if handler is None:
            return False
        # Support a simple CPI flow by allowing programs to emit nested instructions when instr.data starts with b"CPI".
        if instr.data.startswith(b"CPI"):
            nested_count = instr.data[3]
            cursor = 4
            for _ in range(nested_count):
                if cursor + 1 >= len(instr.data):
                    return False
                program_idx = instr.data[cursor]
                acct_count = instr.data[cursor + 1]
                cursor += 2
                if cursor + acct_count > len(instr.data):
                    return False
                account_indices = list(instr.data[cursor : cursor + acct_count])
                cursor += acct_count
                if cursor + 2 > len(instr.data):
                    return False
                data_len = int.from_bytes(instr.data[cursor : cursor + 2], "little")
                cursor += 2
                if cursor + data_len > len(instr.data):
                    return False
                data = instr.data[cursor : cursor + data_len]
                cursor += data_len
                nested_instr = Instruction(accounts=account_indices, program_id_index=program_idx, data=data)
                if not self._dispatch_instruction(staged, parsed, nested_instr, keys, depth + 1):
                    return False
            return True
        return handler(staged, instr, keys, depth)

    def process_legacy_transaction(self, parsed: WireTransactionParts) -> bool:
        if not parsed.account_keys:
            return False
        payer = parsed.account_keys[0].hex()
        staged = self._snapshot_balances()
        fee = self.fee_calculator.fee_for(len(parsed.signatures))
        if not self._apply_fee(staged, payer, fee):
            return False

        keys = [key.hex() for key in parsed.account_keys]
        touched = {payer}
        for instr in parsed.instructions:
            if not self._dispatch_instruction(staged, parsed, instr, keys, 0):
                return False
            touched.update(keys[i] for i in instr.accounts if i < len(keys))

        self._apply_rent_accrual(staged, touched)
        if not self._rent_exempt_ok(staged, touched):
            return False

        self._commit(staged)
        return True

    def register_program(self, program_id: bytes, handler) -> None:
        """Register a custom program handler for instruction dispatch."""
        self.programs[program_id] = handler
