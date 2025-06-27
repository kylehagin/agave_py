"""Helpers for fetching genesis and snapshot archives."""

from pathlib import Path
from typing import Optional, Tuple


def download_genesis_if_missing(
    rpc_addr: str, genesis_package: Path, use_progress_bar: bool
) -> Path:
    """Download the genesis archive if it doesn't exist.

    The real implementation performs HTTP requests and progress reporting.  This
    stub merely returns ``genesis_package`` and does not perform network IO.
    """

    # TODO: implement real download logic
    return genesis_package


def download_snapshot_archive(
    rpc_addr: str,
    full_snapshot_archives_dir: Path,
    incremental_snapshot_archives_dir: Path,
    desired_snapshot_hash: Tuple[int, str],
    snapshot_kind: str,
    maximum_full_snapshot_archives_to_retain: int,
    maximum_incremental_snapshot_archives_to_retain: int,
    use_progress_bar: bool,
    progress_notify_callback: Optional[object] = None,
) -> None:
    """Placeholder for downloading a snapshot archive."""

    # TODO: implement real snapshot download logic
    return None

