"""CLI entry point for ai command."""

import click


@click.command()
@click.argument("task", nargs=-1, required=True)
def main(task: tuple[str, ...]) -> None:
    """Generate a bash command from a natural language description."""
    click.echo("Not implemented yet")
