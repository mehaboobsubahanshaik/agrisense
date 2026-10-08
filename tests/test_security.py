import time

import pytest

from app.core import security


def test_otp_hash_is_not_reversible_and_verifies():
    hashed = security.hash_secret("123456")
    assert hashed != "123456"
    assert security.verify_secret("123456", hashed)
    assert not security.verify_secret("123457", hashed)


def test_access_token_round_trip():
    token = security.create_access_token("user-1", "sess-1", "farmer")
    payload = security.decode_token(token, "access")
    assert payload["sub"] == "user-1" and payload["sid"] == "sess-1"


def test_refresh_token_cannot_be_used_as_access_token():
    token = security.create_refresh_token("user-1", "sess-1")
    with pytest.raises(Exception):
        security.decode_token(token, "access")


def test_token_signature_is_checked():
    token = security.create_access_token("user-1", "sess-1", "farmer")
    tampered = token[:-3] + ("aaa" if not token.endswith("aaa") else "bbb")
    with pytest.raises(Exception):
        security.decode_token(tampered, "access")
