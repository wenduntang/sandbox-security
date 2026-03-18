# sandbox_core/runtime/base.py
from abc import ABC, abstractmethod
from sandbox_core.config import SandboxConfig


class BaseRuntime(ABC):
    def __init__(self, config: SandboxConfig):
        self.config = config

    @abstractmethod
    def start(self) -> str:
        """启动沙箱，返回进程/容器 ID"""
        pass

    @abstractmethod
    def stop(self, id: str) -> str:
        """停止沙箱"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查运行时是否可用"""
        pass
