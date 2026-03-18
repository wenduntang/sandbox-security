# sandbox_core/config.py
from pydantic import BaseModel, Field
from typing import Optional, List


class ResourceConfig(BaseModel):
    cpu_limit: Optional[float] = None  # 0.0-1.0
    memory_mb: Optional[int] = None
    network_bandwidth_mbps: Optional[float] = None


class WhitelistConfig(BaseModel):
    allowed_commands: List[str] = Field(default_factory=list)
    allowed_ports: List[int] = Field(default_factory=list)
    allowed_paths: List[str] = Field(default_factory=list)


class SandboxConfig(BaseModel):
    runtime: str = "auto"  # auto | docker | process
    command: str = ""
    resource: ResourceConfig = Field(default_factory=ResourceConfig)
    whitelist: WhitelistConfig = Field(default_factory=WhitelistConfig)
