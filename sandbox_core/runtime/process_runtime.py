# sandbox_core/runtime/process_runtime.py
import subprocess
import shlex
from sandbox_core.runtime.base import BaseRuntime
from sandbox_core.config import SandboxConfig


class ProcessRuntime(BaseRuntime):
    def __init__(self, config: SandboxConfig):
        super().__init__(config)
        self._process = None

    def is_available(self) -> bool:
        return True

    def start(self) -> str:
        cmd = shlex.split(self.config.command)
        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        return str(self._process.pid)

    def stop(self, id: str) -> str:
        if self._process:
            self._process.terminate()
            self._process.wait(timeout=5)
        return "stopped"
