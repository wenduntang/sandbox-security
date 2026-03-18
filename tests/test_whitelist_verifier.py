# tests/test_whitelist_verifier.py
from sandbox_core.verifier.whitelist_verifier import WhitelistVerifier
from sandbox_core.config import WhitelistConfig


def test_forward_verify_allowed():
    cfg = WhitelistConfig(allowed_commands=["echo", "ls"])
    v = WhitelistVerifier(cfg)
    assert v.forward_verify("echo") is True


def test_forward_verify_denied():
    cfg = WhitelistConfig(allowed_commands=["echo"])
    v = WhitelistVerifier(cfg)
    assert v.forward_verify("rm") is False


def test_reverse_verify_clean():
    v = WhitelistVerifier(WhitelistConfig())
    v.log_audit("allowed")
    assert v.reverse_verify() is True
