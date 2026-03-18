# sandbox_core/runtime/factory.py
from sandbox_core.runtime.base import BaseRuntime
from sandbox_core.runtime.docker_runtime import DockerRuntime
from sandbox_core.runtime.process_runtime import ProcessRuntime
from sandbox_core.config import SandboxConfig


def create_runtime(config: SandboxConfig) -> BaseRuntime:
    if config.runtime == "docker":
        return DockerRuntime(config)
    if config.runtime == "process":
        return ProcessRuntime(config)
    # auto: prefer Docker, fallback to Process
    if DockerRuntime(config).is_available():
        return DockerRuntime(config)
    return ProcessRuntime(config)
