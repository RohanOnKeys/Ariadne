"""
main.py

`ariadne` CLI entry point (see `pyproject.toml`'s `[project.scripts]`):
a thin click group wiring together each subcommand module. Every
subcommand catches `AriadneError` itself and re-raises as
`click.ClickException`, so nothing needs to happen here beyond
assembling the group.
"""

import click

from ariadne.cli.conjunction import conjunction
from ariadne.cli.estimate import estimate
from ariadne.cli.fetch import fetch
from ariadne.cli.propagate import propagate
from ariadne.cli.screen import screen
from ariadne.cli.validate import validate


@click.group()
@click.version_option(package_name="ariadne")
def main() -> None:
    """Ariadne: CLI-first astrodynamics framework."""


main.add_command(fetch)
main.add_command(validate)
main.add_command(propagate)
main.add_command(estimate)
main.add_command(conjunction)
main.add_command(screen)


if __name__ == "__main__":
    main()
