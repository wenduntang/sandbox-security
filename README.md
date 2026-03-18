# 沙箱安全运行环境 + 极简自主编排引擎

隔离运行不可信 Web 服务/API，支持 Docker+进程双重隔离、正逆向验证；内置**代码即编排**的轻量化 Agent 引擎。

---

## 功能介绍

### 一、极简自主编排引擎（code_executor）

**核心理念：代码即编排** — 模型输出 Python 代码，引擎安全执行，无 JSON、无 DAG、无复杂框架。

| 功能 | 说明 |
|------|------|
| **安全执行** | RestrictedPython 编译期拦截 import/open；multiprocessing 超时强杀 |
| **工具调用** | 纯函数 + `__doc__` 自动生成描述，通过 `tools['name'](args)` 调用 |
| **输出捕获** | PrintCollector 收集 print 输出 |
| **Fail-fast** | 报错原样回传 LLM，自主 Debug |
| **缩进归一** | textwrap.dedent 处理多缩进 |
| **权限误区** | 区分安全限制与系统权限，明确提示 |

**使用示例：**

```python
from code_executor import safe_run, run_agent

# 单次执行
ok, result = safe_run("""```python
print(tools['get_weather']('北京'))
```""")

# 自主编排循环（需传入 llm_client.chat）
result = run_agent("北京天气怎么样？", llm_client, max_retries=3)
```

**扩展工具：** 在 `TOOLS` 中增加纯函数即可，`__doc__` 自动注入 System Prompt。

---

### 二、沙箱安全运行环境（sandbox_core）

**定位：** 沙箱安全验证框架 / 学习项目

- **适用场景：** 隔离运行 Web 服务、API 测试、教学与实验
- **当前限制：** 资源监控为模拟、进程模式隔离有限，**不建议用于生产环境**

| 功能 | 说明 |
|------|------|
| **双重运行时** | Docker + 进程（自动选择） |
| **正逆向验证** | 环境/配置、白名单/审计、资源配额 |
| **三种使用方式** | CLI、Python 库、Web 界面 |

## 安装

```bash
git clone https://github.com/wenduntang/push-u.git
cd push-u
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .
pip install RestrictedPython  # code_executor 依赖
```

## 测试

```bash
# 极简编排引擎：正向+逆向自测
pytest tests/test_code_executor.py -v

# 沙箱逆向验证
pytest tests/test_reverse_verification.py -v
```

## 使用

**极简编排引擎：**

```python
from code_executor import safe_run

ok, result = safe_run("""```python
print(tools['get_weather']('北京'))
```""")
# ok=True, result='北京天气：晴'
```

**沙箱 CLI / Python / Web：**

```bash
# CLI
sandbox run --command "echo ok"

# Web 服务
uvicorn web.api:app --host 127.0.0.1 --port 8000
```

```python
# Python
from sandbox_core import SandboxRunner
from sandbox_core.config import SandboxConfig
runner = SandboxRunner(SandboxConfig(command="echo ok"))
result = runner.run()
```

## 许可

MIT License
