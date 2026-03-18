# tests/test_env_verifier.py
import tempfile
from pathlib import Path
from sandbox_core.verifier.env_verifier import EnvVerifier


def test_forward_verify_exists():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test")
        path = f.name
    v = EnvVerifier()
    assert v.forward_verify([path]) is True
    Path(path).unlink()


def test_reverse_verify_no_tampering():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"original")
        path = f.name
    v = EnvVerifier()
    v.take_pre_snapshot([path])
    assert v.reverse_verify([path]) is True
    Path(path).unlink()


def test_reverse_verify_detects_tampering():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"original")
        path = f.name
    v = EnvVerifier()
    v.take_pre_snapshot([path])
    Path(path).write_bytes(b"tampered")
    assert v.reverse_verify([path]) is False
    Path(path).unlink()
