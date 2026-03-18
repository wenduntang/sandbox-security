# tests/test_resource_verifier.py
from sandbox_core.verifier.resource_verifier import ResourceVerifier
from sandbox_core.config import ResourceConfig


def test_forward_verify_valid():
    cfg = ResourceConfig(cpu_limit=0.5, memory_mb=512)
    v = ResourceVerifier(cfg)
    assert v.forward_verify() is True


def test_forward_verify_invalid_cpu():
    cfg = ResourceConfig(cpu_limit=0)
    v = ResourceVerifier(cfg)
    assert v.forward_verify() is False


def test_reverse_verify_under_limit():
    cfg = ResourceConfig(cpu_limit=0.5, memory_mb=512)
    v = ResourceVerifier(cfg)
    v.set_actual_usage(0.3, 256)
    assert v.reverse_verify() is True


def test_reverse_verify_over_limit():
    cfg = ResourceConfig(memory_mb=512)
    v = ResourceVerifier(cfg)
    v.set_actual_usage(0.3, 1024)
    assert v.reverse_verify() is False
