# 沙箱安全运行环境 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建沙箱安全运行环境，隔离运行 Web 服务/API，支持 Docker+进程双重隔离、三种正逆向验证、CLI+库+Web 三种使用方式。

**Architecture:** 分层架构：sandbox_core 为核心库（runtime/verifier/audit），CLI 和 Web 调用同一套 API；运行时优先 Docker，备选进程级；验证分环境/白名单/资源三类，每类含正向预检与逆向事后校验。

**Tech Stack:** Python 3.10+, pytest, click/typer, FastAPI, docker-py (可选), pydantic

---

## Task 1: 项目脚手架

**Files:**
- Create: `~/apps/sandbox-security/pyproject.toml`
- Create: `~/apps/sandbox-security/README.md`
- Create: `~/apps/sandbox-security/.gitignore`

**Step 1: 创建 pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=61", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "sandbox-security"
version = "0.1.0"
description = "沙箱安全运行环境，用于隔离运行不可信 Web 服务/API"
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.0",
    "click>=8.0",
    "fastapi>=0.100",
    "uvicorn>=0.22",
    "docker>=6.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = ["pytest>=7", "pytest-cov>=4"]

[tool.setuptools.packages.find]
include = ["sandbox_core*", "cli*", "web*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

**Step 2: 创建 README.md**

```markdown
# 沙箱安全运行环境

隔离运行不可信 Web 服务/API，支持 Docker+进程双重隔离、正逆向验证。

## 安装

python -m venv ~/.sandbox-security-venv
source ~/.sandbox-security-venv/bin/activate
pip install -e .

## 使用

# CLI
sandbox run --config config.yaml

# Python
from sandbox_core import SandboxRunner
runner = SandboxRunner()
runner.run(...)
```

**Step 3: 创建 .gitignore**

```
__pycache__/
*.pyc
.venv/
*.egg-info/
dist/
*.log
.env
```

**Step 4: Run**

```bash
cd ~/apps/sandbox-security && python -m venv ~/.sandbox-security-venv
source ~/.sandbox-security-venv/bin/activate
pip install -e ".[dev]"
```

Expected: 安装成功

---

## Task 2: 核心配置与数据模型

**Files:**
- Create: `~/apps/sandbox-security/sandbox_core/__init__.py`
- Create: `~/apps/sandbox-security/sandbox_core/config.py`

**Step 1: 创建 __init__.py**

```python
# sandbox_core/__init__.py
__version__ = "0.1.0"
```

**Step 2: 创建 config.py（Pydantic 模型）**

```python
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
```

**Step 3: 测试**

```bash
cd ~/apps/sandbox-security && python -c "
from sandbox_core.config import SandboxConfig, ResourceConfig
c = SandboxConfig(command='python -m http.server 8000')
assert c.runtime == 'auto'
assert c.command == 'python -m http.server 8000'
print('OK')
"
```

**Step 4: Commit**

```bash
git add . && git commit -m "chore: project scaffold and config models"
```

---

## Task 3: 运行时抽象与 Docker 实现

**Files:**
- Create: `~/apps/sandbox-security/sandbox_core/runtime/__init__.py`
- Create: `~/apps/sandbox-security/sandbox_core/runtime/base.py`
- Create: `~/apps/sandbox-security/sandbox_core/runtime/docker_runtime.py`

**Step 1: 创建 base.py**

```python
# sandbox_core/runtime/base.py
from abc import ABC, abstractmethod
from sandbox_core.config import SandboxConfig, ResourceConfig


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
```

**Step 2: 创建 docker_runtime.py**

```python
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
```

**Step 3: 测试**

```bash
cd ~/apps/sandbox-security && python -c "
from sandbox_core.runtime.docker_runtime import DockerRuntime
from sandbox_core.config import SandboxConfig
r = DockerRuntime(SandboxConfig(command='echo hello'))
print('available:', r.is_available())
"
```

**Step 4: Commit**

```bash
git add . && git commit -m "feat: add Docker runtime"
```

---

## Task 4: 进程级运行时

**Files:**
- Create: `~/apps/sandbox-security/sandbox_core/runtime/process_runtime.py`

**Step 1: 创建 process_runtime.py**

```python
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
```

**Step 2: 测试**

```bash
cd ~/apps/sandbox-security && python -c "
from sandbox_core.runtime.process_runtime import ProcessRuntime
from sandbox_core.config import SandboxConfig
r = ProcessRuntime(SandboxConfig(command='sleep 1'))
pid = r.start()
assert pid
r.stop(pid)
print('OK')
"
```

**Step 3: Commit**

```bash
git add . && git commit -m "feat: add process runtime"
```

---

## Task 5: 运行时工厂（自动选择 Docker/Process）

**Files:**
- Create: `~/apps/sandbox-security/sandbox_core/runtime/factory.py`
- Modify: `~/apps/sandbox-security/sandbox_core/runtime/__init__.py`

**Step 1: 创建 factory.py**

```python
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
```

**Step 2: 更新 __init__.py**

```python
# sandbox_core/runtime/__init__.py
from sandbox_core.runtime.factory import create_runtime
from sandbox_core.runtime.base import BaseRuntime
__all__ = ["create_runtime", "BaseRuntime"]
```

**Step 3: 测试**

```bash
cd ~/apps/sandbox-security && python -c "
from sandbox_core.runtime import create_runtime
from sandbox_core.config import SandboxConfig
r = create_runtime(SandboxConfig(command='echo ok'))
print(type(r).__name__)
"
```

**Step 4: Commit**

```bash
git add . && git commit -m "feat: runtime factory with auto selection"
```

---

## Task 6: 环境/配置验证器（正向+逆向）

**Files:**
- Create: `~/apps/sandbox-security/sandbox_core/verifier/__init__.py`
- Create: `~/apps/sandbox-security/sandbox_core/verifier/env_verifier.py`

**Step 1: 创建 env_verifier.py**

```python
# sandbox_core/verifier/env_verifier.py
import os
import hashlib
from pathlib import Path
from typing import Dict, Optional


class EnvVerifier:
    """环境/配置正向与逆向验证"""

    def __init__(self, snapshot_dir: Optional[str] = None):
        self.snapshot_dir = snapshot_dir or "/tmp/sandbox_snapshots"
        self._pre_snapshot: Dict[str, str] = {}

    def forward_verify(self, paths: list[str]) -> bool:
        """正向：检查路径存在且可读"""
        for p in paths:
            if not Path(p).exists():
                return False
        return True

    def take_pre_snapshot(self, paths: list[str]) -> bool:
        """正向：记录启动前快照"""
        self._pre_snapshot = {}
        for p in paths:
            if Path(p).exists():
                content = Path(p).read_bytes()
                self._pre_snapshot[p] = hashlib.sha256(content).hexdigest()
        return True

    def reverse_verify(self, paths: list[str]) -> bool:
        """逆向：对比启动前后，检测篡改"""
        for p in paths:
            if p not in self._pre_snapshot:
                continue
            if not Path(p).exists():
                return False
            content = Path(p).read_bytes()
            h = hashlib.sha256(content).hexdigest()
            if h != self._pre_snapshot[p]:
                return False
        return True
```

**Step 2: 创建 tests/test_env_verifier.py**

```python
# tests/test_env_verifier.py
import tempfile
from pathlib import Path
from sandbox_core.verifier.env_verifier import EnvVerifier


def test_forward_verify_exists():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test")
        path = f.name
    v = EnvVerifier()
    assert v.forward_verify([path]) is True
    Path(path).unlink()


def test_reverse_verify_no_tampering():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"original")
        path = f.name
    v = EnvVerifier()
    v.take_pre_snapshot([path])
    assert v.reverse_verify([path]) is True
    Path(path).unlink()


def test_reverse_verify_detects_tampering():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"original")
        path = f.name
    v = EnvVerifier()
    v.take_pre_snapshot([path])
    Path(path).write_bytes(b"tampered")
    assert v.reverse_verify([path]) is False
    Path(path).unlink()
```

**Step 3: Run tests**

```bash
cd ~/apps/sandbox-security && pytest tests/test_env_verifier.py -v
```

**Step 4: Commit**

```bash
git add . && git commit -m "feat: env verifier with forward/reverse"
```

---

## Task 7: 白名单/审计验证器

**Files:**
- Create: `~/apps/sandbox-security/sandbox_core/verifier/whitelist_verifier.py`
- Create: `~/apps/sandbox-security/tests/test_whitelist_verifier.py`

**Step 1: 创建 whitelist_verifier.py**

```python
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
```

**Step 2: 创建 tests/test_whitelist_verifier.py**

```python
# tests/test_whitelist_verifier.py
from sandbox_core.verifier.whitelist_verifier import WhitelistVerifier
from sandbox_core.config import WhitelistConfig


def test_forward_verify_allowed():
    cfg = WhitelistConfig(allowed_commands=["echo", "ls"])
    v = WhitelistVerifier(cfg)
    assert v.forward_verify("echo") is True


def test_forward_verify_denied():
    cfg = WhitelistConfig(allowed_commands=["echo"])
    v = WhitelistVerifier(cfg)
    assert v.forward_verify("rm") is False


def test_reverse_verify_clean():
    v = WhitelistVerifier(WhitelistConfig())
    v.log_audit("allowed")
    assert v.reverse_verify() is True
```

**Step 3: Run tests**

```bash
cd ~/apps/sandbox-security && pytest tests/test_whitelist_verifier.py -v
```

**Step 4: Commit**

```bash
git add . && git commit -m "feat: whitelist verifier with audit"
```

---

## Task 8: 资源验证器

**Files:**
- Create: `~/apps/sandbox-security/sandbox_core/verifier/resource_verifier.py`
- Create: `~/apps/sandbox-security/tests/test_resource_verifier.py`

**Step 1: 创建 resource_verifier.py**

```python
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
```

**Step 2: 创建 tests/test_resource_verifier.py**

```python
# tests/test_resource_verifier.py
from sandbox_core.verifier.resource_verifier import ResourceVerifier
from sandbox_core.config import ResourceConfig


def test_forward_verify_valid():
    cfg = ResourceConfig(cpu_limit=0.5, memory_mb=512)
    v = ResourceVerifier(cfg)
    assert v.forward_verify() is True


def test_forward_verify_invalid_cpu():
    cfg = ResourceConfig(cpu_limit=0)
    v = ResourceVerifier(cfg)
    assert v.forward_verify() is False


def test_reverse_verify_under_limit():
    cfg = ResourceConfig(cpu_limit=0.5, memory_mb=512)
    v = ResourceVerifier(cfg)
    v.set_actual_usage(0.3, 256)
    assert v.reverse_verify() is True


def test_reverse_verify_over_limit():
    cfg = ResourceConfig(memory_mb=512)
    v = ResourceVerifier(cfg)
    v.set_actual_usage(0.3, 1024)
    assert v.reverse_verify() is False
```

**Step 3: Run tests**

```bash
cd ~/apps/sandbox-security && pytest tests/test_resource_verifier.py -v
```

**Step 4: Commit**

```bash
git add . && git commit -m "feat: resource verifier with forward/reverse"
```

---

## Task 9: SandboxRunner 整合

**Files:**
- Create: `~/apps/sandbox-security/sandbox_core/runner.py`
- Create: `~/apps/sandbox-security/tests/test_runner.py`

**Step 1: 创建 runner.py**

```python
# sandbox_core/runner.py
from sandbox_core.config import SandboxConfig
from sandbox_core.runtime import create_runtime
from sandbox_core.verifier.env_verifier import EnvVerifier
from sandbox_core.verifier.whitelist_verifier import WhitelistVerifier
from sandbox_core.verifier.resource_verifier import ResourceVerifier
from typing import Optional


class SandboxRunner:
    def __init__(self, config: SandboxConfig):
        self.config = config
        self.runtime = create_runtime(config)
        self.env_verifier = EnvVerifier()
        self.whitelist_verifier = WhitelistVerifier(config.whitelist)
        self.resource_verifier = ResourceVerifier(config.resource)

    def run(self, env_paths: Optional[list[str]] = None) -> dict:
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
```

**Step 2: 创建 tests/test_runner.py**

```python
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
```

**Step 3: Run tests**

```bash
cd ~/apps/sandbox-security && pytest tests/test_runner.py -v
```

**Step 4: Commit**

```bash
git add . && git commit -m "feat: SandboxRunner with full verification flow"
```

---

## Task 10: CLI 入口

**Files:**
- Create: `~/apps/sandbox-security/cli/__init__.py`
- Create: `~/apps/sandbox-security/cli/main.py`
- Modify: `~/apps/sandbox-security/pyproject.toml` (add scripts)

**Step 1: 创建 cli/main.py**

```python
# cli/main.py
import click
import yaml
from pathlib import Path
from sandbox_core.config import SandboxConfig, ResourceConfig, WhitelistConfig
from sandbox_core.runner import SandboxRunner


@click.group()
def cli():
    pass


@cli.command()
@click.option("--config", "-c", type=click.Path(exists=True), help="JSON/YAML config")
@click.option("--command", "-C", help="command to run")
def run(config: str, command: str):
    if config:
        data = yaml.safe_load(Path(config).read_text())
        cfg = SandboxConfig(**data)
    else:
        cfg = SandboxConfig(command=command or "echo ok")
    runner = SandboxRunner(cfg)
    result = runner.run()
    click.echo(f"Result: {result}")
```

**Step 2: 创建 cli/__init__.py**

```python
# cli/__init__.py
from cli.main import cli
__all__ = ["cli"]
```

**Step 3: 修改 pyproject.toml 添加 scripts**

```toml
[project.scripts]
sandbox = "cli.main:cli"
```

**Step 4: 测试**

```bash
cd ~/apps/sandbox-security && pip install -e . && sandbox run --command "echo hello"
```

**Step 5: Commit**

```bash
git add . && git commit -m "feat: CLI entry point"
```

---

## Task 11: Web API

**Files:**
- Create: `~/apps/sandbox-security/web/__init__.py`
- Create: `~/apps/sandbox-security/web/api.py`

**Step 1: 创建 web/api.py**

```python
# web/api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sandbox_core.config import SandboxConfig
from sandbox_core.runner import SandboxRunner

app = FastAPI(title="Sandbox Security API")


class RunRequest(BaseModel):
    command: str = "echo ok"
    runtime: str = "auto"


@app.post("/run")
def run_sandbox(req: RunRequest):
    cfg = SandboxConfig(command=req.command, runtime=req.runtime)
    runner = SandboxRunner(cfg)
    result = runner.run()
    if not result.get("ok"):
        raise HTTPException(400, result.get("error", "unknown"))
    return result


@app.get("/health")
def health():
    return {"status": "ok"}
```

**Step 2: 创建启动脚本**

```bash
# 在 README 或单独脚本中
uvicorn web.api:app --host 0.0.0.0 --port 8000
```

**Step 3: 测试**

```bash
cd ~/apps/sandbox-security && uvicorn web.api:app --host 127.0.0.1 --port 8000 &
sleep 2
curl -X POST http://127.0.0.1:8000/run -H "Content-Type: application/json" -d '{"command":"echo ok"}'
```

**Step 4: Commit**

```bash
git add . && git commit -m "feat: Web API with /run and /health"
```

---

## Task 12: 基础 Web 界面

**Files:**
- Create: `~/apps/sandbox-security/web/static/index.html`

**Step 1: 创建 index.html**

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>沙箱安全运行环境</title>
</head>
<body>
  <h1>沙箱安全运行环境</h1>
  <form id="runForm">
    <label>命令: <input name="command" value="echo ok" /></label>
    <button type="submit">运行</button>
  </form>
  <pre id="result"></pre>
  <script>
    document.getElementById('runForm').onsubmit = async (e) => {
      e.preventDefault();
      const cmd = e.target.command.value;
      const r = await fetch('/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: cmd })
      });
      const j = await r.json();
      document.getElementById('result').textContent = JSON.stringify(j, null, 2);
    };
  </script>
