# 沙箱安全运行环境

隔离运行不可信 Web 服务/API，支持 Docker+进程双重隔离、正逆向验证。

## 定位

**沙箱安全验证框架 / 学习项目**

- **适用场景：** 隔离运行 Web 服务、API 测试、教学与实验
- **当前限制：** 资源监控为模拟、进程模式隔离有限，**不建议用于生产环境**

这样既能展示设计思路，又不会误导使用者对安全级别的预期。

## 特性

- Docker + 进程双重运行时（自动选择）
- 三类正逆向验证：环境/配置、白名单/审计、资源配额
- CLI、Python 库、Web 界面三种使用方式

## 安装

```bash
git clone https://github.com/wenduntang/sandbox-security.git
cd sandbox-security
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
```

## 逆向思维测试

```bash
pytest tests/test_reverse_verification.py -v
```

## 使用

```bash
# CLI
sandbox run --command "echo ok"

# Python
from sandbox_core import SandboxRunner
from sandbox_core.config import SandboxConfig
runner = SandboxRunner(SandboxConfig(command="echo ok"))
result = runner.run()

# Web 服务
uvicorn web.api:app --host 127.0.0.1 --port 8000
```

## 许可

MIT License
