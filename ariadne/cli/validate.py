"""
validate.py

CLI: sniff and parse a TLE/CSV/TXT catalog file, reporting how many
records parsed and any per-row warnings, without doing anything else
with the result. Useful before feeding a file to `propagate`/`screen`.
"""

from pathlib import Path

import click

from ariadne.exceptions import AriadneError
from ariadne.ingest.sniff import load_file, sniff_format


@click.command("validate")
@click.argument("path", type=click.Path(exists=True, dir_okay=False))
def validate(path: str) -> None:
    """Validate and summarize a TLE/CSV/TXT catalog file."""
    try:
        fmt = sniff_format(Path(path).read_text())
        records, warnings = load_file(path)
    except AriadneError as exc:
        raise click.ClickException(str(exc))

    click.echo(
        f"{path}: detected {fmt.value}, {len(records)} record(s), {len(warnings)} warning(s)"
    )
    for warning in warnings:
        click.echo(f"  warning: {warning}", err=True)
