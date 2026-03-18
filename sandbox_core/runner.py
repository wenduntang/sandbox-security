# sandbox_core/runner.py
from sandbox_core.config import SandboxConfig
from sandbox_core.runtime import create_runtime
from sandbox_core.verifier.env_verifier import EnvVerifier
from sandbox_core.verifier.whitelist_verifier import WhitelistVerifier
from sandbox_core.verifier.resource_verifier import ResourceVerifier
from typing import Optional, List


class SandboxRunner:
    def __init__(self, config: SandboxConfig):
        self.config = config
        self.runtime = create_runtime(config)
        self.env_verifier = EnvVerifier()
        self.whitelist_verifier = WhitelistVerifier(config.whitelist)
        self.resource_verifier = ResourceVerifier(config.resource)

    def run(self, env_paths: Optional[List[str]] = None) -> dict:
        env_paths = env_paths or []
        # 正向验证
        if not self.resource_verifier.forward_verify():
            return {"ok": False, "error": "resource config invalid"}
        if not self.whitelist_verifier.forward_verify(self.config.command):
            return {"ok": False, "error": "command not in whitelist"}
        if env_paths and not self.env_verifier.forward_verify(env_paths):
            return {"ok": False, "error": "env paths invalid"}
        self.env_verifier.take_pre_snapshot(env_paths)
        # 启动
        sid = self.runtime.start()
        # 模拟：停止（实际应等待或超时）
        self.runtime.stop(sid)
        self.resource_verifier.set_actual_usage(0.1, 64)
        # 逆向验证
        if not self.env_verifier.reverse_verify(env_paths):
            return {"ok": False, "error": "env tampered"}
        if not self.whitelist_verifier.reverse_verify():
            return {"ok": False, "error": "audit violation"}
        if not self.resource_verifier.reverse_verify():
            return {"ok": False, "error": "resource exceeded"}
        return {"ok": True, "id": sid}
