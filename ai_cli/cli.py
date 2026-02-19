"""CLI entry point for ai command."""

import os
import subprocess
import sys

import click
from ollama import list as ollama_list

from ai_cli import __version__
from ai_cli.config import load_config, save_config
from ai_cli.llm import DEFAULT_MODEL, SYSTEM_PROMPT_TEMPLATE, _detect_env, ask_llm
from ai_cli.setup import ensure_ready


def _pick_model() -> str:
    """List installed ollama models and let user pick one."""
    response = ollama_list()
    if not response.models:
        click.secho("No models installed.", fg="red", err=True)
        sys.exit(1)

    click.secho("Installed models:", fg="cyan", err=True)
    for i, m in enumerate(response.models, 1):
        size_gb = m.size / (1024**3) if m.size else 0
        click.secho(f"  {i}. {m.model} ({size_gb:.1f} GB)", err=True)

    choice = click.prompt("Choose model", type=int, err=True)
    if choice < 1 or choice > len(response.models):
        click.secho("Invalid choice.", fg="red", err=True)
        sys.exit(1)

    return response.models[choice - 1].model


@click.command(options_metavar="[OPTIONS] [--]")
@click.version_option(__version__, "--version")
@click.pass_context
@click.argument("task", nargs=-1)
@click.option(
    "-m",
    "model_opt",
    default=None,
    help="Use a specific model for this run.",
)
@click.option(
    "-M",
    "model_save",
    default=None,
    help="Use a specific model and save it as the default.",
)
@click.option(
    "-i",
    "--interactive",
    "interactive",
    is_flag=True,
    default=False,
    help="Interactively pick a model and save it as default.",
)
@click.option("-v", "--verbose", is_flag=True, default=False, help="Show command explanation.")
def main(
    ctx: click.Context,
    task: tuple[str, ...],
    model_opt: str | None,
    model_save: str | None,
    interactive: bool,
    verbose: bool,
) -> None:
    """Generate a bash command from a natural language description."""
    if not task:
        click.echo(ctx.get_help())
        return
    task_str = " ".join(task)

    # Resolve model: -m/-M flag > -i interactive > AI_MODEL env > config > default
    save_after_ready = False
    if model_save is not None:
        model = model_save
        save_after_ready = True
    elif model_opt is not None:
        model = model_opt
    elif interactive:
        model = _pick_model()
        save_after_ready = True
    else:
        config = load_config()
        model = os.environ.get("AI_MODEL", config.get("model", DEFAULT_MODEL))

    if verbose:
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(**_detect_env())
        click.secho(f"Model: {model}", fg="cyan", err=True)
        click.secho(f"System: {system_prompt}", fg="cyan", err=True)

    ensure_ready(model)

    if save_after_ready:
        save_config({"model": model})

    try:
        result = ask_llm(task_str, model=model, verbose=verbose)
        if result is None:
            click.secho("Error: no command generated", fg="red", err=True)
            sys.exit(1)
        command = result.command
        if verbose and result.explanation:
            click.secho(f"\n  {result.explanation}\n", fg="cyan", err=True)
    except Exception as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)

    click.secho(f"\n  {command}\n", fg="yellow", bold=True)

    if click.confirm("Execute?", default=True):
        result = subprocess.run(command, shell=True)
        sys.exit(result.returncode)
    else:
        click.echo("Aborted.")
