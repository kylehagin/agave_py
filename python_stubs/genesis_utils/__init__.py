"""Helpers for interacting with genesis archives."""

from pathlib import Path
from typing import Optional


def download_then_check_genesis_hash(
    rpc_addr: str,
    ledger_path: Path,
    expected_genesis_hash: Optional[str],
    max_genesis_archive_unpacked_size: int,
    no_genesis_fetch: bool,
    use_progress_bar: bool,
    rpc_client: object,
) -> None:
    """Download genesis and verify its hash.

    Networking and actual hash verification are not implemented.
    """

    # TODO: implement download and hash checks
    return None

