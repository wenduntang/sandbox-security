# sandbox_core/verifier/whitelist_verifier.py
from typing import List
from sandbox_core.config import WhitelistConfig


class WhitelistVerifier:
    def __init__(self, config: WhitelistConfig):
        self.config = config
        self._audit_log: List[str] = []

    def forward_verify(self, command: str) -> bool:
        """正向：命令是否在白名单"""
        if not self.config.allowed_commands:
            return True
        return command in self.config.allowed_commands

    def log_audit(self, action: str):
        self._audit_log.append(action)

    def reverse_verify(self) -> bool:
        """逆向：审计日志回放，校验是否越权"""
        for action in self._audit_log:
            if action.startswith("blocked:"):
                return False
        return True
