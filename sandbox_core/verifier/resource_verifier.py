# sandbox_core/verifier/resource_verifier.py
from sandbox_core.config import ResourceConfig


class ResourceVerifier:
    def __init__(self, config: ResourceConfig):
        self.config = config
        self._actual_usage: dict = {}

    def forward_verify(self) -> bool:
        """正向：资源配额预检（配置合法）"""
        if self.config.cpu_limit is not None:
            if not 0 < self.config.cpu_limit <= 1:
                return False
        if self.config.memory_mb is not None:
            if self.config.memory_mb <= 0:
                return False
        return True

    def set_actual_usage(self, cpu: float, memory_mb: int):
        self._actual_usage = {"cpu": cpu, "memory_mb": memory_mb}

    def reverse_verify(self) -> bool:
        """逆向：实际用量与配额对比"""
        if self.config.cpu_limit and self._actual_usage.get("cpu", 0) > self.config.cpu_limit:
            return False
        if self.config.memory_mb and self._actual_usage.get("memory_mb", 0) > self.config.memory_mb:
            return False
        return True
