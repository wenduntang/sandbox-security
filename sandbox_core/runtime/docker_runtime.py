# sandbox_core/runtime/docker_runtime.py
from sandbox_core.runtime.base import BaseRuntime
from sandbox_core.config import SandboxConfig


class DockerRuntime(BaseRuntime):
    def is_available(self) -> bool:
        try:
            import docker
            client = docker.from_env()
            client.ping()
            return True
        except Exception:
            return False

    def start(self) -> str:
        import docker
        client = docker.from_env()
        cmd = self.config.command.split()
        container = client.containers.run(
            "python:3.11-slim",
            command=cmd,
            detach=True,
            remove=True,
            network_mode="none",
        )
        return container.id

    def stop(self, id: str) -> str:
        import docker
        client = docker.from_env()
        c = client.containers.get(id)
        c.stop()
        return "stopped"
