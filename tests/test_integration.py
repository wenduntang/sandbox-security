# tests/test_integration.py
from sandbox_core.runner import SandboxRunner
from sandbox_core.config import SandboxConfig, WhitelistConfig, ResourceConfig


def test_full_flow_process():
    cfg = SandboxConfig(
        command="echo ok",
        runtime="process",
        whitelist=WhitelistConfig(allowed_commands=[]),
        resource=ResourceConfig(cpu_limit=0.5, memory_mb=512),
    )
    cfg.whitelist.allowed_commands = ["echo", "echo ok"]
    r = SandboxRunner(cfg)
    result = r.run()
    assert result["ok"] is True
