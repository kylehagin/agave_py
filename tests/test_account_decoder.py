from dataclasses import dataclass
import base64
import sys
import types

fake_base58 = types.SimpleNamespace()
fake_base58.b58encode = lambda b: b.hex().encode("ascii")
sys.modules.setdefault("base58", fake_base58)

import base58
from account_decoder import encode_ui_account, _slice_data
from account_decoder_client_types import UiAccountEncoding, UiDataSliceConfig


@dataclass
class FakeAccount:
    lamports: int
    data: bytes
    owner: str
    executable: bool
    rent_epoch: int


def test_slice_data_basic():
    assert _slice_data(b"abcdef", UiDataSliceConfig(offset=2, length=3)) == b"cde"
    assert _slice_data(b"abc", UiDataSliceConfig(offset=10, length=2)) == b""


def test_encode_ui_account_base64():
    acc = FakeAccount(1, b"hello", "owner", False, 0)
    ui = encode_ui_account("pub", acc, UiAccountEncoding.BASE64)
    assert ui.data.raw_data == base64.b64encode(b"hello").decode("ascii")
    assert ui.data.encoding == UiAccountEncoding.BASE64
    assert ui.lamports == 1
    assert ui.space == 5


def test_encode_ui_account_base58_binary():
    acc = FakeAccount(1, b"hello", "owner", False, 0)
    ui = encode_ui_account("pub", acc, UiAccountEncoding.BINARY)
    assert ui.data.raw_data == base58.b58encode(b"hello").decode("ascii")
    assert ui.data.encoding == UiAccountEncoding.BINARY


def test_encode_ui_account_with_slice():
    acc = FakeAccount(1, b"hello", "owner", False, 0)
    cfg = UiDataSliceConfig(offset=1, length=3)
    ui = encode_ui_account("pub", acc, UiAccountEncoding.BASE64, data_slice_config=cfg)
    assert ui.data.raw_data == base64.b64encode(b"ell").decode("ascii")