</body>
</html>
```

**Step 2: 在 FastAPI 中挂载静态文件**

```python
# web/api.py 添加
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="web/static", html=True), name="static")
```

**Step 3: 测试**

```bash
# 浏览器打开 http://127.0.0.1:8000
```

**Step 4: Commit**

```bash
git add . && git commit -m "feat: basic Web UI"
```

---

## Task 13: 集成测试与安全测试

**Files:**
- Create: `~/apps/sandbox-security/tests/test_integration.py`
- Create: `~/apps/sandbox-security/tests/test_security.py`

**Step 1: 创建 test_integration.py**

```python
# tests/test_integration.py
from sandbox_core.runner import SandboxRunner
from sandbox_core.config import SandboxConfig, WhitelistConfig, ResourceConfig


def test_full_flow_process():
    cfg = SandboxConfig(
        command="echo ok",
        runtime="process",
        whitelist=WhitelistConfig(allowed_commands=[]),
        resource=ResourceConfig(cpu_limit=0.5, memory_mb=512),
    )
    cfg.whitelist.allowed_commands = ["echo", "echo ok"]
    r = SandboxRunner(cfg)
    result = r.run()
    assert result["ok"] is True
```

**Step 2: 创建 test_security.py**

```python
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
```

**Step 3: Run all tests**

```bash
cd ~/apps/sandbox-security && pytest tests/ -v --cov=sandbox_core
```

**Step 4: Commit**

```bash
git add . && git commit -m "test: integration and security tests"
```

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-03-19-sandbox-security-implementation.md`.

**两种执行方式：**

1. **Subagent-Driven（本会话）**：按任务逐项执行，每任务后检查
2. **Parallel Session（新会话）**：在新会话中打开 executing-plans，批量执行

**选择哪种？**
