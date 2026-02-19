"""CLI entry point for ai command."""

import os
import subprocess
import sys

import click

from ai_cli.llm import DEFAULT_MODEL, ask_llm
from ai_cli.setup import ensure_ready


@click.command()
@click.pass_context
@click.argument("task", nargs=-1)
def main(ctx: click.Context, task: tuple[str, ...]) -> None:
    """Generate a bash command from a natural language description."""
    if not task:
        click.echo(ctx.get_help())
        return
    task_str = " ".join(task)
    model = os.environ.get("AI_MODEL", DEFAULT_MODEL)

    ensure_ready(model)

    try:
        command = ask_llm(task_str, model=model)
    except Exception as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)

    if not command:
        click.secho("Error: no command generated", fg="red", err=True)
        sys.exit(1)

    click.secho(f"\n  {command}\n", fg="yellow", bold=True)

    if click.confirm("Execute?", default=False):
        result = subprocess.run(command, shell=True)
        sys.exit(result.returncode)
    else:
        click.echo("Aborted.")
