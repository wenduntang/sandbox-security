# tests/test_security.py
from sandbox_core.runner import SandboxRunner
from sandbox_core.config import SandboxConfig, WhitelistConfig


def test_whitelist_blocks_unauthorized():
    cfg = SandboxConfig(
        command="rm -rf /",
        runtime="process",
        whitelist=WhitelistConfig(allowed_commands=["echo"]),
    )
    r = SandboxRunner(cfg)
    result = r.run()
    assert result["ok"] is False
    assert "whitelist" in result.get("error", "").lower()
