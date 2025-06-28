from pathlib import Path
import socket

import download_utils


def test_download_genesis_if_missing_no_network(monkeypatch):
    def fail_socket(*args, **kwargs):
        raise AssertionError("network call attempted")

    monkeypatch.setattr(socket, "socket", fail_socket)
    path = Path("genesis.tar.bz2")
    assert download_utils.download_genesis_if_missing("http://localhost", path, False) == path
