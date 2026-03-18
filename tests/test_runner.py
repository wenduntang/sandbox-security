# tests/test_runner.py
from sandbox_core.runner import SandboxRunner
from sandbox_core.config import SandboxConfig, WhitelistConfig


def test_runner_integration():
    cfg = SandboxConfig(
        command="echo ok",
        runtime="process",
        whitelist=WhitelistConfig(allowed_commands=[]),
    )
    r = SandboxRunner(cfg)
    r.config.whitelist.allowed_commands = ["echo", "echo ok"]
    result = r.run()
    assert result["ok"] is True
