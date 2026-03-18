# web/api.py
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
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


# 挂载静态文件（Web UI）
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
