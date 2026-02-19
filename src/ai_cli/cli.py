"""CLI entry point for ai command."""

import subprocess
import sys

import click

from ai_cli.llm import ask_llm


@click.command()
@click.argument("task", nargs=-1, required=True)
def main(task: tuple[str, ...]) -> None:
    """Generate a bash command from a natural language description."""
    task_str = " ".join(task)

    try:
        command = ask_llm(task_str)
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
