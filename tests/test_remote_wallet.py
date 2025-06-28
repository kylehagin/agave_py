from remote_wallet import RemoteWalletManager, Device, RemoteWalletInfo


def test_wallet_manager_basic():
    manager = RemoteWalletManager()
    assert manager.update_devices() == 0
    assert manager.list_devices() == []

    manager.devices = [
        Device(path="/tmp/d1", pubkey="p1"),
        Device(path="/tmp/d2", pubkey="p2"),
    ]
    assert manager.update_devices() == 2
    infos = manager.list_devices()
    assert infos == [
        RemoteWalletInfo("p1", "/tmp/d1"),
        RemoteWalletInfo("p2", "/tmp/d2"),
    ]
    assert manager.get_wallet_info("p2") == RemoteWalletInfo("p2", "/tmp/d2")
    assert manager.get_wallet_info("missing") is None
