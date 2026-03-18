# cli/main.py
import click
import yaml
from pathlib import Path
from sandbox_core.config import SandboxConfig
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
