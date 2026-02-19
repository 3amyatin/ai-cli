"""Ollama readiness checks: server reachable, model available."""

import sys
from shutil import which as shutil_which

import click
from ollama import list as ollama_list
from ollama import pull as ollama_pull


def ensure_ready(model: str) -> None:
    """Ensure ollama server is reachable and the target model is available.

    Steps:
    1. Check ollama server connectivity via ollama.list()
    2. On ConnectionError: check if ollama binary exists on PATH
       - Missing binary → print install instructions, exit(1)
       - Binary present but server down → suggest `ollama serve`, exit(1)
    3. Check if target model is in the installed models list
    4. If model missing → auto-pull with progress output
    """
    # Step 1-2: Check server connectivity
    try:
        response = ollama_list()
    except ConnectionError:
        if shutil_which("ollama") is None:
            click.secho(
                "ollama is not installed. Install it: https://ollama.com/download",
                fg="red",
                err=True,
            )
        else:
            click.secho(
                "ollama is not running. Start it with: ollama serve",
                fg="red",
                err=True,
            )
        sys.exit(1)

    # Step 3: Check if model is already available
    installed = {m.model for m in response.models}
    if model in installed:
        return

    # Step 4: Pull the missing model
    click.secho(f"Pulling model {model}...", fg="yellow", err=True)
    try:
        for progress in ollama_pull(model, stream=True):
            if progress.completed is not None and progress.total:
                pct = int(progress.completed / progress.total * 100)
                click.secho(
                    f"\r  {progress.status}: {pct}%", fg="yellow", err=True, nl=False
                )
            else:
                click.secho(f"\r  {progress.status}", fg="yellow", err=True, nl=False)
        click.secho("", err=True)  # newline after progress
    except Exception as e:
        click.secho(f"\nFailed to pull model {model}: {e}", fg="red", err=True)
        sys.exit(1)
