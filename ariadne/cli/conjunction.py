"""
conjunction.py

CLI: find the time of closest approach between two TLE-defined objects,
both propagated to a common reference epoch via SGP4 before the search.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import click

from ariadne.cli._util import parse_iso_epoch, select_tle
from ariadne.conjunction.tca import find_tca
from ariadne.exceptions import AriadneError
from ariadne.export.json import tca_to_dict
from ariadne.ingest.tle import load_tle_file
from ariadne.propagate.sgp4 import propagate as sgp4_propagate


def _reference_state(path: str, norad_id: Optional[int], epoch0: datetime):
    tle = select_tle(load_tle_file(path), norad_id, path)
    return sgp4_propagate(tle, epoch0).as_vector()


@click.command("conjunction")
@click.argument("primary_tle", type=click.Path(exists=True, dir_okay=False))
@click.argument("secondary_tle", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--epoch", required=True,
    help="Reference epoch both objects are propagated to before searching, ISO-8601 UTC.",
)
@click.option("--primary-norad-id", type=int)
@click.option("--secondary-norad-id", type=int)
@click.option(
    "--window-s", type=(float, float), default=(-1800.0, 1800.0), show_default=True,
    help="TCA search window, seconds from --epoch.",
)
@click.option("--no-j2", is_flag=True, help="Disable the J2 perturbation term in the TCA search.")
@click.option(
    "--format", "fmt", type=click.Choice(["table", "json"]), default="table", show_default=True,
)
@click.option("--out", "out_path", type=click.Path(dir_okay=False))
def conjunction(
    primary_tle: str, secondary_tle: str, epoch: str,
    primary_norad_id: Optional[int], secondary_norad_id: Optional[int],
    window_s, no_j2: bool, fmt: str, out_path: Optional[str],
) -> None:
    """Find the time of closest approach between two TLE-defined objects."""
    try:
        epoch0 = parse_iso_epoch(epoch)
        primary_state = _reference_state(primary_tle, primary_norad_id, epoch0)
        secondary_state = _reference_state(secondary_tle, secondary_norad_id, epoch0)
        result = find_tca(epoch0, primary_state, secondary_state, window_s, include_j2=not no_j2)
    except AriadneError as exc:
        raise click.ClickException(str(exc))

    if fmt == "json":
        text = json.dumps(tca_to_dict(result), indent=2)
        if out_path:
            Path(out_path).write_text(text)
            click.echo(f"wrote {out_path}")
        else:
            click.echo(text)
    else:
        click.echo(f"TCA: {result.epoch.isoformat()}  (dt={result.dt:+.1f}s from reference epoch)")
        click.echo(f"miss distance: {result.miss_distance:.3f} km")
