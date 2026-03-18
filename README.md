# 沙箱安全运行环境

隔离运行不可信 Web 服务/API，支持 Docker+进程双重隔离、正逆向验证。

## 安装

```bash
python -m venv ~/.sandbox-security-venv
source ~/.sandbox-security-venv/bin/activate
pip install -e .
```

## 使用

```bash
# CLI
sandbox run --config config.yaml

# Python
from sandbox_core import SandboxRunner
runner = SandboxRunner()
runner.run(...)
```
